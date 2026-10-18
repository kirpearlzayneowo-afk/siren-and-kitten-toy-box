// Dependency-free regression checks: node test-toys.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function boot(file, saved = null) {
  const nodes = new Map(), storage = new Map(), intervals = new Set();
  let now = 0;
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, {
      textContent: '', innerHTML: '', style: {}, dataset: {}, attributes: {}, handlers: {},
      classList: {add() {}, remove() {}, toggle() {}},
      setAttribute(k,v) { this.attributes[k] = v; },
      addEventListener(k,fn) { this.handlers[k] = fn; },
      querySelector(s) { return node(id+s); }, appendChild() {}, focus() {},
    });
    return nodes.get(id);
  }
  const areas = [0,1,2,3].map(i=>node('area'+i));
  const document = {getElementById: node, querySelector: node,
    querySelectorAll: s=>s==='.area'?areas:[], addEventListener() {}, createElement: ()=>node('new')};
  const context = {document, window: {}, navigator: {}, performance: {now: ()=>now},
    setInterval: fn=>(intervals.add(fn),fn), clearInterval: fn=>intervals.delete(fn),
    localStorage: {getItem: k=>storage.has(k)?storage.get(k):saved, setItem: (k,v)=>storage.set(k,v)}};
  const html = fs.readFileSync(path.join(__dirname,file),'utf8');
  vm.runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
  return {node, areas, storage,
    click(id, dataset) { const b={dataset,hasAttribute:k=>Object.hasOwn(dataset,k),closest:()=>b};
      node(id).handlers.click(dataset?{target:b}:{}); },
    advance(ms) { now+=ms; for(const fn of [...intervals]) fn(); }};
}
// Old saves keep progress; malformed fields cannot become HTML or array indices.
for (const saved of [null, '{bad', JSON.stringify({style:'constructor',outfit:1.5,draws:'<img>',charges:['hug','hug','oops']})]) {
  const app=boot('catverse/index.html',saved);
  app.click('.nav',{tab:'closet'});
  assert.match(app.node('content').innerHTML,/暮色茶会/);
  app.click('content',{move:'-1'});
  assert.match(app.node('content').innerHTML,/月光标本/);
  app.click('.nav',{tab:'gacha'});
  assert.doesNotMatch(app.node('content').innerHTML,/<img>/);
}
const art=boot('catverse/index.html',JSON.stringify({xp:75,style:'hanfu',outfit:1,draws:9,charges:['hug']}));
assert.match(art.node('content').innerHTML,/75 XP/);
art.click('.nav',{tab:'closet'});
assert.match(art.node('content').innerHTML,/雪夜观灯/);
// Favorites survive reload, can be removed, and ignore unknown saved IDs.
art.click('content',{'data-favorite-look':''});
let saved=JSON.parse(art.storage.get('siren-catverse-v1'));
assert.deepEqual(saved.favorites,['hanfu:1']);
assert.equal(saved.xp,75);
const closet=boot('catverse/index.html',JSON.stringify({...saved,favorites:['hanfu:1','hanfu:1','<img>','daily:99']}));
closet.click('.nav',{tab:'closet'});
assert.match(closet.node('content').innerHTML,/心爱的小衣架 · 1/);
closet.click('content',{style:'daily'});
closet.click('content',{look:'hanfu:1'});
assert.match(closet.node('content').innerHTML,/雪夜观灯/);
closet.click('content',{'data-favorite-look':''});
assert.deepEqual(JSON.parse(closet.storage.get('siren-catverse-v1')).favorites,[]);
for(let i=0;i<30;i++){
  const before=JSON.parse(closet.storage.get('siren-catverse-v1'));
  closet.click('content',{'data-pick-look':''});
  const after=JSON.parse(closet.storage.get('siren-catverse-v1'));
  assert.notEqual(after.style+':'+after.outfit,before.style+':'+before.outfit);
  assert(['lolita','hanfu','daily'].includes(after.style));
  assert(after.outfit>=0&&after.outfit<3);
}
// Both timer modes start in area 1, pause without counting, and award once.
for (const seconds of [120,180]) {
  const app=boot('toothbrushing-planet/index.html');
  if(seconds===180) app.click('three');
  app.click('start');
  assert.equal(app.node('status').textContent,'正在清洁 · 右上');
  app.advance(seconds/4*1000);
  assert.equal(app.node('status').textContent,'正在清洁 · 左上');
  app.click('start');
  const paused=app.node('time').textContent;
  app.advance(60000);
  assert.equal(app.node('time').textContent,paused);
  app.click('start');
  app.advance(seconds*1000);
  assert.equal(app.storage.get('sirenBrushPearls'),'1');
  assert(app.areas.every(el=>el.className==='area done'));
  app.advance(seconds*1000);
  assert.equal(app.storage.get('sirenBrushPearls'),'1');
}
console.log('Toy regressions passed: save compatibility, malformed saves, wardrobe wrap, both timer modes, pause and single reward.');
