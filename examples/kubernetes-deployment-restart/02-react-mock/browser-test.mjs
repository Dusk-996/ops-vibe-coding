import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {mkdir, mkdtemp, writeFile} from 'node:fs/promises';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {sep} from 'node:path';
import {once} from 'node:events';
import {chromium} from 'playwright-core';
import {createDemoServer} from './server.mjs';

const candidates = [
  process.env.CHROME_PATH, chromium.executablePath(),
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].filter(Boolean);
const executablePath = candidates.find(existsSync);
const dist = new URL('./dist/', import.meta.url);
await mkdir(dist, {recursive: true});
const evidence = pathToFileURL(await mkdtemp(fileURLToPath(new URL('e2e-', dist))) + sep);
console.log('Evidence:', fileURLToPath(evidence));
let browser;
const report = {started: new Date().toISOString(), node: process.version, browser: null, cases: [], parity: []};
async function fixture(viewport, run) {
  const {server, store} = createDemoServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const context = await browser.newContext({viewport, locale: 'zh-CN', deviceScaleFactor: 1});
  const origin = 'http://127.0.0.1:' + server.address().port;
  const events = [];
  const external = [];
  try {
    await context.route('**/*', route => {
      if (new URL(route.request().url()).origin === origin) return route.continue();
      external.push(route.request().url());
      return route.abort();
    });
    const page = await context.newPage();
    context.on('response', response => {
      const url = new URL(response.url());
      if (url.pathname.startsWith('/api/')) {
        events.push({method: response.request().method(), path: url.pathname + url.search,
          code: response.status(), operationId: response.request().headers()['x-operation-id'] || undefined});
      }
    });
    await run({store, page, origin, events});
    assert.deepEqual(external, [], '浏览器请求越出获批回环地址');
  } finally {
    await context.close();
    await new Promise(resolve => server.close(resolve));
  }
}
const click = (page, name) => page.getByRole('button', {name, exact: true}).click();
async function openDialog(page) {
  await click(page, '重启 Deployment');
  const dialog = page.getByRole('dialog');
  await dialog.waitFor();
  assert.match(await dialog.innerText(), /集群 lab \/ Namespace staging \/ Deployment checkout/);
}
const cases = [
  {name: 'cancel', title: null},
  {name: 'accepted', title: '请求已提交', log: 'SUBMITTED / accepted / confirmed', code: 200},
  {name: 'timeout', title: '结果待核验', log: 'UNKNOWN / unknown / confirmed', code: 504},
  {name: 'rejected', title: '请求被拒绝', log: 'REJECTED / rejected / confirmed', code: 422},
  {name: 'audit-unconfirmed', title: '最终审计待核验', log: 'SUBMITTING / accepted / unconfirmed', code: 503},
];
async function testCase(sample, entry) {
  await fixture({width: 1280, height: 800}, async ({store, page, origin, events}) => {
    entry.events = events;
    try {
      await page.goto(origin);
      if (sample.title) await page.getByLabel('模拟条件').selectOption(sample.name);
      await openDialog(page);
      if (!sample.title) {
        await click(page, '取消');
        await page.getByRole('dialog').waitFor({state: 'hidden'});
        assert.equal(await page.locator('.result').count(), 0);
      } else {
        await click(page, '确认提交');
        await page.getByRole('heading', {name: sample.title, exact: true}).waitFor();
        const operationId = await page.locator('.result code').textContent();
        assert.match(operationId, /^[0-9a-f-]{36}$/);
        assert.equal(events[0].code, sample.code);
        assert.equal(events[0].operationId, operationId);
        await click(page, '查看操作记录');
        await page.getByText(sample.log, {exact: true}).waitFor();
        assert.equal(store.lookup(operationId).id, operationId);
        assert.match(events[1].path, new RegExp(operationId + '$'));
        if (sample.name === 'accepted') assert.match(await page.locator('.result').innerText(), /rollout 尚未验证/);
        if (['timeout', 'audit-unconfirmed'].includes(sample.name)) {
          assert.equal(await page.getByRole('button', {name: '重启 Deployment'}).isDisabled(), true);
          const restored = page.waitForResponse(r => r.url().includes('/api/audit?'));
          await page.reload();
          await restored;
          await click(page, '查看操作记录');
          await page.getByText(sample.log, {exact: true}).waitFor();
          assert.equal(await page.locator('.result code').textContent(), operationId);
          assert.equal(await page.getByRole('button', {name: '重启 Deployment'}).isDisabled(), true);
          const path = fileURLToPath(new URL(sample.name + '.png', evidence));
          await page.screenshot({path, fullPage: true});
          entry.screenshots.push(sample.name + '.png');
        }
      }
      const expected = sample.title ? 1 : 0;
      assert.equal(events.filter(x => x.method === 'POST').length, expected);
      assert.equal(store.mutationCount, expected);
      console.log('PASS', sample.name, 'mock mutations', store.mutationCount);
    } finally { entry.mutationCount = store.mutationCount; }
  });
}
async function parity(size, viewport, entry) {
  await fixture(viewport, async ({page, origin}) => {
    const images = [];
    const panels = [];
    for (const [name, route] of [['prototype', '/prototype/'], ['react', '/']]) {
      await page.goto(origin + route);
      await openDialog(page);
      const filename = size + '-' + name + '-confirm.png';
      images.push(await page.screenshot({path: fileURLToPath(new URL(filename, evidence)), fullPage: true}));
      entry.screenshots.push(filename);
      await click(page, '取消');
      await page.getByLabel('模拟条件').selectOption('timeout');
      await openDialog(page);
      await click(page, '确认提交');
      await page.getByRole('heading', {name: '结果待核验'}).waitFor();
      await click(page, '查看操作记录');
      await page.getByText('UNKNOWN / unknown / confirmed', {exact: true}).waitFor();
      panels.push({
        title: await page.locator('.result h2').innerText(), message: await page.locator('.result p').innerText(),
        audit: await page.locator('.result pre').innerText(),
        disabled: await page.getByRole('button', {name: '重启 Deployment'}).isDisabled(),
      });
    }
    assert.deepEqual(panels[0], panels[1]);
    const identical = images[0].equals(images[1]);
    Object.assign(entry, {viewport, confirmationScreenshotsEqual: identical, unknownPanel: panels[0]});
    console.log('COMPARE', size, 'identical confirmation PNG:', identical);
  });
}
async function conflictWindows(entry) {
  await fixture({width: 1280, height: 800}, async ({page, origin, events, store}) => {
    entry.events = events;
    const other = await page.context().newPage();
    try {
      await page.goto(origin);
      await other.goto(origin);
      await page.getByLabel('模拟条件').selectOption('timeout');
      await openDialog(page);
      await click(page, '确认提交');
      await page.getByRole('heading', {name: '结果待核验'}).waitFor();
      const original = await page.locator('.result code').textContent();
      await openDialog(other);
      await click(other, '确认提交');
      await other.locator('.result h2').waitFor();
      assert.equal(await other.locator('.result h2').innerText(), '本次未提交');
      const posts = events.filter(e => e.method === 'POST');
      assert.deepEqual(posts.map(e => e.code), [504, 409]);
      assert.notEqual(posts[1].operationId, original);
      for (const reload of [false, true]) {
        if (reload) {
          const restored = other.waitForResponse(r => r.url().includes('operation_id=' + original));
          await other.reload();
          await restored;
        }
        assert.equal(await other.locator('.result h2').innerText(), '本次未提交');
        assert.equal(await other.locator('.result code').innerText(), original);
        assert.equal(await other.locator('.result samp').innerText(), posts[1].operationId);
        assert.equal(await other.getByRole('button', {name: '重启 Deployment'}).isDisabled(), true);
        await click(other, '查看操作记录');
        await other.getByText('UNKNOWN / unknown / confirmed', {exact: true}).waitFor();
      }
      assert.equal(events.filter(e => e.method === 'POST').length, 2);
      assert.equal(store.mutationCount, 1);
      await other.screenshot({path: fileURLToPath(new URL('conflict.png', evidence)), fullPage: true});
      entry.screenshots.push('conflict.png');
    } finally {
      entry.mutationCount = store.mutationCount;
      await other.close();
    }
  });
}
async function prototypeReload(entry) {
  await fixture({width: 390, height: 844}, async ({page, origin, events, store}) => {
    entry.events = events;
    await page.goto(origin + '/prototype/');
    await page.getByLabel('模拟条件').selectOption('timeout');
    await openDialog(page);
    await click(page, '确认提交');
    const original = await page.locator('.result code').innerText();
    await page.reload();
    assert.equal(await page.locator('.result').isVisible(), true);
    assert.equal(await page.locator('.result code').innerText(), original);
    assert.equal(await page.getByRole('button', {name: '重启 Deployment'}).isDisabled(), true);
    await click(page, '查看操作记录');
    await page.getByText('UNKNOWN / unknown / confirmed', {exact: true}).waitFor();
    assert.equal(events.length, 0);
    entry.operationId = original;
    entry.mutationCount = store.mutationCount;
    await page.screenshot({path: fileURLToPath(new URL('prototype-reload.png', evidence)), fullPage: true});
    entry.screenshots.push('prototype-reload.png');
  });
}
const planned = [
  ...cases.map(sample => ({name: sample.name, results: report.cases, run: entry => testCase(sample, entry)})),
  {name: 'conflict-windows', results: report.cases, run: conflictWindows},
  {name: 'prototype-reload', results: report.cases, run: prototypeReload},
  ...Object.entries({desktop: {width: 1280, height: 800}, mobile: {width: 390, height: 844}})
    .map(([size, viewport]) => ({name: size, results: report.parity, run: entry => parity(size, viewport, entry)})),
];
for (const task of planned) {
  task.entry = {name: task.name, status: 'SKIPPED', reason: '尚未执行', screenshots: []};
  task.results.push(task.entry);
}
try {
  if (!executablePath) throw new Error('请通过 CHROME_PATH 指向现有 Chrome/Chromium 可执行文件。');
  browser = await chromium.launch({executablePath, headless: true, args: ['--no-proxy-server']});
  report.browser = browser.version();
  const selection = process.argv[2];
  if (selection && !planned.some(task => task.name === selection)) throw Error('未知用例 ' + selection);
  for (const task of planned) {
    if (selection && selection !== task.name) {
      task.entry.reason = '本轮仅复测 ' + selection;
      continue;
    }
    delete task.entry.reason;
    try {
      await task.run(task.entry);
      task.entry.status = 'PASS';
    } catch (error) {
      task.entry.status = 'FAIL';
      task.entry.reason = error.message;
      throw new Error(task.name + ': ' + error.message, {cause: error});
    }
  }
} catch (error) {
  report.failure = error.message;
  for (const task of planned) {
    if (task.entry.status === 'SKIPPED') task.entry.reason = '本轮测试已停止：' + report.failure;
  }
  process.exitCode = 1;
  console.error(error);
} finally {
  await browser?.close();
  report.finished = new Date().toISOString();
  await writeFile(new URL('run.json', evidence), JSON.stringify(report, null, 2) + '\n');
}
