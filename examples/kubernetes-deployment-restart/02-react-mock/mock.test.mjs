import assert from 'node:assert/strict';
import test from 'node:test';
import { createMockStore } from './mock.mjs';
import { TARGET } from './target.mjs';

test('a fresh store has zero simulated mutations', () => {
  assert.equal(createMockStore().mutationCount, 0);
});

test('submitted means remote acceptance and recorded final audit', () => {
  const store = createMockStore();
  const { code, record } = store.submit(TARGET, 'op-accepted', 'accepted');
  assert.equal(code, 200);
  assert.deepEqual([record.state, record.remote, record.audit], ['SUBMITTED', 'accepted', 'confirmed']);
  assert.deepEqual(store.lookup('op-accepted'), record);
});

test('replay returns the same result; new ID cannot submit an unknown target', () => {
  const store = createMockStore();
  const first = store.submit(TARGET, 'op-unknown', 'timeout');
  assert.equal(first.code, 504);
  assert.deepEqual(store.submit(TARGET, 'op-unknown', 'accepted'), first);
  assert.equal(store.submit(TARGET, 'op-second', 'accepted').code, 409);
  assert.equal(store.mutationCount, 1);
});

test('binding rejects an out-of-scope target before lookup or mutation', () => {
  const store = createMockStore();
  store.submit(TARGET, 'op-1', 'accepted');
  assert.equal(store.submit({...TARGET, namespace:'other'}, 'op-1', 'accepted').code, 403);
  assert.equal(store.mutationCount, 1);
});

test('uncertain audit retains the occupied target even after remote acceptance', () => {
  const store = createMockStore();
  const { code, record } = store.submit(TARGET, 'op-audit', 'audit-unconfirmed');
  assert.equal(code, 503);
  assert.deepEqual([record.state, record.remote, record.audit], ['SUBMITTING', 'accepted', 'unconfirmed']);
  assert.equal(store.submit(TARGET, 'op-2', 'accepted').code, 409);
  assert.equal(store.mutationCount, 1);
});

test('definite rejection has a record and permits a new independent operation', () => {
  const store = createMockStore();
  assert.equal(store.submit(TARGET, 'op-rejected', 'rejected').record.state, 'REJECTED');
  assert.equal(store.submit(TARGET, 'op-next', 'accepted').code, 200);
});
