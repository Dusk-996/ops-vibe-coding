(() => {
  const $ = (selector) => document.querySelector(selector);
  const dialog = $('dialog');
  const panel = $('.result');
  const messages = {
    accepted: ['请求已提交', '模拟 API 已接受并记录；rollout 尚未验证。', 'SUBMITTED', 'accepted', 'confirmed'],
    timeout: ['结果待核验', '请求可能已执行，请勿重复提交。请保留操作 ID 并联系核验人员。', 'UNKNOWN', 'unknown', 'confirmed'],
    rejected: ['请求被拒绝', '模拟 API 明确拒绝，本次未形成变更。', 'REJECTED', 'rejected', 'confirmed'],
    'audit-unconfirmed': ['最终审计待核验', '模拟 API 已接受，最终审计尚未确认。请保留操作 ID 并联系核验人员。', 'SUBMITTING', 'accepted', 'unconfirmed'],
  };
  const storageKey = 'restart:prototype:lab/staging/checkout';
  let record;
  $('#restart').onclick = () => dialog.showModal();
  $('#cancel').onclick = () => dialog.close();
  function showRecord() {
    const [title, detail, state] = messages[record.scenario];
    panel.hidden = false;
    $('.result h2').textContent = title;
    $('.result p').textContent = detail;
    $('.result code').textContent = record.id;
    $('.result pre').hidden = true;
    $('#restart').disabled = state === 'UNKNOWN' || state === 'SUBMITTING';
  }
  $('#submit').onclick = () => {
    dialog.close();
    const scenario = $('#scenario').value;
    const [, , state, remote, audit] = messages[scenario];
    record = {id: 'prototype-' + crypto.randomUUID(), scenario, state, remote, audit};
    try { sessionStorage.setItem(storageKey, JSON.stringify(record)); } catch { /* 部分 file:// 环境禁用会话存储。 */ }
    showRecord();
  };
  $('#audit').onclick = () => {
    const output = $('.result pre');
    output.textContent = [record.state, record.remote, record.audit].join(' / ');
    output.hidden = false;
  };
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey));
    if (saved && Object.hasOwn(messages, saved.scenario) && typeof saved.id === 'string') {
      record = saved;
      $('#scenario').value = saved.scenario;
      showRecord();
    }
  } catch { /* 首次打开或未提供会话存储时显示空状态。 */ }
})();
