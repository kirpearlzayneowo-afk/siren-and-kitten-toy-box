const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'panel.html'),'utf8');
const code=html.split('// BESIDE-POLLING-BEGIN:')[1].split('\n').slice(1).join('\n').split('// BESIDE-POLLING-END')[0];
(async()=>{
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  const timers=new Map(),pending=[];
  let listener,calls=0,id=0;
  const document={hidden:false,addEventListener:(_,fn)=>listener=fn};
  const context={document,stopped:false,refreshVersion:0,
    refresh:()=>{calls++;return new Promise(resolve=>pending.push(resolve));},
    setTimeout:(fn,ms)=>{assert.equal(ms,5000);timers.set(++id,fn);return id;},
    clearTimeout:key=>timers.delete(key)};
  vm.runInNewContext(code,context);
  assert.equal(calls,1);
  // Hide and return while the previous request is still pending.
  document.hidden=true;listener();
  document.hidden=false;listener();
  assert.equal(calls,2);
  pending.shift()();await flush();
  assert.equal(timers.size,0,'old request must not schedule a second loop');
  pending.shift()();await flush();
  assert.equal(timers.size,1);
  document.hidden=true;listener();
  assert.equal(timers.size,0,'hidden panel has no refresh timer');
  document.hidden=false;listener();
  assert.equal(calls,3,'returning refreshes immediately');
  context.stopped=true;
  pending.shift()();await flush();
  assert.equal(timers.size,0,'stopped collector leaves no polling loop');
  console.log('Polling tests passed: hide, return, in-flight race and stop.');
})().catch(error=>{console.error(error);process.exitCode=1;});
