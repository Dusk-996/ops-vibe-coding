import {build} from 'esbuild';
await build({
  entryPoints: ['app.jsx'], outfile: 'dist/app.js', bundle: true, minify: true,
  define: {'process.env.NODE_ENV': '"production"'},
});
