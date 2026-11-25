"""多驱动主动巡检采集引擎（local / ssh / mock），5 并发隔离失败，超时绝不自动重试。"""

from __future__ import annotations

import ctypes
import hashlib
import logging
import os
import platform
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .config import Settings
from .storage import now_str

logger = logging.getLogger("ops_inspect.collector")

# 远程输出单次读取安全上限，避免异常标准输出撑爆进程内存
MAX_SSH_OUTPUT_BYTES = 65536
MAX_SSH_STDERR_BYTES = 4096

# 远程 Linux 只读白名单命令常量：严禁拼接用户输入，一次 SSH 往返采集全部指标
SSH_READONLY_CMD = (
    "awk '/^(MemTotal|MemAvailable|MemFree|Buffers|Cached):/{print $1,$2}' /proc/meminfo; "
    "echo '---CORES---'; "
    "(nproc 2>/dev/null || grep -c '^processor' /proc/cpuinfo); "
    "echo '---STAT1---'; head -n 1 /proc/stat; "
    "sleep 0.5; "
    "echo '---STAT2---'; head -n 1 /proc/stat"
)


@dataclass
class ProbeResult:
    target_id: int
    host: str
    mem_total: float | None
    mem_free: float | None
    cores: int | None
    cpu: float | None
    probe_status: str  # OK | WARN | HIGH_LOAD | TIMEOUT | UNREACHABLE
    last_checked_at: str
    probe_error: str = ""

    @property
    def ok(self) -> bool:
        return self.probe_status in ("OK", "WARN", "HIGH_LOAD")


def evaluate_probe_status(mem_total: float, mem_free: float, cpu: float) -> str:
    ratio = (mem_free / mem_total) if mem_total > 0 else 1.0
    if cpu >= 80.0 or ratio < 0.15:
        return "HIGH_LOAD"
    if cpu >= 60.0 or ratio < 0.25:
        return "WARN"
    return "OK"


def parse_proc_meminfo(text: str) -> tuple[float, float]:
    """解析 /proc/meminfo（单位 kB），优先 MemAvailable，老内核回退 MemFree+Buffers+Cached。"""
    vals: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"^\s*(MemTotal|MemAvailable|MemFree|Buffers|Cached):\s+(\d+)", line)
        if m:
            vals[m.group(1)] = int(m.group(2))
    total_kb = vals.get("MemTotal", 0)
    if total_kb <= 0:
        raise ValueError("未能从 /proc/meminfo 解析出有效 MemTotal")
    avail_kb = vals.get("MemAvailable")
    if avail_kb is None:
        avail_kb = vals.get("MemFree", 0) + vals.get("Buffers", 0) + vals.get("Cached", 0)
    mem_total_gb = round(total_kb / (1024 * 1024), 1)
    mem_free_gb = round(min(avail_kb, total_kb) / (1024 * 1024), 1)
    return mem_total_gb, mem_free_gb


def _parse_proc_stat_line(line: str) -> tuple[int, int]:
    parts = line.strip().split()
    if len(parts) < 5 or not parts[0].startswith("cpu"):
        raise ValueError("无效的 /proc/stat 首行输出")
    nums = [int(x) for x in parts[1:] if x.isdigit()]
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
    total = sum(nums)
    return total, idle


def calc_cpu_percent_from_stat(stat1: str, stat2: str) -> float:
    t1, i1 = _parse_proc_stat_line(stat1)
    t2, i2 = _parse_proc_stat_line(stat2)
    total_delta = t2 - t1
    idle_delta = i2 - i1
    if total_delta <= 0:
        return 0.0
    usage = ((total_delta - idle_delta) / total_delta) * 100.0
    return round(min(100.0, max(0.0, usage)), 1)


