async page => {
  if (new URL(page.url()).hostname !== '127.0.0.1') throw Error('预期本地回环页面');
  const paths = [];
  page.on('request', req => {
    if (new URL(req.url()).pathname.startsWith('/api/')) paths.push(req.method() + ' ' + new URL(req.url()).pathname);
  });
  const click = name => page.getByRole('button', {name, exact: true}).click();
  await click('重启 Deployment');
  await click('取消');
  if (paths.length) throw Error('取消产生 API 请求');
  await click('重启 Deployment');
  await click('确认提交');
  await page.getByRole('heading', {name: '请求已提交'}).waitFor();
  await click('查看操作记录');
  await page.getByText('SUBMITTED / accepted / confirmed', {exact: true}).waitFor();
  const id = await page.locator('.result code').innerText();
  if (paths.length !== 2 || !id) throw Error('预期一次提交和一次查询');
  return {cancelApiCalls: 0, requests: paths, operationId: id, summary: 'SUBMITTED / accepted / confirmed'};
}
