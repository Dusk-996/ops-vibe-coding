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
  let record;
  let counter = 0;
  $('#restart').onclick = () => dialog.showModal();
  $('#cancel').onclick = () => dialog.close();
  $('#submit').onclick = () => {
    dialog.close();
    const [title, detail, state, remote, audit] = messages[$('#scenario').value];
    record = {id: 'prototype-' + (++counter), state, remote, audit};
    panel.hidden = false;
    $('.result h2').textContent = title;
    $('.result p').textContent = detail;
    $('.result code').textContent = record.id;
    $('.result pre').hidden = true;
    $('#restart').disabled = state === 'UNKNOWN' || state === 'SUBMITTING';
  };
  $('#audit').onclick = () => {
    const output = $('.result pre');
    output.textContent = [record.state, record.remote, record.audit].join(' / ');
    output.hidden = false;
  };
})();