def parse_ssh_combined_output(raw_output: str) -> tuple[float, float, int, float]:
    """解析 SSH_READONLY_CMD 组合输出，返回 (mem_total, mem_free, cores, cpu)。"""
    parts_cores = raw_output.split("---CORES---")
    if len(parts_cores) != 2:
        raise ValueError("SSH 采集输出缺少 CORES 分隔段")
    mem_part = parts_cores[0]
    parts_stat1 = parts_cores[1].split("---STAT1---")
    if len(parts_stat1) != 2:
        raise ValueError("SSH 采集输出缺少 STAT1 分隔段")
    cores_str = parts_stat1[0].strip().splitlines()[0].strip()
    parts_stat2 = parts_stat1[1].split("---STAT2---")
    if len(parts_stat2) != 2:
        raise ValueError("SSH 采集输出缺少 STAT2 分隔段")

    mem_total, mem_free = parse_proc_meminfo(mem_part)
    cores = max(1, int(cores_str))
    stat1 = parts_stat2[0].strip().splitlines()[0]
    stat2 = parts_stat2[1].strip().splitlines()[0]
    cpu = calc_cpu_percent_from_stat(stat1, stat2)
    return mem_total, mem_free, cores, cpu


# ==================== Windows 本机真实采集（纯标准库 ctypes） ====================


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class _FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", ctypes.c_ulong),
        ("dwHighDateTime", ctypes.c_ulong),
    ]


def _filetime_to_int(ft: _FILETIME) -> int:
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


def _collect_local_windows(sample_interval: float = 0.5) -> tuple[float, float, int, float]:
    kernel32 = ctypes.windll.kernel32
    mem = _MEMORYSTATUSEX()
    mem.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
        raise OSError("GlobalMemoryStatusEx 调用失败")

    mem_total_gb = round(mem.ullTotalPhys / (1024**3), 1)
    mem_free_gb = round(mem.ullAvailPhys / (1024**3), 1)

    def read_times() -> tuple[int, int, int]:
        idle, kernel, user = _FILETIME(), _FILETIME(), _FILETIME()
        if not kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            raise OSError("GetSystemTimes 调用失败")
        return _filetime_to_int(idle), _filetime_to_int(kernel), _filetime_to_int(user)

    i1, k1, u1 = read_times()
    time.sleep(sample_interval)
    i2, k2, u2 = read_times()

    # Win32 规范：kernelTime 已包含 idleTime
    sys_delta = (k2 - k1) + (u2 - u1)
    idle_delta = i2 - i1
    cpu = round(min(100.0, max(0.0, ((sys_delta - idle_delta) / sys_delta) * 100.0)), 1) if sys_delta > 0 else 0.0
    cores = os.cpu_count() or 1
    return mem_total_gb, mem_free_gb, cores, cpu


def _collect_local_linux(sample_interval: float = 0.5) -> tuple[float, float, int, float]:
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace")
    mem_total, mem_free = parse_proc_meminfo(meminfo)
    stat1 = Path("/proc/stat").read_text(encoding="utf-8", errors="replace").splitlines()[0]
    time.sleep(sample_interval)
    stat2 = Path("/proc/stat").read_text(encoding="utf-8", errors="replace").splitlines()[0]
    cpu = calc_cpu_percent_from_stat(stat1, stat2)
    cores = os.cpu_count() or 1
    return mem_total, mem_free, cores, cpu


def collect_local(target: dict[str, Any], sample_interval: float = 0.5) -> ProbeResult:
    """本机真实系统指标采集（Windows ctypes / Linux /proc，零额外第三方依赖）。"""
    ts = now_str()
    try:
        if platform.system().lower() == "windows":
            mem_total, mem_free, cores, cpu = _collect_local_windows(sample_interval=sample_interval)
        else:
            mem_total, mem_free, cores, cpu = _collect_local_linux(sample_interval=sample_interval)
        status = evaluate_probe_status(mem_total, mem_free, cpu)
        return ProbeResult(
            target_id=target["id"],
            host=target["host"],
            mem_total=mem_total,
            mem_free=mem_free,
            cores=cores,
            cpu=cpu,
            probe_status=status,
            last_checked_at=ts,
            probe_error="",
        )
    except Exception as exc:
        return ProbeResult(
            target_id=target["id"],
            host=target["host"],
            mem_total=None,
            mem_free=None,
            cores=None,
            cpu=None,
            probe_status="UNREACHABLE",
            last_checked_at=ts,
            probe_error=f"本机采集失败：{exc.__class__.__name__}",
        )


