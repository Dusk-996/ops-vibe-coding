export const TARGET = Object.freeze({cluster:'lab', namespace:'staging', name:'checkout'});

export function createMockStore() {
  const rows = new Map();
  let count = 0;
  return {
    get mutationCount() { return count; },
    lookup(id) { return rows.get(id); },
    submit(target, id) {
      count++;
      const record = {id, target, state:'SUBMITTED', remote:'accepted', audit:'confirmed'};
      rows.set(id, record);
      return {code:200, record};
    }
  };
}
