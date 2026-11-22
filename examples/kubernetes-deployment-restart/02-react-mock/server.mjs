import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {createMockStore} from './mock.mjs';
import {RESTART_PATH} from './target.mjs';

const staticFiles = new Map([
  ['/', ['./index.html', 'text/html']],
  ['/app.js', ['./dist/app.js', 'text/javascript']],
  ['/style.css', ['../01-prototype/style.css', 'text/css']],
  ['/prototype/', ['../01-prototype/index.html', 'text/html']],
  ['/prototype/style.css', ['../01-prototype/style.css', 'text/css']],
  ['/prototype/prototype.js', ['../01-prototype/prototype.js', 'text/javascript']],
]);

export function createDemoServer() {
  const store = createMockStore();
  const server = createServer(async (request, response) => {
    const url = new URL(request.url, 'http://127.0.0.1');
    const json = (code, body) => {
      response.writeHead(code, {'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store'});
      response.end(JSON.stringify(body));
    };
    try {
      // 限制本机来源。模拟服务不读取 kubeconfig，也没有真实集群客户端。
      if (request.headers.origin && request.headers.origin !== 'http://' + request.headers.host) {
        return json(403, {error: '来源不在本地范围'});
      }
      if (request.method === 'GET' && url.pathname === '/api/audit') {
        const record = store.lookup(url.searchParams.get('operation_id'));
        return record ? json(200, {record}) : json(404, {error: '本次服务中无此记录，请保留原操作 ID'});
      }
      if (request.method === 'POST' && url.pathname === RESTART_PATH) {
        if (request.headers['content-type'] !== 'application/json') return json(415, {error: '预期 JSON'});
        let input = '';
        for await (const chunk of request) {
          input += chunk;
          if (input.length > 2048) return json(413, {error: '请求过大'});
        }
        let body;
        try { body = JSON.parse(input); } catch { return json(400, {error: 'JSON 无效'}); }
        const result = store.submit(body?.target, request.headers['x-operation-id'], body?.scenario);
        return json(result.code, result);
      }
      if (request.method === 'GET' && url.pathname === '/favicon.ico') {
        response.writeHead(204).end();
        return;
      }
      const file = staticFiles.get(url.pathname);
      if (request.method !== 'GET' || !file) return json(404, {error: '无此路径'});
      const bytes = await readFile(new URL(file[0], import.meta.url));
      response.writeHead(200, {'Content-Type': file[1] + '; charset=utf-8', 'Cache-Control': 'no-store'});
      response.end(bytes);
    } catch {
      json(500, {error: '本地材料读取失败。请确认已执行 npm run build。'});
    }
  });
  return {server, store};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  createDemoServer().server.listen(Number(process.env.PORT || 4173), '127.0.0.1', function () {
    console.log('Restart Mock: http://127.0.0.1:' + this.address().port);
  });
}
