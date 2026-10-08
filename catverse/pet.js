/* CATVERSE 小祈罐罐存档：仅本地，不联网。加载后使用 window.CatversePet。 */
(function(global){
"use strict";
const KEY="siren-catverse-qi-v1";
const TYPES=["star","hawthorn","moon"];
const SNACKS=["lollipop","icepop","tanghulu","fishcan","brush","scale","latiao"];
const NAMES={star:"⭐ 星星鱼泥",hawthorn:"🍒 山楂果冻",moon:"🌙 月光小鱼干"};
const VALID=/^[a-zA-Z0-9_-]{8,96}$/;
const MAX=9999,MAX_IDS=1200;
function safe(v,max=MAX){return Number.isSafeInteger(v)&&v>=0&&v<=max?v:0;}
function fresh(){return {version:2,cans:{star:0,hawthorn:0,moon:0},processed:[],fed:0,bond:0,lastKind:"",snackCounts:{lollipop:0,icepop:0,tanghulu:0,fishcan:0,brush:0,scale:0,latiao:0},scales:0,tongue:"",pawsDirty:false,wish:""};}
function clean(raw){
const p=fresh();if(!raw||typeof raw!=="object"||Array.isArray(raw))return p;
for(const type of TYPES)p.cans[type]=safe(raw.cans?.[type]);
p.processed=Array.isArray(raw.processed)?[...new Set(raw.processed.filter(x=>typeof x==="string"&&VALID.test(x)))].slice(-MAX_IDS):[];
p.fed=safe(raw.fed);p.bond=safe(raw.bond);
p.lastKind=TYPES.includes(raw.lastKind)?raw.lastKind:"";
for(const type of SNACKS)p.snackCounts[type]=safe(raw.snackCounts?.[type]);
p.scales=safe(raw.scales,999);p.tongue=raw.tongue==="rainbow"?"rainbow":"";
p.pawsDirty=raw.pawsDirty===true;p.wish=typeof raw.wish==="string"?raw.wish.slice(0,120):"";
return p;
}
function load(){try{return clean(JSON.parse(localStorage.getItem(KEY)||"null"))}catch(e){return fresh()}}
function store(p){try{localStorage.setItem(KEY,JSON.stringify(clean(p)));return true}catch(e){return false}}
function total(p){return TYPES.reduce((sum,t)=>sum+p.cans[t],0)}
function choose(id){let n=0;for(let i=0;i<id.length;i++)n=(Math.imul(n,31)+id.charCodeAt(i))>>>0;return TYPES[n%TYPES.length]}
function newRoundId(){
let rand="";
try{const bytes=new Uint32Array(2);crypto.getRandomValues(bytes);rand=Array.from(bytes,x=>x.toString(36)).join("-");}
catch(e){rand=Math.random().toString(36).slice(2)+Math.random().toString(36).slice(2);}
return "round-"+Date.now().toString(36)+"-"+rand;
}
function grant(id){
if(typeof id!=="string"||!VALID.test(id))return {ok:false,error:"invalid-id"};
const p=load();
if(p.processed.includes(id))return {ok:true,awarded:false,kind:null,state:p};
if(total(p)>=MAX)return {ok:false,error:"inventory-full"};
const kind=choose(id);p.cans[kind]++;p.processed.push(id);p.processed=p.processed.slice(-MAX_IDS);
if(!store(p))return {ok:false,error:"storage-failed"};
return {ok:true,awarded:true,kind,state:p};
}
function feed(kind){
const p=load();if(!TYPES.includes(kind)||!p.cans[kind])return {ok:false,error:"no-can"};
p.cans[kind]--;p.fed=Math.min(MAX,p.fed+1);p.bond=Math.min(MAX,p.bond+1);p.lastKind=kind;
if(!store(p))return {ok:false,error:"storage-failed"};
return {ok:true,kind,state:p};
}
function snack(kind){
if(!SNACKS.includes(kind))return {ok:false,error:"invalid-snack"};
const p=load();if(total(p)<1)return {ok:false,error:"no-cans"};
if(kind==="scale"&&p.scales>=999)return {ok:false,error:"scale-complete"};
const cost=TYPES.find(t=>p.cans[t]>0);if(!cost)return {ok:false,error:"no-cans"};
p.cans[cost]--;p.snackCounts[kind]=Math.min(MAX,p.snackCounts[kind]+1);
if(kind==="scale")p.scales=Math.min(999,p.scales+1);
else{p.fed=Math.min(MAX,p.fed+1);p.bond=Math.min(MAX,p.bond+1);}
if(kind==="lollipop")p.tongue="rainbow";
if(kind==="latiao")p.pawsDirty=true;
if(kind==="icepop")p.tongue="";
if(!store(p))return {ok:false,error:"storage-failed"};
return {ok:true,kind,cost,state:p};
}
function wash(){const p=load();if(!p.pawsDirty)return {ok:true,washed:false,state:p};p.pawsDirty=false;if(!store(p))return {ok:false,error:"storage-failed"};return {ok:true,washed:true,state:p};}
function makeWish(value){const p=load();if(p.scales<999)return {ok:false,error:"not-enough-scales"};if(typeof value!=="string"||!value.trim()||value.length>120)return {ok:false,error:"invalid-wish"};p.wish=value.trim();if(!store(p))return {ok:false,error:"storage-failed"};return {ok:true,state:p};}
global.CatversePet={KEY,TYPES,NAMES,SNACKS,clean,load,store,grant,feed,snack,wash,makeWish,total,newRoundId};
})(window);