def resolve_ssh_key_path(ref: str, settings: Settings) -> Path | None:
    """按凭据别名安全解析只读私钥文件路径，禁止路径穿越。"""
    clean_ref = (ref or "").strip()
    if not clean_ref:
        return None
    if clean_ref in settings.ssh_key_map:
        mapped = Path(settings.ssh_key_map[clean_ref]).resolve()
        return mapped if mapped.is_file() else None
    if ".." in clean_ref or "/" in clean_ref or "\\" in clean_ref:
        return None
    candidate = (settings.ssh_keys_dir / clean_ref).resolve()
    base = settings.ssh_keys_dir.resolve()
    if base not in candidate.parents:
        return None
    return candidate if candidate.is_file() else None


def collect_ssh(
    target: dict[str, Any],
    settings: Settings,
    *,
    connect_timeout: float = 5.0,
    exec_timeout: float = 8.0,
    ssh_client_factory: Callable[[], Any] | None = None,
) -> ProbeResult:
    """远程 Linux 只读 SSH 采集（基于 paramiko，单次执行绝不自动重试）。"""
    ts = now_str()
    cred_ref = str(target.get("ssh_credential_ref") or "").strip()
    key_path = resolve_ssh_key_path(cred_ref, settings) if ssh_client_factory is None else Path(cred_ref or "mock-key")
    if ssh_client_factory is None and key_path is None:
        return ProbeResult(
            target_id=target["id"],
            host=target["host"],
            mem_total=None,
            mem_free=None,
            cores=None,
            cpu=None,
            probe_status="UNREACHABLE",
            last_checked_at=ts,
            probe_error=f"未找到 SSH 凭据别名 [{cred_ref or '未配置'}] 对应的只读私钥文件",
        )

    import paramiko  # 延迟导入便于轻量化

    client = ssh_client_factory() if ssh_client_factory else paramiko.SSHClient()
    try:
        if ssh_client_factory is None:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            known_hosts = settings.ssh_keys_dir / "known_hosts"
            if known_hosts.is_file():
                client.load_host_keys(str(known_hosts))
            elif settings.ssh_strict_host_key:
                logger.warning(
                    "SSH 严格主机指纹校验已阻断连接：target=%s address=%s 缺少 known_hosts 文件",
                    target.get("host"),
                    target.get("address"),
                )
                return ProbeResult(
                    target_id=target["id"],
                    host=target["host"],
                    mem_total=None,
                    mem_free=None,
                    cores=None,
                    cpu=None,
                    probe_status="UNREACHABLE",
                    last_checked_at=ts,
                    probe_error="缺少 SSH known_hosts 主机指纹白名单文件（严格模式下已拒连）",
                )
            else:
                logger.warning(
                    "SSH_STRICT_HOST_KEY=false 且缺少 known_hosts，已临时使用 AutoAddPolicy：target=%s address=%s",
                    target.get("host"),
                    target.get("address"),
                )
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            hostname=target["address"],
            port=int(target.get("ssh_port") or 22),
            username=target.get("ssh_user") or "ops-ro",
            key_filename=str(key_path) if key_path else None,
            timeout=connect_timeout,
            banner_timeout=connect_timeout,
            auth_timeout=connect_timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        _, stdout, stderr = client.exec_command(SSH_READONLY_CMD, timeout=exec_timeout)
        if hasattr(stdout, "channel") and stdout.channel is not None:
            stdout.channel.settimeout(exec_timeout)
        raw_out_bytes = stdout.read(MAX_SSH_OUTPUT_BYTES + 1)
        if len(raw_out_bytes) > MAX_SSH_OUTPUT_BYTES:
            raise ValueError(f"SSH 采集输出超过 {MAX_SSH_OUTPUT_BYTES} 字节安全上限")
        raw_out = raw_out_bytes.decode("utf-8", errors="replace")
        raw_err = stderr.read(MAX_SSH_STDERR_BYTES).decode("utf-8", errors="replace").strip() if stderr else ""
        if not raw_out.strip():
            raise RuntimeError(raw_err or "远程只读采集未返回指标输出")

        mem_total, mem_free, cores, cpu = parse_ssh_combined_output(raw_out)
        status = evaluate_probe_status(mem_total, mem_free, cpu)
        return ProbeResult(
            target_id=target["id"],
            host=target["host"],
            mem_total=mem_total,
            mem_free=mem_free,
            cores=cores,
            cpu=cpu,
            probe_status=status,
            last_checked_at=ts,
            probe_error="",
        )
    except (TimeoutError, socket.timeout):
        return ProbeResult(
            target_id=target["id"],
            host=target["host"],
            mem_total=None,
            mem_free=None,
            cores=None,
            cpu=None,
            probe_status="TIMEOUT",
            last_checked_at=ts,
            probe_error=f"SSH 采集超过 {int(exec_timeout)}s 超时（单台已隔离，未自动重试）",
        )
    except Exception as exc:
        return ProbeResult(
            target_id=target["id"],
            host=target["host"],
            mem_total=None,
            mem_free=None,
            cores=None,
            cpu=None,
            probe_status="UNREACHABLE",
            last_checked_at=ts,
            probe_error=f"SSH 连接或采集失败：{exc.__class__.__name__}",
        )
    finally:
        try:
            client.close()
        except Exception:
            pass


