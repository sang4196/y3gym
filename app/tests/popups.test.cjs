const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createController, domUI, nextMidnight, valid, SESSION_KEY, HIDE_PREFIX} = require('../assets/popups.js');
const T = Date.parse('2026-10-05T14:59:00Z'); // KST 23:59
const iso = time => new Date(time).toISOString();
const popup = (id='1',changes={}) => ({id,title:'TEST title',message:'TEST message',image:null,starts_at:iso(T-60000),ends_at:iso(T+86400000*3),post:{id, title:'TEST post', detail_path:'/posts/'+id+'/'},...changes});
function storage() { const values=new Map();return {values,getItem:key=>values.get(key)||null,setItem:(key,value)=>values.set(key,value)}; }
function setup(items=[popup()], shared) {
  const stores=shared || {sessionStorage:storage(),localStorage:storage()};
  const state={tick:0,server:T,items,calls:0,renders:[],hides:0,visible:true};
  const env={origin:'https://test.example',AbortController,clock:()=>state.tick,visible:()=>state.visible,storage:name=>stores[name],
    fetch:async (url,options)=>{assert.equal(url,'/api/v1/popups/active/');assert.equal(options.cache,'no-store');assert.equal(options.credentials,'omit');state.calls++;return response({items:state.items,meta:{server_time:iso(state.server)}});},
    render:(item,close,today)=>{state.renders.push(item);state.close=close;state.today=today;return true;},hide:()=>state.hides++};
  return {env,state,stores,controller:createController(env)};
}
const response = payload => ({ok:true,status:200,headers:{get:()=> 'application/json'},json:async()=>payload});

for (const [field,limit] of [['title',200],['message',1000],['image.alt',200]]) {
  test(field+' uses server code-point limits and does not suppress valid candidates',async()=>{
    const candidate = value => popup('2',field==='image.alt'
      ? {image:{url:'https://test.example/images/display/1/',alt:value,width:64,height:48}}
      : {[field]:value});
    for (const [profile,value] of [
      ['BMP','가'.repeat(limit)],
      ['mixed','가'.repeat(limit-1)+'😀'],
      ['non-BMP','😀'.repeat(limit)],
    ]) {
      const item=candidate(value);
      assert.equal(valid(item,'https://test.example'),true,profile+' boundary accepted');
      // Validate the full response even when this candidate is not selected.
      for (const items of [[item,popup()],[popup(),item]]) {
        const e=setup(items);
        assert.equal(await e.controller.load(),'shown',profile+' response accepted');
        assert.deepEqual(e.state.renders,[items[0]]);
      }
      for (const extra of ['가','😀']) {
        const oversized=candidate(value+extra);
        assert.equal(valid(oversized,'https://test.example'),false,profile+' over limit rejected');
        const e=setup([popup(),oversized]);
        assert.equal(await e.controller.load(),'invalid');
        assert.equal(e.state.renders.length,0);
        assert.equal(e.stores.sessionStorage.getItem(SESSION_KEY),null);
      }
    }
  });
}

