import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {once} from 'node:events';
import {chromium} from 'playwright-core';
import {createDemoServer} from './server.mjs';

const candidates = [
  process.env.CHROME_PATH, chromium.executablePath(),
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].filter(Boolean);
const executablePath = candidates.find(existsSync);
if (!executablePath) throw new Error('请通过 CHROME_PATH 指向现有 Chrome/Chromium 可执行文件。');

const evidence = new URL('../09-e2e/evidence/', import.meta.url);
await mkdir(evidence, {recursive: true});
const browser = await chromium.launch({executablePath, headless: true, args: ['--no-proxy-server']});
const report = {started: new Date().toISOString(), node: process.version, browser: browser.version(), cases: [], parity: []};
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
    page.on('response', response => {
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
async function testCase(sample) {
  await fixture({width: 1280, height: 800}, async ({store, page, origin, events}) => {
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
      }
    }
    const expected = sample.title ? 1 : 0;
    assert.equal(events.filter(x => x.method === 'POST').length, expected);
    assert.equal(store.mutationCount, expected);
    report.cases.push({name: sample.name, status: 'PASS', title: sample.title, events, mutationCount: store.mutationCount});
    console.log('PASS', sample.name, 'mock mutations', store.mutationCount);
  });
}
async function parity(size, viewport) {
  await fixture(viewport, async ({page, origin}) => {
    const images = [];
    const panels = [];
    for (const [name, route] of [['prototype', '/prototype/'], ['react', '/']]) {
      await page.goto(origin + route);
      await openDialog(page);
      const filename = size + '-' + name + '-confirm.png';
      images.push(await page.screenshot({path: fileURLToPath(new URL(filename, evidence)), fullPage: true}));
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
    report.parity.push({size, viewport, confirmationScreenshotsEqual: identical, unknownPanel: panels[0]});
    console.log('COMPARE', size, 'identical confirmation PNG:', identical);
  });
}
try {
  for (const sample of cases) await testCase(sample);
  await parity('desktop', {width: 1280, height: 800});
  await parity('mobile', {width: 390, height: 844});
} catch (error) {
  report.failure = error.message;
  process.exitCode = 1;
  console.error(error);
} finally {
  await browser.close();
  report.finished = new Date().toISOString();
  await writeFile(new URL('run.json', evidence), JSON.stringify(report, null, 2) + '\n');
}