def collect_mock(target: dict[str, Any]) -> ProbeResult:
    """确定性模拟探针：离线演示与自动化测试用。"""
    ts = now_str()
    host = str(target.get("host") or "")
    addr = str(target.get("address") or "")
    low_host = host.lower()

    if addr.endswith(".52") or "timeout" in low_host:
        return ProbeResult(
            target_id=target["id"],
            host=host,
            mem_total=None,
            mem_free=None,
            cores=None,
            cpu=None,
            probe_status="TIMEOUT",
            last_checked_at=ts,
            probe_error="SSH 采集超过 8s 超时（单台已隔离，未自动重试）",
        )
    if "unreachable" in low_host:
        return ProbeResult(
            target_id=target["id"],
            host=host,
            mem_total=None,
            mem_free=None,
            cores=None,
            cpu=None,
            probe_status="UNREACHABLE",
            last_checked_at=ts,
            probe_error="目标主机不可达（连接被拒绝）",
        )

    # 基于主机名生成稳定且有区分度的演示指标
    digest = int(hashlib.sha256(host.encode("utf-8")).hexdigest()[:6], 16)
    if "k8s-node-01" in low_host or "high" in low_host:
        mem_total, mem_free, cores, cpu = 256.0, 34.5, 64, 86.2
    elif "db-master" in low_host or "warn" in low_host:
        mem_total, mem_free, cores, cpu = 512.0, 148.0, 128, 65.4
    else:
        mem_total = float([64, 128, 256][digest % 3])
        cores = [16, 32, 64][digest % 3]
        cpu = round(18.0 + (digest % 35), 1)
        mem_free = round(mem_total * (0.42 + (digest % 25) / 100.0), 1)

    status = evaluate_probe_status(mem_total, mem_free, cpu)
    return ProbeResult(
        target_id=target["id"],
        host=host,
        mem_total=mem_total,
        mem_free=mem_free,
        cores=cores,
        cpu=cpu,
        probe_status=status,
        last_checked_at=ts,
        probe_error="",
    )


def probe_target(
    target: dict[str, Any],
    settings: Settings,
    *,
    ssh_client_factory: Callable[[], Any] | None = None,
    sample_interval: float = 0.5,
) -> ProbeResult:
    col = str(target.get("collector_type") or "mock").lower()
    if col == "local":
        return collect_local(target, sample_interval=sample_interval)
    if col == "ssh":
        return collect_ssh(target, settings, ssh_client_factory=ssh_client_factory)
    return collect_mock(target)


def inspect_all_targets(
    targets: list[dict[str, Any]],
    settings: Settings,
    *,
    max_workers: int = 5,
    ssh_client_factory: Callable[[], Any] | None = None,
    sample_interval: float = 0.5,
) -> list[ProbeResult]:
    """5 并发全量巡检，单台异常严格隔离，绝不拖垮整批巡检。"""
    if not targets:
        return []

    def _safe_probe(t: dict[str, Any]) -> ProbeResult:
        try:
            return probe_target(
                t,
                settings,
                ssh_client_factory=ssh_client_factory,
                sample_interval=sample_interval,
            )
        except Exception as exc:
            return ProbeResult(
                target_id=t["id"],
                host=t["host"],
                mem_total=None,
                mem_free=None,
                cores=None,
                cpu=None,
                probe_status="UNREACHABLE",
                last_checked_at=now_str(),
                probe_error=f"采集异常隔离：{exc.__class__.__name__}",
            )

    workers = max(1, min(max_workers, len(targets)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_safe_probe, targets))
