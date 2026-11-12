import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
const root=fileURLToPath(new URL('..',import.meta.url));
const runtimePython='/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const python=process.env.STUDIO_PYTHON||process.env.CODEX_PRIMARY_RUNTIME_PYTHON||(existsSync(runtimePython)?runtimePython:'python3');
const backend=spawn(python,['-m','uvicorn','backend.app:app','--host','127.0.0.1','--port','8001'],{cwd:root,stdio:'inherit',env:{...process.env,PYTHONPATH:root+'/.runtime/python'+(process.env.PYTHONPATH?':'+process.env.PYTHONPATH:''),OMP_NUM_THREADS:'1',OPENBLAS_NUM_THREADS:'1'}});
let vite;
function stop(){backend.kill('SIGTERM');vite?.kill('SIGTERM');}
process.on('SIGINT',()=>{stop();process.exit(0);});process.on('SIGTERM',()=>{stop();process.exit(0);});
backend.on('error',e=>{console.error(e);process.exit(1);});
backend.on('exit',code=>{if(code){vite?.kill();process.exit(code);}});
let ready=false;
for(let i=0;i<100;i++){try{const r=await fetch('http://127.0.0.1:8001/api/health');if(r.ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,150));}
if(!ready){console.error('Scientific backend did not start. Install requirements.txt.');stop();process.exit(1);}
vite=spawn(process.execPath,['node_modules/vite/bin/vite.js',...process.argv.slice(2)],{cwd:root,stdio:'inherit'});
vite.on('exit',code=>{backend.kill();process.exit(code||0);});