test('server order, hide by ID, one successful display per tab and no chaining on close',async()=>{
  const e=setup([popup('2'),popup('1')]);e.stores.localStorage.setItem(HIDE_PREFIX+'2',String(nextMidnight(T)));
  assert.equal(await e.controller.load(),'shown');assert.equal(e.state.renders[0].id,'1');
  assert.equal(e.stores.sessionStorage.getItem(SESSION_KEY),'1');e.state.close();
  assert.equal(await e.controller.load(),'skipped');assert.equal(e.state.calls,1);assert.equal(e.state.renders.length,1);
  const nextPage=setup([popup()],e.stores);assert.equal(await nextPage.controller.load(),'skipped');assert.equal(nextPage.state.calls,0);
  const newTab=setup([popup()],{sessionStorage:storage(),localStorage:e.stores.localStorage});assert.equal(await newTab.controller.load(),'shown');
});
test('all hidden and empty responses do not consume automatic display',async()=>{
  const e=setup();e.stores.localStorage.setItem(HIDE_PREFIX+'1',String(nextMidnight(T)));
  assert.equal(await e.controller.load(),'hidden');assert.equal(e.stores.sessionStorage.getItem(SESSION_KEY),null);
  e.state.items=[];assert.equal(await e.controller.load(),'empty');
  e.state.items=[popup('2')];assert.equal(await e.controller.load(),'shown');
});
test('today is popup-ID based until exactly next Korean midnight, unaffected by message edits',async()=>{
  const e=setup();assert.equal(await e.controller.load(),'shown');e.state.today();
  const midnight=Date.parse('2026-10-05T15:00:00Z');assert.equal(Number(e.stores.localStorage.getItem(HIDE_PREFIX+'1')),midnight);
  const next=setup([popup('1',{message:'TEST changed'})],{sessionStorage:storage(),localStorage:e.stores.localStorage});
  next.state.server=midnight-1;assert.equal(await next.controller.load(),'hidden');
  next.state.server=midnight;assert.equal(await next.controller.load(),'shown');
});
test('server time and monotonic elapsed ignore a wildly wrong browser wall clock',async()=>{
  const e=setup();const original=Date.now;Date.now=()=>1;
  try {assert.equal(await e.controller.load(),'shown');e.state.tick=120000;e.state.today();}
  finally {Date.now=original;}
  assert.equal(Number(e.stores.localStorage.getItem(HIDE_PREFIX+'1')),Date.parse('2026-10-06T15:00:00Z'));
});
test('unavailable or corrupt storage never breaks display, closing or same-document memory',async()=>{
  const e=setup();e.env.storage=()=>{throw new Error('storage denied');};
  assert.equal(await e.controller.load(),'shown');e.state.today();assert.equal(e.state.hides,1);
  assert.equal(await e.controller.load(),'skipped');
  const corrupt=setup();corrupt.stores.sessionStorage.setItem(SESSION_KEY,'garbage');corrupt.stores.localStorage.setItem(HIDE_PREFIX+'1','999999999999999');
  assert.equal(await corrupt.controller.load(),'shown');
});
test('expired during network transit re-fetches once without recording a display',async()=>{
  const e=setup([popup('1',{ends_at:iso(T+100)})]);
  // First response represents a valid server decision before transit.
  e.env.fetch=async()=>{e.state.calls++;e.state.tick+=200;return response({items:e.state.calls===1?e.state.items:[],meta:{server_time:iso(e.state.calls===1?T:T+e.state.tick)}});};
  assert.equal(await e.controller.load(),'empty');assert.equal(e.state.calls,2);assert.equal(e.state.renders.length,0);assert.equal(e.stores.sessionStorage.getItem(SESSION_KEY),null);
});
test('very slow response discarded, bounded retry, no polling',async()=>{
  const e=setup();e.env.fetch=async()=>{e.state.calls++;e.state.tick+=16000;return response({items:[popup()],meta:{server_time:iso(T)}});};
  assert.equal(await e.controller.load(),'expired');assert.equal(e.state.calls,2);assert.equal(e.state.renders.length,0);
});
test('pagehide invalidates in-flight response, bfcache uses a new response',async()=>{
  const e=setup();let finish;
  e.env.fetch=()=>new Promise(resolve=>{finish=resolve;});
  const old=e.controller.load();e.controller.suspend();finish(response({items:[popup()],meta:{server_time:iso(T)}}));
  assert.equal(await old,'stale');assert.equal(e.state.renders.length,0);
  e.env.fetch=async()=>response({items:[],meta:{server_time:iso(T+1000)}});
  assert.equal(await e.controller.load(),'empty');
});
test('shown notice removed on bfcache suspension and never reuses old candidates',async()=>{
  const e=setup();assert.equal(await e.controller.load(),'shown');e.controller.suspend();
  assert.equal(await e.controller.load(),'skipped');assert.equal(e.state.hides,1);assert.equal(e.state.calls,1);
});
test('hidden tab and failed DOM insertion do not mark as displayed',async()=>{
  const e=setup();e.state.visible=false;assert.equal(await e.controller.load(),'skipped');assert.equal(e.state.calls,0);
  e.state.visible=true;e.env.render=()=>false;assert.equal(await e.controller.load(),'skipped');assert.equal(e.stores.sessionStorage.getItem(SESSION_KEY),null);
});
test('network and server failures are quiet, malformed time and unsafe DTOs fail closed',async()=>{
  const e=setup();e.env.fetch=async()=>{throw new Error('network');};assert.equal(await e.controller.load(),'error');
  e.env.fetch=async()=>({...response({}),ok:false,status:500});assert.equal(await e.controller.load(),'error');
  for (const payload of [
    {items:[],meta:{server_time:'2026-02-30T00:00:00Z'}},
    {items:[popup('1',{post:{id:'1',title:'x',detail_path:'javascript:evil'}})],meta:{server_time:iso(T)}},
    {items:[popup('1',{image:{url:'https://evil.test/photo',alt:'x',width:1,height:1}})],meta:{server_time:iso(T)}},
    {items:[popup('1',{starts_at:iso(T+1000)})],meta:{server_time:iso(T)}},
    {items:[popup('1',{ends_at:iso(T)})],meta:{server_time:iso(T)}},
  ]) {e.env.fetch=async()=>response(payload);assert.equal(await e.controller.load(),'invalid');}
  assert.equal(e.state.renders.length,0);assert.equal(e.stores.sessionStorage.getItem(SESSION_KEY),null);
});
test('DOM uses plain text, real controls, no focus theft and restores focus only from closed region',()=>{
  let focusCalls=0;
  class Element {
    constructor(tag){this.tag=tag;this.children=[];this.events={};this.isConnected=true;}
    set innerHTML(_){throw new Error('innerHTML forbidden');}
    replaceChildren(...children){this.children=children;}
    contains(node){return node===this||this.children.includes(node);}
    addEventListener(name,fn){this.events[name]=fn;}
    focus(){focusCalls++;}
  }
  const region=new Element('section'),home=new Element('h1'),body=new Element('body');
  const doc={body,hidden:false,activeElement:body,createElement:tag=>new Element(tag),querySelector:()=>home};
  const ui=domUI(doc,region);let closed=0,today=0;
  assert.equal(ui.render(popup('1',{title:'<script>TEST</script>'}),()=>closed++,()=>today++),true);
  assert.equal(focusCalls,0);assert.equal(region.hidden,false);assert.equal(region.children[0].textContent,'<script>TEST</script>');
  const buttons=region.children.filter(x=>x.tag==='button');assert.equal(buttons.length,2);assert.equal(buttons[0].type,'button');
  buttons[0].events.click();buttons[1].events.click();assert.equal(closed,1);assert.equal(today,1);
  doc.activeElement=buttons[0];ui.hide();assert.equal(focusCalls,1);assert.equal(region.hidden,true);
  ui.hide();assert.equal(focusCalls,1);
});

test('invalid monotonic time immediately before insertion fails closed',async()=>{
  const e=setup();const ticks=[0,0,0,1,-1];e.env.clock=()=>ticks.shift();
  assert.equal(await e.controller.load(),'invalid');assert.equal(e.state.renders.length,0);
});
