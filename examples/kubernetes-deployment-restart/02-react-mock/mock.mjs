import {TARGET} from './target.mjs';

const outcomes = new Map([
  ['accepted', [200, 'SUBMITTED', 'accepted', 'confirmed']],
  ['timeout', [504, 'UNKNOWN', 'unknown', 'confirmed']],
  ['rejected', [422, 'REJECTED', 'rejected', 'confirmed']],
  ['audit-unconfirmed', [503, 'SUBMITTING', 'accepted', 'unconfirmed']],
]);

export function createMockStore() {
  const responses = new Map();
  let occupiedId;
  let mutationCount = 0;

  return {
    get mutationCount() { return mutationCount; },
    lookup(id) { return responses.get(id)?.record; },
    submit(target, id, scenario) {
      if (!Object.entries(TARGET).every(([key, value]) => target?.[key] === value)) {
        return {code: 403, error: '目标超出本地范围'};
      }
      if (!/^[A-Za-z0-9-]{1,80}$/.test(id ?? '') || !outcomes.has(scenario)) {
        return {code: 400, error: '操作 ID 或样本无效'};
      }
      if (responses.has(id)) return responses.get(id);
      if (occupiedId) return {code: 409, record: responses.get(occupiedId).record};

      // 此处只统计模拟变更尝试；未知及审计未确认均保持该目标占用。
      mutationCount++;
      const [code, state, remote, audit] = outcomes.get(scenario);
      const record = Object.freeze({id, target: TARGET, state, remote, audit});
      const response = Object.freeze({code, record});
      responses.set(id, response);
      if (state === 'UNKNOWN' || state === 'SUBMITTING') occupiedId = id;
      return response;
    },
  };
}
