import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {TARGET as target, RESTART_PATH} from './target.mjs';

const storageKey = ['restart', target.cluster, target.namespace, target.name, 'last-operation'].join(':');
const targetLabel = `集群 ${target.cluster} / Namespace ${target.namespace} / Deployment ${target.name}`;
const copy = {
  SUBMITTED: ['请求已提交', '模拟 API 已接受并记录；rollout 尚未验证。'],
  REJECTED: ['请求被拒绝', '模拟 API 明确拒绝，本次未形成变更。'],
  UNKNOWN: ['结果待核验', '请求可能已执行，请勿重复提交。请保留操作 ID 并联系核验人员。'],
  SUBMITTING: ['最终审计待核验', '模拟 API 已接受，最终审计尚未确认。请保留操作 ID 并联系核验人员。'],
  UNVERIFIED: ['结果待核验', '当前无法读取记录。请保留操作 ID 并联系核验人员。'],
};
async function lookup(id) {
  const response = await fetch('/api/audit?operation_id=' + encodeURIComponent(id));
  if (!response.ok) throw new Error('未读取到操作记录');
  return (await response.json()).record;
}
function Demo() {
  const [scenario, setScenario] = useState('accepted');
  const [record, setRecord] = useState(() => {
    const id = sessionStorage.getItem(storageKey);
    return id ? {id, state: 'UNVERIFIED'} : null;
  });
  const [busy, setBusy] = useState(false);
  const [conflictId, setConflictId] = useState(() => sessionStorage.getItem(storageKey + ':conflict'));
  const [auditText, setAuditText] = useState('');
  const dialog = useRef(null);
  const lock = useRef(false);
  useEffect(() => {
    const id = sessionStorage.getItem(storageKey);
    if (!id) return;
    let current = true;
    lookup(id).then(row => { if (current) setRecord(row); }).catch(() => {});
    return () => { current = false; };
  }, []);
  async function submit() {
    if (lock.current) return;
    lock.current = true;
    dialog.current.close();
    setBusy(true);
    setAuditText('');
    const id = crypto.randomUUID();
    sessionStorage.setItem(storageKey, id);
    sessionStorage.removeItem(storageKey + ':conflict');
    setConflictId(null);
    try {
      const response = await fetch(RESTART_PATH, {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-Operation-ID': id},
        body: JSON.stringify({target, scenario}),
      });
      const result = await response.json();
      if (!result.record) throw new Error('未取得操作记录');
      if (response.status === 409) {
        // 分开保留被拒的新请求和占用目标的原记录；刷新只查询原记录。
        sessionStorage.setItem(storageKey + ':conflict', id);
        setConflictId(id);
      }
      sessionStorage.setItem(storageKey, result.record.id);
      setRecord(result.record);
    } catch {
      // 即使响应未到，本次操作也可能已经到达服务；保留 ID 并禁止自动重发。
      setRecord({id, state: 'UNVERIFIED'});
    } finally {
      setBusy(false);
      lock.current = false;
    }
  }
  async function showAudit() {
    setBusy(true);
    try {
      const row = await lookup(record.id);
      setRecord(row);
      setAuditText([row.state, row.remote, row.audit].join(' / '));
    } catch {
      setAuditText('未读取到操作记录。请保留原操作 ID。');
    } finally { setBusy(false); }
  }
  const blocked = busy || (record && !['SUBMITTED', 'REJECTED'].includes(record.state));
  return <>
    <header><h1>Deployment 重启</h1><p>本地模拟 · 单目标提交</p></header>
    <section className="card"><h2>操作目标</h2>
      <dl><div><dt>集群</dt><dd>{target.cluster}</dd></div><div><dt>Namespace</dt><dd>{target.namespace}</dd></div><div><dt>Deployment</dt><dd>{target.name}</dd></div></dl>
      <label>模拟条件<select value={scenario} onChange={event => setScenario(event.target.value)}>
        <option value="accepted">接受并记录</option><option value="timeout">提交超时</option>
        <option value="rejected">明确拒绝</option><option value="audit-unconfirmed">最终审计未确认</option>
      </select></label>
      <div className="actions"><button className="primary" disabled={blocked} onClick={() => dialog.current.showModal()}>{busy ? '处理中…' : '重启 Deployment'}</button></div>
    </section>
    <dialog ref={dialog} aria-labelledby="confirm-title"><h2 id="confirm-title">确认重启目标</h2>
      <p>{targetLabel}</p><div className="actions">
        <button onClick={() => dialog.current.close()}>取消</button><button className="primary" onClick={submit}>确认提交</button>
      </div></dialog>
    {record && <section aria-live="polite" className="card result"><h2>{conflictId ? '本次未提交' : copy[record.state][0]}</h2>
      {conflictId && <><p>另一笔操作已占用目标，本次未执行模拟变更。下方为占用操作的记录。</p><div>本次请求 ID <samp>{conflictId}</samp></div></>}
      <p>{copy[record.state][1]}</p>
      <div>{conflictId ? '占用操作 ID' : '操作 ID'} <code>{record.id}</code></div><div className="actions"><button disabled={busy} onClick={showAudit}>查看操作记录</button></div>
      {auditText && <pre>{auditText}</pre>}</section>}
  </>;
}
createRoot(document.getElementById('app')).render(<Demo/>);
