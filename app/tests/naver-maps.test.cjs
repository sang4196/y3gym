const {test}=require('node:test');
const assert=require('node:assert/strict');
const maps=require('../assets/naver-maps.js');
const {mount}=require('../assets/branch-address.js');
const query='TEST 도로 10';
const payload=(q=query, rows=1)=>({v2:{status:'OK',meta:{totalCount:rows,count:rows,page:1},addresses:Array.from({length:rows},()=>({roadAddress:q,jibunAddress:'',x:'127.1',y:'37.2'}))}});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function node(value='') {
  const handlers={};
  return {value,dataset:{},hidden:true,isConnected:true,disabled:false,textContent:'',
    addEventListener(k,cb){(handlers[k]??=[]).push(cb);},
    emit(k,event={}){return (handlers[k]||[]).map(cb=>cb(event));},
    replaceChildren(){this.cleared=true;}};
}
function setup() {
  const s={scripts:[],requests:[],maps:[],markers:[],timers:new Map(),destroyed:0,removed:0};
  const win=node(),canvas=node();let timer=0;
  const sdk={Service:{Status:{OK:'OK'},geocode(opts,cb){s.requests.push({opts,cb});}},
    LatLng:class{constructor(lat,lng){this.lat=lat;this.lng=lng;}},
    Map:class{constructor(el,opts){s.maps.push({el,opts});}destroy(){s.destroyed++;}},
    Marker:class{constructor(opts){s.markers.push(opts);}setMap(map){assert.equal(map,null);s.removed++;}}};
  win.document={head:{appendChild(script){s.scripts.push(script);}},createElement(){return {remove(){}};}};
  win.setTimeout=(cb,ms)=>{s.timers.set(++timer,{cb,ms});return timer;};win.clearTimeout=id=>s.timers.delete(id);
  // Fail immediately if application code attempts client storage or server submission.
  for (const k of ['localStorage','sessionStorage','indexedDB','fetch','XMLHttpRequest','navigator']) Object.defineProperty(win,k,{get(){throw Error('forbidden '+k);}});
  const states=[], c=maps.createMap(win,canvas,(...v)=>states.push(v));
  const ready=()=>{win.naver={maps:sdk};win.__y3gymNaverReady();};
  const reply=(n=0,data=payload(),status='OK')=>s.requests[n].cb(status,data);
  return {s,win,canvas,sdk,c,states,ready,reply};
}
test('disabled key/invalid input/disconnected means zero SDK and geocode requests',async()=>{
 const e=setup();
 for (const [q,key] of [[query,''],['','TEST'],[query,'bad\n'],[query,'bad&secret'],['x'.repeat(256),'TEST']]) assert.equal(await e.c.show(q,key),'disabled');
 e.canvas.isConnected=false;assert.equal(await e.c.show(query,'TEST'),'disabled');assert.equal(e.s.scripts.length,0);
});
test('official geocoder single matching result used immediately once; only own query notification',async()=>{
 const e=setup(),p=e.c.show(query,'TEST');e.ready();await tick();
 assert.equal(e.s.scripts[0].src,'https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=TEST&submodules=geocoder&callback=__y3gymNaverReady');
 assert.deepEqual(e.s.requests[0].opts,{query});e.reply();assert.equal(await p,'shown');
 assert.deepEqual({...e.s.maps[0].opts.center},{lat:37.2,lng:127.1}); assert.deepEqual(Object.keys(e.s.maps[0].opts),['center','zoom']); assert.equal(e.s.maps[0].opts.zoom,16);
 assert.deepEqual(e.states.at(-1),['shown',query]);assert.equal(e.s.timers.size,0);
 e.reply();assert.equal(e.s.maps.length,1);
});
test('strict normalized full address match; no prefix alias or first candidate',()=>{
 assert.ok(maps.pointFor('TEST  도로 10',payload()));
 for (const data of [payload(query,0),payload(query,2),payload('TEST 도로 100'),payload('TEST 도로 10 건물'),payload('TEST 다른주소')]) assert.equal(maps.pointFor(query,data),null);
 for (const value of ['NaN','Infinity','181','',true,null,'1e2','127\n']) {const p=payload();p.v2.addresses[0].x=value;assert.equal(maps.pointFor(query,p),null);}
 const truncated=payload();truncated.v2.meta.totalCount=2;assert.equal(maps.pointFor(query,truncated),null);
 const missingMeta=payload();delete missingMeta.v2.meta;assert.equal(maps.pointFor(query,missingMeta),null);
});
test('multiple or invalid/error/quota responses never render a marker',async()=>{
 for (const [data,status] of [[payload(query,2),'OK'],[payload('OTHER'),'OK'],[payload(),'ERROR'],[null,'429'],[{},'OK']]) {
  const e=setup(),p=e.c.show(query,'TEST');e.ready();await tick();e.reply(0,data,status);assert.equal(await p,'unavailable');assert.equal(e.s.maps.length,0);
 }
});
test('one loader across branches, in-flight duplicate suppressed, each branch fresh geocode',async()=>{
 const e=setup(),other=maps.createMap(e.win,node());const p=e.c.show(query,'TEST');
 assert.equal(await e.c.show(query,'TEST'),'busy');const p2=other.show('OTHER 1','TEST');e.ready();await tick();
 assert.equal(e.s.scripts.length,1);assert.equal(e.s.requests.length,2);e.reply();e.reply(1,payload('OTHER 1'));assert.equal(await p,'shown');assert.equal(await p2,'shown');
});
test('address invalidation and reversed callbacks cannot restore old map',async()=>{
 const e=setup(),old=e.c.show(query,'TEST');e.ready();await tick();e.c.reset();const fresh=e.c.show('NEW 1','TEST');await tick();
 e.reply(1,payload('NEW 1'));e.reply();assert.equal(await old,'stale');assert.equal(await fresh,'shown');assert.equal(e.s.maps.length,1);
});
for (const reason of ['network','auth','timeout']) test('SDK '+reason+' fails closed with late callback inert',async()=>{
 const e=setup(),p=e.c.show(query,'TEST'),late=e.win.__y3gymNaverReady;
 if(reason==='network')e.s.scripts[0].onerror();if(reason==='auth')e.win.navermap_authFailure();
 if(reason==='timeout')for(const t of [...e.s.timers.values()])t.cb();
 assert.equal(await p,'unavailable');e.win.naver={maps:e.sdk};late();await tick();assert.equal(e.s.requests.length,0);assert.equal(e.s.maps.length,0);
});
test('geocode timeout ignores late response and explicit retry makes new request',async()=>{
 const e=setup(),p=e.c.show(query,'TEST');e.ready();await tick();for(const t of [...e.s.timers.values()])t.cb();assert.equal(await p,'unavailable');e.reply();
 const next=e.c.show(query,'TEST');await tick();e.reply(1);assert.equal(await next,'shown');assert.equal(e.s.requests.length,2);assert.equal(e.s.maps.length,1);
});
test('late authentication failure clears displayed map',async()=>{
 const e=setup(),p=e.c.show(query,'TEST');e.ready();await tick();e.reply();await p;e.win.navermap_authFailure();
 assert.equal(e.canvas.hidden,true);assert.equal(e.s.destroyed,1);assert.equal(await e.c.show(query,'TEST'),'unavailable');
});
test('pagehide cancels pending, bfcache resume never reuses old result',async()=>{
 const e=setup(),p=e.c.show(query,'TEST');e.ready();await tick();e.c.suspend();e.reply();assert.equal(await p,'stale');
 assert.equal(await e.c.show(query,'TEST'),'disabled');e.c.resume();assert.equal(e.s.requests.length,1);
 const next=e.c.show(query,'TEST');await tick();e.reply(1);assert.equal(await next,'shown');assert.equal(e.s.requests.length,2);
 e.c.suspend();assert.equal(e.s.destroyed,1);assert.equal(e.s.removed,1);
});
test('public mount waits for click; pagehide/pageshow reset without automatic query',async()=>{
 const e=setup(),button=node(),status=node(),area={querySelector:s=>s==='[data-map-open]'?button:status};
 e.win.document.querySelector=()=>area;e.win.document.getElementById=()=>e.canvas;
 maps.mountPublic(e.win,{keyId:'TEST',items:[{id:'1',query}]});assert.equal(e.s.scripts.length,0);
 button.emit('click');e.ready();await tick();e.reply();assert.equal(button.disabled,true);
 e.win.emit('pagehide');e.win.emit('pageshow',{persisted:true});assert.equal(button.disabled,false);assert.equal(e.s.requests.length,1);assert.equal(e.canvas.hidden,true);
 button.emit('click');await tick();e.reply(1);assert.equal(e.s.requests.length,2);assert.equal(e.s.scripts.length,1);
});
function admin(key='TEST') {
 const e=setup(),fields={address:node(query),edit_version:node('3'),map_confirmation:node(),map_confirmation_address:node(),map_confirmation_version:node()};
 const form=node();form.elements={namedItem:k=>fields[k]};
 const ui=Object.fromEntries(['map-open','map-confirm','map-status','saved-map-status'].map(k=>[k,node()]));ui['map-canvas']=e.canvas;
 const area={dataset:{mapKey:key},closest:()=>form,querySelector:s=>ui[s.slice(6,-1)]};
 mount(e.win,area,maps);return {...e,fields,form,ui};
}
test('admin confirmation emits own address/version/intent only after current match; input clears all',async()=>{
 const e=admin();assert.equal(e.ui['map-confirm'].disabled,true);assert.equal(e.s.scripts.length,0);
 const [pending]=e.ui['map-open'].emit('click');e.ready();await tick();e.reply();await pending;
 assert.equal(e.ui['map-confirm'].disabled,false);e.ui['map-confirm'].emit('click');
 assert.deepEqual(['map_confirmation','map_confirmation_address','map_confirmation_version'].map(k=>e.fields[k].value),['true',query,'3']);
 e.fields.address.value='NEW 1';e.fields.address.emit('input');assert.equal(e.fields.map_confirmation.value,'');assert.equal(e.canvas.hidden,true);
});
test('admin no key, changed version or response after address change cannot confirm',async()=>{
 const disabled=admin('');disabled.ui['map-open'].emit('click');assert.equal(disabled.s.scripts.length,0);
 for(const kind of ['version','address']){
  const e=admin(),[p]=e.ui['map-open'].emit('click');e.ready();await tick();
  if(kind==='version')e.fields.edit_version.value='4';else{e.fields.address.value='NEW';e.fields.address.emit('input');}
  e.reply();await p;assert.equal(e.ui['map-confirm'].disabled,true);assert.equal(e.fields.map_confirmation.value,'');
 }
});
test('admin pagehide clears confirmed intent and bfcache needs fresh lookup',async()=>{
 const e=admin(),[p]=e.ui['map-open'].emit('click');e.ready();await tick();e.reply();await p;e.ui['map-confirm'].emit('click');
 e.win.emit('pagehide');e.win.emit('pageshow',{persisted:true});assert.equal(e.fields.map_confirmation.value,'');assert.equal(e.ui['map-confirm'].disabled,true);assert.equal(e.s.requests.length,1);
});
test('marker constructor failure destroys partially created map',async()=>{
 const e=setup();e.sdk.Marker=class{constructor(){throw Error('TEST');}};
 const p=e.c.show(query,'TEST');e.ready();await tick();e.reply();assert.equal(await p,'unavailable');assert.equal(e.s.destroyed,1);assert.equal(e.canvas.hidden,true);
});
test('admin input changed back still invalidates old callback and submit tamper clears intent',async()=>{
 const e=admin(),[p]=e.ui['map-open'].emit('click');e.ready();await tick();
 e.fields.address.value='NEW';e.fields.address.emit('input');e.fields.address.value=query;e.fields.address.emit('input');e.reply();await p;
 assert.equal(e.ui['map-confirm'].disabled,true);assert.equal(e.s.maps.length,0);
 const [next]=e.ui['map-open'].emit('click');await tick();e.reply(1);await next;e.ui['map-confirm'].emit('click');
 e.fields.address.value='NEW';e.form.emit('submit');assert.equal(e.fields.map_confirmation.value,'');
});
