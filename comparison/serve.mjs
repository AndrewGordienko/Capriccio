import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('./dist/', import.meta.url));
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mp4':'video/mp4','.jpg':'image/jpeg'};
http.createServer((req,res)=>{
  let target;
  try {target=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));}
  catch{res.writeHead(400).end();return;}
  if(target===root || target===root.slice(0,-1))target=path.join(root,'index.html');
  if(!target.startsWith(root)){res.writeHead(403).end();return;}
  let stat;try{stat=fs.statSync(target);}catch{res.writeHead(404).end('Not found');return;}
  if(!stat.isFile()){res.writeHead(404).end();return;}
  const headers={'Content-Type':mime[path.extname(target)]||'application/octet-stream','Accept-Ranges':'bytes','Cache-Control':'no-cache'};
  let start=0,end=stat.size-1,status=200;
  if(req.headers.range){
    const match=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
    if(!match || (!match[1]&&!match[2])){res.writeHead(416,{'Content-Range':`bytes */${stat.size}`}).end();return;}
    if(match[1]){start=Number(match[1]);if(match[2])end=Math.min(Number(match[2]),end);}
    else start=Math.max(0,stat.size-Number(match[2]));
    if(start>end || start>=stat.size){res.writeHead(416,{'Content-Range':`bytes */${stat.size}`}).end();return;}
    status=206;headers['Content-Range']=`bytes ${start}-${end}/${stat.size}`;
  }
  headers['Content-Length']=end-start+1;
  res.writeHead(status,headers);
  if(req.method==='HEAD'){res.end();return;}
  const stream=fs.createReadStream(target,{start,end});stream.on('error',()=>res.destroy());req.on('close',()=>stream.destroy());stream.pipe(res);
}).listen(3000,'127.0.0.1',()=>console.log('Listening Room: http://localhost:3000'));
