// Test only the decorative copy module, without running the app or a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, 'panel.html'), 'utf8');
const code = html.split('// BESIDE-BANTER-BEGIN')[1].split('// BESIDE-BANTER-END')[0].split('\n').slice(1).join('\n');
const classes = new Set();
const click = {};
const line = {textContent:'塞壬开嗓中…'};
const button = {classList:{add:x=>classes.add(x),remove:x=>classes.delete(x)},addEventListener:(name,fn)=>{click[name]=fn;}};
let tick,swap,visibility,intervalMs,clears=0;
const document = {hidden:false,getElementById:id=>id==='intro'?button:line,addEventListener:(name,fn)=>{visibility=fn;}};
vm.runInNewContext(code,{document,setTimeout:fn=>{swap=fn;return 1;},clearTimeout:()=>{swap=null;},setInterval:(fn,ms)=>{tick=fn;intervalMs=ms;return 2;},clearInterval:()=>{clears++;}});
assert.equal(intervalMs,8000);
tick(); assert.ok(classes.has('changing')); swap();
assert.equal(line.textContent,'抛光鳞片中…');
click.click();swap();assert.equal(line.textContent,'沈砚在 coding…');
document.hidden=true;visibility();assert.equal(swap,null);assert.ok(clears>0);
const old=line.textContent;tick();assert.equal(line.textContent,old);
document.hidden=false;visibility();
for(let i=0;i<10;i++){tick();swap();}
assert.equal(line.textContent,'塞壬开嗓中…');
assert.ok(!classes.has('changing'));
console.log('Banter: rotation, click, wraparound, and hidden-page pause passed.');
