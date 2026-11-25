#!/usr/bin/env python3
"""Ops Vibe Coding v3.3 确定性门禁引擎（仅使用 Python 标准库）。

支持 4 条命令：
  init     初始化目标项目（生成 AGENTS.md、.vibe/state.json、docs/vibe/）
  check    执行 P1–P5 全 6 阶段硬校验（p1/p2/p3/p4a/p4b/p5，亲自跑命令拿真实退出码 + 静态红线扫描）
  approve  人工拍板放行（覆盖全部 6 阶段 p1/p2/p3/p4a/p4b/p5，且必须先通过对应阶段 check）
  status   查看当前阶段、命令配置、失败重试计数与人工批准状态
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

# Windows 终端统一 UTF-8 输出，避免中文打印异常
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCHEMA_VERSION = "3.3"
MAX_RETRIES = 3
STAGES = ("p1", "p2", "p3", "p4a", "p4b", "p5")
HUMAN_GATES = ("p1", "p2", "p3", "p4a", "p4b", "p5")
NEXT_STAGE = {
    "p1": "p2",
    "p2": "p3",
    "p3": "p4a",
    "p4a": "p4b",
    "p4b": "p5",
    "p5": "released",
}

GUARD_START = "<!-- VIBE-GUARD-START -->"
GUARD_END = "<!-- VIBE-GUARD-END -->"

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vibe",
    ".agents",
    ".agent",
}

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
AGENTS_TEMPLATE_PATH = REPO_ROOT / "templates" / "AGENTS.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_state(project: Path) -> dict[str, Any]:
    state_path = project / ".vibe" / "state.json"
    if not state_path.exists():
        raise SystemExit(f"[ERROR] 未找到 {state_path}，请先执行 init 初始化项目。")
    return json.loads(read_text(state_path))


def save_state(project: Path, state: dict[str, Any]) -> None:
    write_json(project / ".vibe" / "state.json", state)


def extract_guard_hash(agents_md: Path) -> str | None:
    """提取 AGENTS.md 中受保护的安全红线区块并计算 SHA-256。"""
    if not agents_md.exists():
        return None
    text = read_text(agents_md).replace("\r\n", "\n")
    start = text.find(GUARD_START)
    end = text.find(GUARD_END)
    if start == -1 or end == -1 or end <= start:
        return None
    block = text[start : end + len(GUARD_END)].strip()
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def format_gate_script_ref(project: Path) -> str:
    try:
        return Path(os.path.relpath(SCRIPT_PATH, project.resolve())).as_posix()
    except ValueError:
        return SCRIPT_PATH.as_posix()


def run_cmd(cmd: str, cwd: Path, timeout: int = 300) -> dict[str, Any]:
    """真实执行外部命令并返回退出码与尾部输出。"""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "command": cmd,
            "cwd": cwd.as_posix(),
            "returncode": proc.returncode,
            "passed": proc.returncode == 0,
            "stdout_tail": (proc.stdout or "")[-1500:],
            "stderr_tail": (proc.stderr or "")[-1500:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "cwd": cwd.as_posix(),
            "returncode": -1,
            "passed": False,
            "stdout_tail": (exc.stdout or "")[-1500:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": f"Command timed out after {timeout}s",
        }


class _HtmlValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.text_len = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag.lower())

    def handle_data(self, data: str) -> None:
        self.text_len += len(data.strip())


def has_unresolved_issue(markdown_text: str, keywords: tuple[str, ...] = ("BLOCKER", "FAIL")) -> list[str]:
    """按行检查审查报告中是否存在未关闭的 BLOCKER / FAIL。"""
    resolved_hints = (
        "0 blocker",
        "0 fail",
        "no blocker",
        "no fail",
        "无 blocker",
        "无 fail",
        "无阻断",
        "closed",
        "resolved",
        "fixed",
        "已关闭",
        "已修复",
        "已解决",
        "passed",
    )
    hits: list[str] = []
    for lineno, raw in enumerate(markdown_text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if any(h in low for h in resolved_hints):
            continue
        for kw in keywords:
            if re.search(rf"(?<![A-Za-z]){re.escape(kw)}(?![A-Za-z])", line, re.IGNORECASE):
                hits.append(f"L{lineno}: {line[:120]}")
                break
    return hits


def iter_project_files(project: Path, include_docs_vibe: bool = False) -> list[Path]:
    """遍历项目文件，自动跳过构建产物、依赖与内部目录。"""
    results: list[Path] = []
    docs_vibe = (project / "docs" / "vibe").resolve()
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root).resolve()
        if not include_docs_vibe and (root_path == docs_vibe or docs_vibe in root_path.parents):
            continue
        for fname in files:
            results.append(root_path / fname)
    return results


def is_test_file(path: Path, project: Path) -> bool:
    rel = path.relative_to(project.resolve()).as_posix().lower()
    parts = rel.split("/")
    name = path.name.lower()
    return (
        any(p in ("test", "tests", "__tests__", "e2e") for p in parts)
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
        or name.endswith("_test.py")
    )


def builtin_hard_scan(project: Path) -> list[str]:
    """P4 内置硬扫描：密钥、:latest、root 容器、reload=True、CORS *、Mock 未关、K8s 探针/限额。"""
    issues: list[str] = []
    project_res = project.resolve()
    files = iter_project_files(project_res, include_docs_vibe=False)

    secret_always = [
        (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "疑似明文私钥"),
        (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "疑似 GitHub Token"),
        (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "疑似 API Secret Key"),
        (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "疑似 AWS Access Key"),
    ]
    secret_non_test = re.compile(
        r"""(?i)\b(password|passwd|api_secret|secret_key|jwt_secret)\b\s*[:=]\s*["']([^"'\s${}]{6,})["']"""
    )

    for fpath in files:
        if fpath.resolve() == SCRIPT_PATH:
            continue
        rel = fpath.relative_to(project_res).as_posix()
        name = fpath.name
        low_name = name.lower()
        suffix = fpath.suffix.lower()

        # 仅扫描文本类源码与配置，跳过超大文件或二进制
        if fpath.stat().st_size > 1_000_000:
            continue
        if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".woff", ".woff2", ".lock"):
            continue

        text = read_text(fpath)
        test_flag = is_test_file(fpath, project_res)

        # 1. 明文密钥扫描
        for pat, desc in secret_always:
            if pat.search(text):
                issues.append(f"[SECRET] {rel}: {desc}")
        if not test_flag and suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".yml", ".yaml", ".env", ".json", ".toml"):
            for m in secret_non_test.finditer(text):
                val = m.group(2).lower()
                if any(placeholder in val for placeholder in ("changeme", "example", "placeholder", "your_", "dummy")):
                    continue
                issues.append(f"[SECRET] {rel}: 疑似硬编码敏感凭据 `{m.group(1)}`")
                break

        # 2. Dockerfile 检查（:latest、USER root / 缺少 USER、VITE_USE_MOCK=true）
        if low_name == "dockerfile" or low_name.startswith("dockerfile.") or low_name.endswith(".dockerfile"):
            users: list[str] = []
            for lineno, raw in enumerate(text.splitlines(), start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if re.match(r"(?i)^FROM\s+\S+:latest(\s|$)", line):
                    issues.append(f"[IMAGE] {rel}:{lineno}: 禁止使用 :latest 镜像标签")
                m_user = re.match(r"(?i)^USER\s+(\S+)", line)
                if m_user:
                    users.append(m_user.group(1).strip())
                if re.search(r"VITE_USE_MOCK\s*[:=]\s*[\"']?true[\"']?", line, re.IGNORECASE):
                    issues.append(f"[MOCK] {rel}:{lineno}: 镜像构建启用了 VITE_USE_MOCK=true")
            if not users:
                issues.append(f"[ROOT] {rel}: 未声明非 root 的 USER 指令")
            elif users[-1].lower() in ("root", "0", "0:0"):
                issues.append(f"[ROOT] {rel}: 最终运行用户为 root ({users[-1]})")

        # 3. docker-compose 与 K8s YAML 检查
        if suffix in (".yml", ".yaml"):
            for lineno, raw in enumerate(text.splitlines(), start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if re.match(r"^image\s*:\s*['\"]?\S+:latest['\"]?(\s|$)", line):
                    issues.append(f"[IMAGE] {rel}:{lineno}: 禁止使用 :latest 镜像标签")
                if re.search(r"VITE_USE_MOCK\s*[:=]\s*[\"']?true[\"']?", line, re.IGNORECASE):
                    issues.append(f"[MOCK] {rel}:{lineno}: 编排配置启用了 VITE_USE_MOCK=true")

            if re.search(r"(?m)^kind\s*:\s*(Deployment|StatefulSet)\s*$", text):
                for idx, doc in enumerate(re.split(r"(?m)^---\s*$", text), start=1):
                    if not re.search(r"(?m)^kind\s*:\s*(Deployment|StatefulSet)\s*$", doc):
                        continue
                    if "livenessProbe:" not in doc:
                        issues.append(f"[K8S] {rel} (doc #{idx}): 缺少 livenessProbe")
                    if "readinessProbe:" not in doc:
                        issues.append(f"[K8S] {rel} (doc #{idx}): 缺少 readinessProbe")
                    if "resources:" not in doc or "limits:" not in doc:
                        issues.append(f"[K8S] {rel} (doc #{idx}): 缺少 resources.limits")

        # 4. .env 文件检查 VITE_USE_MOCK=true
        if low_name == ".env" or low_name.startswith(".env."):
            for lineno, raw in enumerate(text.splitlines(), start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if re.search(r"VITE_USE_MOCK\s*=\s*[\"']?true[\"']?", line, re.IGNORECASE):
                    issues.append(f"[MOCK] {rel}:{lineno}: 环境配置开启了 VITE_USE_MOCK=true")

        # 5. Python 后端源码检查 reload=True 与 CORS *
        if suffix == ".py" and not test_flag:
            if re.search(r"\breload\s*=\s*True\b", text):
                issues.append(f"[RELOAD] {rel}: 禁止保留 reload=True")
            if re.search(r"""allow_origins\s*=\s*\[\s*["']\*["']\s*\]""", text) or re.search(
                r"""Access-Control-Allow-Origin["']?\s*[:=]\s*["']\*["']""", text
            ):
                issues.append(f"[CORS] {rel}: 禁止通配 CORS (*)")

        # 6. 前端源码检查默认开启 Mock
        if rel.startswith("frontend/") and suffix in (".ts", ".tsx", ".js", ".jsx") and not test_flag:
            if re.search(r"""VITE_USE_MOCK\s*!==\s*["']false["']""", text) or re.search(
                r"""const\s+USE_MOCK\s*=\s*true\b""", text
            ):
                issues.append(f"[MOCK] {rel}: 前端源码默认开启了 Mock 模式")

    return issues


def scan_frontend_ui_baseline(project: Path) -> list[str]:
    """P4a 前端生产 UI 硬检查：禁止业务组件裸用系统原生 <select> 标签。"""
    issues: list[str] = []
    fe_src = (project / "frontend" / "src").resolve()
    if not fe_src.is_dir():
        return issues

    project_res = project.resolve()
    for fpath in fe_src.rglob("*"):
        if not fpath.is_file() or fpath.suffix.lower() not in (".jsx", ".tsx", ".vue"):
            continue
        if is_test_file(fpath, project_res):
            continue
        raw = read_text(fpath)
        # 剔除块注释与单行注释，避免注释里提及 <select> 产生误报
        no_block = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
        no_line = re.sub(r"(?m)^\s*//.*$", "", no_block)
        if re.search(r"<select(?:\s|>|/)", no_line, re.IGNORECASE):
            rel = fpath.relative_to(project_res).as_posix()
            issues.append(f"[UI-BASELINE] {rel}: 禁止裸用系统原生 <select>，请统一使用自定义圆角浮层下拉组件")
    return issues


def run_optional_scanners(project: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """自动探测并执行已安装的外部扫描器；未安装显式标 SKIPPED。"""
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    project_res = project.resolve()
    all_files = iter_project_files(project_res, include_docs_vibe=False)

    has_py = any(f.suffix == ".py" for f in all_files)
    has_backend_py = any(
        f.suffix == ".py" and f.relative_to(project_res).as_posix().startswith("backend/") for f in all_files
    )
    dockerfiles = [
        f
        for f in all_files
        if f.name.lower() == "dockerfile"
        or f.name.lower().startswith("dockerfile.")
        or f.name.lower().endswith(".dockerfile")
    ]

    # gitleaks
    if shutil.which("gitleaks"):
        res = run_cmd("gitleaks detect --no-git --source . --redact", cwd=project_res)
        status = "PASS" if res["passed"] else "FAIL"
        results.append({"tool": "gitleaks", "status": status, "returncode": res["returncode"]})
        if not res["passed"]:
            failures.append(f"gitleaks 扫描失败（exit={res['returncode']}）")
    else:
        results.append({"tool": "gitleaks", "status": "SKIPPED", "reason": "not installed"})

    # ruff
    if not shutil.which("ruff"):
        results.append({"tool": "ruff", "status": "SKIPPED", "reason": "not installed"})
    elif not has_py:
        results.append({"tool": "ruff", "status": "SKIPPED", "reason": "no python files"})
    else:
        res = run_cmd("ruff check .", cwd=project_res)
        status = "PASS" if res["passed"] else "FAIL"
        results.append({"tool": "ruff", "status": status, "returncode": res["returncode"]})
        if not res["passed"]:
            failures.append(f"ruff 检查未通过（exit={res['returncode']}）")

    # bandit
    if not shutil.which("bandit"):
        results.append({"tool": "bandit", "status": "SKIPPED", "reason": "not installed"})
    elif not has_backend_py:
        results.append({"tool": "bandit", "status": "SKIPPED", "reason": "no backend python files"})
    else:
        res = run_cmd("bandit -r backend -ll", cwd=project_res)
        status = "PASS" if res["passed"] else "FAIL"
        results.append({"tool": "bandit", "status": status, "returncode": res["returncode"]})
        if not res["passed"]:
            failures.append(f"bandit 安全扫描未通过（exit={res['returncode']}）")

    # hadolint
    if not shutil.which("hadolint"):
        results.append({"tool": "hadolint", "status": "SKIPPED", "reason": "not installed"})
    elif not dockerfiles:
        results.append({"tool": "hadolint", "status": "SKIPPED", "reason": "no Dockerfile found"})
    else:
        failed_df = []
        for df in dockerfiles:
            rel = df.relative_to(project_res).as_posix()
            res = run_cmd(f'hadolint "{rel}"', cwd=project_res)
            if not res["passed"]:
                failed_df.append(rel)
        if failed_df:
            results.append({"tool": "hadolint", "status": "FAIL", "files": failed_df})
            failures.append(f"hadolint 检查未通过: {', '.join(failed_df)}")
        else:
            results.append({"tool": "hadolint", "status": "PASS", "returncode": 0})

    return results, failures


def check_mutating_security_tests(project: Path) -> list[str]:
    """mutating 模式强制校验测试覆盖 401 / 403 / 409 / 超时不重试 4 类负面安全用例。"""
    project_res = project.resolve()
    test_files = [
        f
        for f in iter_project_files(project_res, include_docs_vibe=False)
        if is_test_file(f, project_res) and f.suffix.lower() in (".py", ".ts", ".tsx", ".js", ".jsx", ".go")
    ]
    if not test_files:
        return ["mutating 模式未找到任何自动化测试文件"]

    corpus = "\n".join(read_text(f) for f in test_files)
    missing: list[str] = []

    if not re.search(r"\b401\b|HTTP_401|UNAUTHORIZED", corpus, re.IGNORECASE):
        missing.append("401 未认证测试")
    if not re.search(r"\b403\b|HTTP_403|FORBIDDEN", corpus, re.IGNORECASE):
        missing.append("403 越权测试")
    if not re.search(r"\b409\b|HTTP_409|CONFLICT", corpus, re.IGNORECASE):
        missing.append("409 冲突防重测试")

    has_timeout = bool(re.search(r"timeout|timed\s*out|504|超时", corpus, re.IGNORECASE))
    has_no_retry = bool(
        re.search(
            r"no[_\s-]?retry|not[_\s-]?retry|retry|retries|call_count\s*==\s*1|assert_called_once|toHaveBeenCalledTimes\(1\)|不重试",
            corpus,
            re.IGNORECASE,
        )
    )
    if not (has_timeout and has_no_retry):
        missing.append("超时不重试测试（需同时体现 timeout 与无重试断言）")

    return [f"mutating 模式缺少必需负面安全测试: {', '.join(missing)}"] if missing else []


# ==================== 各阶段硬校验 ====================


def check_p1(project: Path, state: dict[str, Any], _args: argparse.Namespace | None = None) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    design = project / "docs" / "vibe" / "01-design.md"
    brief = project / "docs" / "vibe" / "01-brief.md"
    doc = design if design.exists() else brief
    proto = project / "docs" / "vibe" / "01-prototype" / "index.html"

    if not doc.exists() or not read_text(doc).strip():
        errors.append("缺少或为空: docs/vibe/01-design.md（或 01-brief.md）")
    else:
        text = read_text(doc)
        has_goal = bool(re.search(r"(目标|Goal|Objectives?)", text, re.IGNORECASE))
        has_non_goal = bool(re.search(r"(非目标|Non-?Goals?|Out of Scope|不做)", text, re.IGNORECASE))
        if not has_goal:
            errors.append(f"{doc.relative_to(project).as_posix()} 未写明“目标 / Goal”")
        if not has_non_goal:
            errors.append(f"{doc.relative_to(project).as_posix()} 未写明“非目标 / Non-Goal”")

    if not proto.exists() or not read_text(proto).strip():
        errors.append("缺少或为空: docs/vibe/01-prototype/index.html")
    else:
        parser = _HtmlValidator()
        try:
            parser.feed(read_text(proto))
            parser.close()
        except Exception as exc:
            errors.append(f"01-prototype/index.html 解析失败: {exc}")
        else:
            if len(parser.tags) < 3 or parser.text_len == 0:
                errors.append("01-prototype/index.html 内容过少，不是有效可交互 HTML 原型")

    return errors, {}


def check_p2(project: Path, state: dict[str, Any], _args: argparse.Namespace | None = None) -> tuple[list[str], dict[str, Any]]:
    """v3.0 P2：聚焦技术栈与核心运维机制确认（跳过假 React Mock 二次返工）。"""
    errors: list[str] = []

    if not state["gates"]["p1"].get("approved"):
        errors.append("前置门禁未通过：P1 尚未获得人工 approve p1")

    draft = project / "docs" / "vibe" / "02-architecture.draft.md"
    grill = project / "docs" / "vibe" / "02-grill.md"
    arch = project / "docs" / "vibe" / "02-architecture.md"

    for doc in (draft, grill, arch):
        if not doc.exists() or not read_text(doc).strip():
            errors.append(f"缺少或为空: {doc.relative_to(project).as_posix()}")

    if arch.exists() and read_text(arch).strip():
        a_text = read_text(arch)
        # 排除引用草案文件名（如 02-architecture.draft.md）造成的误报
        cleaned_text = re.sub(r"[\w./-]+\.draft\.md\b", "", a_text, flags=re.IGNORECASE)
        if re.search(r"(?i)\b(DRAFT|TBD|TODO|BLOCKER)\b|待定|阻断未知项", cleaned_text):
            errors.append("docs/vibe/02-architecture.md 仍含未定稿标记（DRAFT/TBD/TODO/BLOCKER/待定）")
        if not re.search(r"(技术栈|语言|框架|FastAPI|Gin|React|Vue)", a_text, re.IGNORECASE):
            errors.append("docs/vibe/02-architecture.md 未显式确认前后端技术栈（语言/框架）")
        if not re.search(r"(采集|检测|执行机制|核心机制|Collector|SSH|API)", a_text, re.IGNORECASE):
            errors.append("docs/vibe/02-architecture.md 未显式说明核心运维机制如何实现")

    return errors, {}


def check_p3(project: Path, state: dict[str, Any], args: argparse.Namespace | None = None) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []

    if not state["gates"]["p2"].get("approved"):
        errors.append("前置门禁未通过：P2（技术栈与核心机制）尚未获得人工 approve p2")

    # 校验根 AGENTS.md 安全红线未被删改
    agents_md = project / "AGENTS.md"
    expected_hash = state.get("agents_guard_sha256")
    actual_hash = extract_guard_hash(agents_md)
    if not agents_md.exists():
        errors.append("根目录缺少 AGENTS.md")
    elif not actual_hash or actual_hash != expected_hash:
        errors.append("根 AGENTS.md 安全红线区块（VIBE-GUARD）缺失或已被篡改")

    for rel in ("docs/vibe/03-spec.md", "docs/vibe/03-openapi.yaml", "docs/vibe/03-tasks.md", "docker-compose.yml"):
        p = project / rel
        if not p.exists() or not read_text(p).strip():
            errors.append(f"缺少或为空: {rel}")

    for dname in ("backend", "frontend"):
        d = project / dname
        if not d.is_dir() or not any(d.iterdir()):
            errors.append(f"缺少或为空目录: {dname}/")

    tasks_path = project / "docs" / "vibe" / "03-tasks.md"
    if tasks_path.exists():
        t_text = read_text(tasks_path)
        if not re.search(r"(401|403|安全用例|安全测试|security\s+test|rbac)", t_text, re.IGNORECASE):
            errors.append("docs/vibe/03-tasks.md 未包含安全用例任务")
        if state.get("mode") == "mutating" and not re.search(r"(409|防重|幂等|超时|timeout)", t_text, re.IGNORECASE):
            errors.append("mutating 模式：docs/vibe/03-tasks.md 需包含 409 防重/超时安全用例任务")

    cmds = state.get("commands") or {}
    allow_skip_fe = bool(getattr(args, "allow_skip_frontend", False))
    if not cmds.get("frontend_build", "").strip() and not allow_skip_fe:
        errors.append(".vibe/state.json 尚未配置 commands.frontend_build（纯离线演练可加 --allow-skip-frontend）")
    if not cmds.get("backend_test", "").strip():
        errors.append(".vibe/state.json 尚未配置 commands.backend_test")

    # v3.2：P3 空骨架阶段即提前执行容器/配置红线扫描，不等到 P4b 才暴露
    errors.extend(builtin_hard_scan(project))

    return errors, {}


def check_p4a(project: Path, state: dict[str, Any], args: argparse.Namespace | None = None) -> tuple[list[str], dict[str, Any]]:
    """v3.2 P4a：前端实现、构建与生产 UI 基线校验（验收通过后才准进入 P4b 写后端）。"""
    errors: list[str] = []
    extra: dict[str, Any] = {"command_results": []}

    if not state["gates"]["p3"].get("approved"):
        errors.append("前置门禁未通过：P3（骨架、核心逻辑与验收用例）尚未获得人工 approve p3")

    agents_md = project / "AGENTS.md"
    expected_hash = state.get("agents_guard_sha256")
    actual_hash = extract_guard_hash(agents_md)
    if not agents_md.exists() or not actual_hash or actual_hash != expected_hash:
        errors.append("根 AGENTS.md 安全红线区块（VIBE-GUARD）缺失或已被篡改")

    frontend_dir = project / "frontend"
    if not (frontend_dir / "package.json").exists():
        errors.append("缺少 frontend/package.json")

    cmds = state.get("commands") or {}
    allow_skip_fe = bool(getattr(args, "allow_skip_frontend", False))
    fb_cmd = (cmds.get("frontend_build") or "").strip()
    if fb_cmd and not allow_skip_fe:
        res = run_cmd(fb_cmd, cwd=project)
        res["name"] = "frontend_build"
        extra["command_results"].append(res)
        if not res["passed"]:
            errors.append(f"前端构建命令失败（exit={res['returncode']}）: {fb_cmd}")
    elif not fb_cmd and not allow_skip_fe:
        errors.append(".vibe/state.json 缺少 commands.frontend_build（纯离线演练请加 --allow-skip-frontend）")

    # 检查前端生产环境不能残留 VITE_USE_MOCK=true
    for env_name in (".env.production", ".env.prod"):
        ep = frontend_dir / env_name
        if ep.exists() and re.search(r"(?mi)^\s*VITE_USE_MOCK\s*=\s*['\"]?(?:true|1)['\"]?\s*$", read_text(ep)):
            errors.append(f"frontend/{env_name} 禁止开启 VITE_USE_MOCK=true")

    # v3.2：P4a 即执行内置硬扫描（含默认 Mock/凭据泄漏）与前端生产 UI 基线检查（禁原生 <select>）
    errors.extend(builtin_hard_scan(project))
    errors.extend(scan_frontend_ui_baseline(project))

    return errors, extra


def check_p4b(project: Path, state: dict[str, Any], args: argparse.Namespace | None = None) -> tuple[list[str], dict[str, Any]]:
    """v3.1 P4b：后端核心采集/业务实现、真实测试、安全扫描与双审查（必须先过 P4a 前端验收）。"""
    errors: list[str] = []
    extra: dict[str, Any] = {"command_results": [], "scanners": [], "hard_scan_issues": []}

    if not state["gates"]["p4a"].get("approved"):
        errors.append("前置门禁未通过：P4a（前端启动与人工验收）尚未获得人工 approve p4a，禁止进入后端验收")

    agents_md = project / "AGENTS.md"
    expected_hash = state.get("agents_guard_sha256")
    actual_hash = extract_guard_hash(agents_md)
    if not agents_md.exists() or not actual_hash or actual_hash != expected_hash:
        errors.append("根 AGENTS.md 安全红线区块（VIBE-GUARD）缺失或已被篡改")

    cmds = state.get("commands") or {}
    if not cmds.get("backend_test", "").strip():
        errors.append(".vibe/state.json 缺少必填命令 commands.backend_test")

    ran_test_outputs: list[str] = []
    for key in ("backend_test", "security_test"):
        cmd = (cmds.get(key) or "").strip()
        if not cmd:
            continue
        res = run_cmd(cmd, cwd=project)
        res["name"] = key
        extra["command_results"].append(res)
        if not res["passed"]:
            errors.append(f"命令 `{key}` 失败（exit={res['returncode']}）: {cmd}")
        ran_test_outputs.append(res["stdout_tail"] + "\n" + res["stderr_tail"])

    combined_test_out = "\n".join(ran_test_outputs)
    if combined_test_out and re.search(r"\bcollected 0 items\b|\b0 passed\b|\bno tests ran\b", combined_test_out, re.IGNORECASE):
        errors.append("后端/安全测试输出显示未实际执行任何用例（0 passed / collected 0 items）")

    core_pat = (state.get("core_test_pattern") or "").strip()
    if core_pat:
        passed_lines = "\n".join(ln for ln in combined_test_out.splitlines() if "PASSED" in ln)
        if not re.search(core_pat, passed_lines, re.IGNORECASE):
            errors.append(f"核心业务能力测试未在真实测试输出中通过（未匹配模式：{core_pat}）")

    scanners, scanner_failures = run_optional_scanners(project)
    extra["scanners"] = scanners
    errors.extend(scanner_failures)

    hard_issues = builtin_hard_scan(project)
    extra["hard_scan_issues"] = hard_issues
    errors.extend(hard_issues)

    if state.get("mode") == "mutating":
        errors.extend(check_mutating_security_tests(project))

    for rel in ("docs/vibe/04-code-review.md", "docs/vibe/04-ops-readiness.md"):
        p = project / rel
        if not p.exists() or not read_text(p).strip():
            errors.append(f"缺少或为空: {rel}")
        else:
            unresolved = has_unresolved_issue(read_text(p))
            if unresolved:
                errors.append(f"{rel} 存在未关闭 BLOCKER/FAIL: {unresolved[0]}")

    return errors, extra


def check_p5(project: Path, state: dict[str, Any], args: argparse.Namespace | None = None) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    extra: dict[str, Any] = {"evidence_files": []}

    if not state["gates"]["p4b"].get("approved"):
        errors.append("前置门禁未通过：P4b（后端实现与实测结果）尚未获得人工 approve p4b")

    report = project / "docs" / "vibe" / "05-e2e-report.md"
    if not report.exists() or not read_text(report).strip():
        errors.append("缺少或为空: docs/vibe/05-e2e-report.md")
    else:
        unresolved = has_unresolved_issue(read_text(report))
        if unresolved:
            errors.append(f"docs/vibe/05-e2e-report.md 存在未关闭 FAIL/BLOCKER: {unresolved[0]}")

    vibe_dir = project / "docs" / "vibe"
    evidence_exts = {".png", ".jpg", ".jpeg", ".webp", ".log", ".zip", ".har", ".webm", ".txt"}
    evidence_files: list[str] = []
    if vibe_dir.exists():
        for p in vibe_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in evidence_exts:
                evidence_files.append(p.relative_to(project).as_posix())
    extra["evidence_files"] = sorted(evidence_files)
    if not evidence_files and not bool(getattr(args, "allow_no_screenshots", False)):
        errors.append("docs/vibe/ 下未找到 E2E 截图或日志证据文件（无浏览器环境可加 --allow-no-screenshots）")

    p4a_gate = state["gates"]["p4a"]
    p4b_gate = state["gates"]["p4b"]
    scanners = p4b_gate.get("scanners", [])
    unverified = [f"{s['tool']} ({s.get('reason', 'skipped')})" for s in scanners if s.get("status") == "SKIPPED"]

    release_gate = {
        "generated_at": now_iso(),
        "project_name": state.get("project_name"),
        "mode": state.get("mode"),
        "ready_for_human_approval": len(errors) == 0,
        "p4a_commands": p4a_gate.get("command_results", []),
        "p4b_commands": [
            {
                "name": c.get("name"),
                "command": c.get("command"),
                "returncode": c.get("returncode"),
                "passed": c.get("passed"),
            }
            for c in p4b_gate.get("command_results", [])
        ],
        "scanners": scanners,
        "unverified_items": unverified,
        "e2e_evidence": extra["evidence_files"],
        "approvals": {
            g: {
                "approved": state["gates"][g].get("approved"),
                "approved_by": state["gates"][g].get("approved_by"),
                "approved_at": state["gates"][g].get("approved_at"),
            }
            for g in HUMAN_GATES
        },
        "blocking_errors": errors,
    }
    write_json(project / "docs" / "vibe" / "05-release-gate.json", release_gate)
    return errors, extra


CHECKERS = {
    "p1": check_p1,
    "p2": check_p2,
    "p3": check_p3,
    "p4a": check_p4a,
    "p4b": check_p4b,
    "p5": check_p5,
}


# ==================== 4 条 CLI 子命令 ====================


def cmd_init(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    project.mkdir(parents=True, exist_ok=True)
    (project / "docs" / "vibe").mkdir(parents=True, exist_ok=True)
    (project / ".vibe").mkdir(parents=True, exist_ok=True)

    state_path = project / ".vibe" / "state.json"
    agents_path = project / "AGENTS.md"

    if state_path.exists() and not args.force:
        print(f"[ERROR] {state_path} 已存在；如需覆盖请加 --force。", file=sys.stderr)
        return 1

    if not AGENTS_TEMPLATE_PATH.exists():
        print(f"[ERROR] 缺少模板文件: {AGENTS_TEMPLATE_PATH}", file=sys.stderr)
        return 1

    template = read_text(AGENTS_TEMPLATE_PATH)
    rendered = (
        template.replace("{{PROJECT_NAME}}", args.name)
        .replace("{{MODE}}", args.mode)
        .replace("{{GATE_SCRIPT}}", format_gate_script_ref(project))
    )
    agents_path.write_text(rendered, encoding="utf-8")

    guard_hash = extract_guard_hash(agents_path)
    if not guard_hash:
        print("[ERROR] 模板 AGENTS.md 缺少 VIBE-GUARD 区块。", file=sys.stderr)
        return 1

    gates: dict[str, Any] = {}
    for s in STAGES:
        entry: dict[str, Any] = {
            "status": "pending",
            "retries": 0,
            "last_checked_at": None,
            "findings": [],
        }
        if s in HUMAN_GATES:
            entry.update({"approved": False, "approved_at": None, "approved_by": None, "note": ""})
        gates[s] = entry

    state = {
        "schema_version": SCHEMA_VERSION,
        "project_name": args.name,
        "mode": args.mode,
        "selected_style": "",
        "core_test_pattern": "",
        "initialized_at": now_iso(),
        "current_stage": "p1",
        "max_retries": MAX_RETRIES,
        "agents_guard_sha256": guard_hash,
        "commands": {
            "frontend_build": "",
            "frontend_test": "",
            "backend_test": "",
            "security_test": "",
        },
        "gates": gates,
    }
    save_state(project, state)

    print(f"[OK] 已初始化项目 `{args.name}`（mode={args.mode}）")
    print(f"  - 控制中枢: {agents_path}")
    print(f"  - 状态文件: {state_path}")
    print(f"  - 产物目录: {project / 'docs' / 'vibe'}")
    print("下一步：进入 P1（devops-brainstorming -> frontend-design），完成后运行 check p1。")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    stage = args.stage.lower()
    state = load_state(project)
    gate = state["gates"][stage]

    errors, extra = CHECKERS[stage](project, state, args)
    gate["last_checked_at"] = now_iso()
    gate["findings"] = errors
    for k, v in extra.items():
        gate[k] = v

    if not errors:
        gate["status"] = "passed"
        gate["retries"] = 0
        if stage not in HUMAN_GATES and state.get("current_stage") == stage:
            state["current_stage"] = NEXT_STAGE[stage]
        save_state(project, state)

        print(f"[PASS] {stage.upper()} 门禁校验通过！")
        if stage in HUMAN_GATES:
            print(f"人工停手点：请人类核对产物后执行 `approve {stage}`。")
        else:
            print(f"已自动推进至下一阶段：{state['current_stage'].upper()}。")
        return 0

    gate["status"] = "failed"
    gate["retries"] = int(gate.get("retries", 0)) + 1
    max_retries = int(state.get("max_retries", MAX_RETRIES))
    save_state(project, state)

    print(f"[FAIL] {stage.upper()} 门禁校验未通过（第 {gate['retries']}/{max_retries} 轮）：")
    for idx, err in enumerate(errors, start=1):
        print(f"  {idx}. {err}")

    if gate["retries"] >= max_retries:
        print(f"\n[CIRCUIT BREAKER] {stage.upper()} 连续失败已达 {max_retries} 轮，触发熔断！请立即停手交由人类介入。")
        return 2
    return 1


def cmd_approve(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    stage = args.stage.lower()
    state = load_state(project)
    gate = state["gates"][stage]

    if gate.get("status") != "passed":
        print(f"[ERROR] {stage.upper()} 尚未通过 check（当前状态: {gate.get('status')}），禁止批准。", file=sys.stderr)
        return 1

    gate["approved"] = True
    gate["approved_at"] = now_iso()
    gate["approved_by"] = args.by or getpass.getuser()
    gate["note"] = args.note or ""
    state["current_stage"] = NEXT_STAGE[stage]
    save_state(project, state)

    print(f"[APPROVED] {stage.upper()} 已由 {gate['approved_by']} 批准，当前阶段推进至：{state['current_stage'].upper()}。")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    state = load_state(project)
    print(
        f"Project: {state['project_name']} | Mode: {state['mode']} | Current: {state['current_stage'].upper()} | Schema: v{state['schema_version']}"
    )
    print("-" * 72)
    for s in STAGES:
        g = state["gates"][s]
        if s in HUMAN_GATES:
            appr = f"approved({g['approved_by']})" if g.get("approved") else "waiting-human"
        else:
            appr = "auto"
        print(f"  {s.upper():<4} status={g['status']:<8} retries={g['retries']}/{state['max_retries']}   gate={appr}")
        for f in g.get("findings", [])[:3]:
            print(f"       - {f}")
    cmds = state.get("commands") or {}
    configured = [k for k, v in cmds.items() if str(v).strip()]
    print("-" * 72)
    print(f"Configured commands: {', '.join(configured) if configured else '(none)'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ops Vibe Coding v3.3 确定性门禁引擎")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="初始化目标项目")
    p_init.add_argument("--project", required=True, help="目标项目目录路径")
    p_init.add_argument("--name", required=True, help="项目名称")
    p_init.add_argument("--mode", required=True, choices=["readonly", "mutating"], help="运维风险模式")
    p_init.add_argument("--force", action="store_true", help="强制覆盖已有 .vibe/state.json 和 AGENTS.md")
    p_init.set_defaults(func=cmd_init)

    p_check = sub.add_parser("check", help="执行指定阶段硬校验")
    p_check.add_argument("stage", choices=STAGES, help="阶段名称 (p1..p5)")
    p_check.add_argument("--project", default=".", help="目标项目目录（默认当前目录）")
    p_check.add_argument("--allow-skip-frontend", action="store_true", help="离线演练时显式允许跳过前端构建")
    p_check.add_argument("--allow-no-screenshots", action="store_true", help="无浏览器环境时显式允许无截图证据")
    p_check.set_defaults(func=cmd_check)

    p_approve = sub.add_parser("approve", help="人类批准阶段放行")
    p_approve.add_argument("stage", choices=HUMAN_GATES, help="人工验收阶段 (p1..p5)")
    p_approve.add_argument("--project", default=".", help="目标项目目录（默认当前目录）")
    p_approve.add_argument("--by", default="", help="批准人标识（默认系统用户名）")
    p_approve.add_argument("--note", default="", help="批准备注")
    p_approve.set_defaults(func=cmd_approve)

    p_status = sub.add_parser("status", help="查看项目门禁状态")
    p_status.add_argument("--project", default=".", help="目标项目目录（默认当前目录）")
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
