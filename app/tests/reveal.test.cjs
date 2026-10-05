const {test}=require('node:test');
const assert=require('node:assert/strict');
const {start}=require('../assets/reveal.js');
function eventTarget() {
 const events=new Map();
 return {addEventListener(k,fn){if(!events.has(k))events.set(k,new Set());events.get(k).add(fn);},removeEventListener(k,fn){events.get(k)?.delete(fn);},emit(k,e={}){for(const fn of [...(events.get(k)||[])])fn(e);}};
}
function element(top=1200,extra={}) {
 const attrs={},styles={};
 const el={...eventTarget(),top,parentElement:null,children:[],attrs,styles,
  style:{setProperty(k,v){styles[k]=v;},removeProperty(k){delete styles[k];}},
  setAttribute(k,v){attrs[k]=v;},removeAttribute(k){delete attrs[k];},
  getBoundingClientRect(){return {top:this.top,bottom:this.top+100,height:100};},
  contains(other){return other===this || this.children.some(c=>c.contains(other));},
  closest(selector){if(selector==='[data-reveal]')return this.marked?this:this.parentElement?.closest(selector);if(selector==='a[href]')return this.href?this:this.parentElement?.closest(selector);return this.excluded?this:this.parentElement?.closest(selector);},
  querySelector(){return this.children.find(c=>c.excluded)||null;},...extra};
 Object.defineProperty(el,'innerHTML',{set(){throw Error('must not rewrite content');}});
 return el;
}
function setup(options={}) {
 const win=eventTarget(), root=element(), body=element(), parent=element();
 const nodes=options.nodes||[element(-100),element(100),element(800),element(1300)];nodes.forEach(n=>{n.marked=true;n.parentElement??=parent;});parent.children=nodes;
 const reduced={...eventTarget(),matches:!!options.reduced},printing={...eventTarget(),matches:false};
 const doc={...eventTarget(),documentElement:root,body,activeElement:body,hidden:false,querySelectorAll(){return nodes;},getElementById(id){return nodes.find(n=>n.id===id)||null;}};
 win.document=doc;win.innerHeight=800;win.location={href:'http://test.local/branches/'+(options.hash||''),hash:options.hash||''};
 win.matchMedia=q=>q==='print'?printing:reduced;
 const observers=[],intervals=new Map();let id=0,clock=0;
 win.performance={now:()=>clock};
 win.setInterval=(fn,ms)=>{if(options.timerError)throw Error('timer failure');intervals.set(++id,{fn,ms});return id;};win.clearInterval=id=>intervals.delete(id);
 win.IntersectionObserver=class {
  constructor(cb){if(options.constructorError)throw Error('observer unavailable');this.cb=cb;this.observed=new Set();observers.push(this);}
  observe(el){if(options.observeError && this.observed.size===1)throw Error('registration failure');this.observed.add(el);}
  unobserve(el){if(options.unobserveError)throw Error('callback failure');this.observed.delete(el);}
  disconnect(){this.disconnected=true;this.observed.clear();}
 };
 if(options.noAPI)delete win.IntersectionObserver;
 if(options.noMedia)delete win.matchMedia;
 for(const name of ['fetch','XMLHttpRequest','scrollTo','scrollBy','localStorage','sessionStorage'])Object.defineProperty(win,name,{get(){throw Error('forbidden '+name);}});
 const fire=(el,intersecting=true)=>observers[0].cb([{target:el,isIntersecting:intersecting,boundingClientRect:el.getBoundingClientRect()}]);
 const boot=()=>start(win);
 const allVisible=()=>nodes.every(n=>n.attrs['data-reveal-state']!=='waiting');
 return {win,doc,root,nodes,parent,reduced,printing,observers,intervals,fire,boot,allVisible,advance(ms){clock+=ms;}};
}
test('SSR default visible; first viewport and already passed content never hidden',()=>{
 const e=setup();assert.ok(e.allVisible());e.boot();assert.equal(e.nodes[0].attrs['data-reveal-state'],undefined);assert.equal(e.nodes[1].attrs['data-reveal-state'],undefined);
 assert.equal(e.nodes[2].attrs['data-reveal-state'],'waiting');assert.equal(e.observers[0].observed.size,2);
});
test('enter once, unobserve, bounded group delay; repeated initialization is inert',()=>{
 const e=setup({nodes:Array.from({length:6},(_,i)=>element(900+i*100))});e.boot();
 assert.deepEqual(e.nodes.map(n=>n.styles['--reveal-delay']),['0ms','70ms','140ms','210ms','210ms','210ms']);
 e.fire(e.nodes[0]);assert.equal(e.nodes[0].attrs['data-reveal-state'],'entering');assert.equal(e.observers[0].observed.has(e.nodes[0]),false);
 e.fire(e.nodes[0],false);assert.equal(e.nodes[0].attrs['data-reveal-state'],'entering');e.boot();assert.equal(e.observers.length,1);
 e.nodes.slice(1).forEach(n=>e.fire(n));assert.equal(e.intervals.size,0);assert.equal(e.observers[0].disconnected,true);
});
test('missing API/media and reduced motion startup stay fully visible',()=>{
 for(const opts of [{noAPI:true},{noMedia:true},{reduced:true},{constructorError:true},{observeError:true},{timerError:true}]){
  const e=setup(opts);assert.doesNotThrow(e.boot);assert.ok(e.allVisible());assert.equal(e.intervals.size,0);
 }
});
test('observer callback errors restore every armed node',()=>{
 const e=setup({unobserveError:true});e.boot();e.fire(e.nodes[2]);assert.ok(e.allVisible());assert.equal(e.intervals.size,0);
});
test('observer callback loss recovered by viewport watchdog without scroll manipulation',()=>{
 const e=setup();e.boot();e.nodes[2].top=100;e.nodes[3].top=-200;
 const sweep=[...e.intervals.values()][0].fn;sweep();assert.equal(e.nodes[2].attrs['data-reveal-state'],'waiting');assert.equal(e.nodes[3].attrs['data-reveal-state'],undefined);
 e.advance(500);sweep();assert.ok(e.allVisible());assert.equal(e.intervals.size,0);
});
test('reduced motion changes while active restore content permanently',()=>{
 const e=setup();e.boot();e.reduced.emit('change',{matches:true});assert.ok(e.allVisible());
 e.reduced.emit('change',{matches:false});e.boot();assert.ok(e.allVisible());assert.equal(e.observers.length,1);
});
test('focus in a target or a focused ancestor reveals all related content immediately',()=>{
 const e=setup();const link=element();e.nodes[2].children=[link];link.parentElement=e.nodes[2];e.boot();e.doc.emit('focusin',{target:link});
 assert.equal(e.nodes[2].attrs['data-reveal-state'],undefined);assert.equal(e.nodes[2].styles['--reveal-delay'],undefined);
 e.doc.emit('focusin',{target:e.parent});assert.ok(e.allVisible());
});
test('existing focused container is respected during initialization',()=>{
 const e=setup();e.doc.activeElement=e.parent;e.boot();assert.ok(e.allVisible());
});
test('initial hash, hashchange, and same-page anchor click expose their targets before navigation',()=>{
 const e=setup({hash:'#target'});e.nodes[2].id='target';e.nodes[3].id='next';e.boot();assert.equal(e.nodes[2].attrs['data-reveal-state'],undefined);
 e.win.location.hash='#next';e.win.emit('hashchange');assert.ok(e.allVisible());
 const f=setup();f.nodes[2].id='anchor';f.boot();const a=element(0,{href:'http://test.local/branches/#anchor'});f.doc.emit('click',{target:a});assert.equal(f.nodes[2].attrs['data-reveal-state'],undefined);
});
test('malformed hash fails visible instead of blocking content',()=>{
 const e=setup({hash:'#%ZZ'});e.boot();assert.ok(e.allVisible());assert.equal(e.intervals.size,0);
});
test('print, pagehide/bfcache, and hidden document restore all content',()=>{
 for(const which of ['print','pagehide','pageshow','visibility']){
  const e=setup();e.boot();
  if(which==='print')e.win.emit('beforeprint');
  if(which==='pagehide'){e.win.emit('pagehide');e.win.emit('pageshow',{persisted:true});}
  if(which==='pageshow')e.win.emit('pageshow',{persisted:true});
  if(which==='visibility'){e.doc.hidden=true;e.doc.emit('visibilitychange');}
  assert.ok(e.allVisible());assert.equal(e.intervals.size,0);e.boot();assert.ok(e.allVisible());
 }
});
test('print media change and missing change API also fall back',()=>{
 const e=setup();e.boot();e.printing.emit('change',{matches:true});assert.ok(e.allVisible());
 const f=setup();delete f.reduced.addEventListener;f.boot();assert.ok(f.allVisible());
});
test('excluded UI, parents containing map/popup, nested targets and zero-size content never arm',()=>{
 const excluded=element(1000,{excluded:true}),wrapper=element(),nested=element(),zero=element(1200,{getBoundingClientRect(){return {top:1200,height:0};}}),container=element();
 nested.parentElement=wrapper;wrapper.children=[nested];container.children=[element(1200,{excluded:true})];
 const e=setup({nodes:[excluded,wrapper,nested,zero,container]});e.boot();
 assert.equal(wrapper.attrs['data-reveal-state'],'waiting');for(const n of [excluded,nested,zero,container])assert.equal(n.attrs['data-reveal-state'],undefined);
});
test('geometry or resize failure never leaves waiting state',()=>{
 const e=setup();e.boot();e.nodes[2].getBoundingClientRect=()=>{throw Error('layout unavailable');};e.win.emit('resize');assert.ok(e.allVisible());
});

test('focus and hash cancel a running or delayed transition, not just waiting state',()=>{
 for(const method of ['focus','hash','ancestor']){
  const e=setup();const target=e.nodes[3];target.id='entering';const link=element();target.children=[link];link.parentElement=target;
  e.boot();e.fire(target);assert.equal(target.attrs['data-reveal-state'],'entering');
  if(method==='focus')e.doc.emit('focusin',{target:link});
  if(method==='hash'){e.win.location.hash='#entering';e.win.emit('hashchange');}
  if(method==='ancestor')e.doc.emit('focusin',{target:e.parent});
  assert.equal(target.attrs['data-reveal-state'],undefined);assert.equal(target.styles['--reveal-delay'],undefined);
 }
});
test('watchdog grace allows normal observer to animate after the first visible poll',()=>{
 const e=setup();e.boot();e.nodes[2].top=100;const sweep=[...e.intervals.values()][0].fn;
 sweep();e.advance(250);sweep();assert.equal(e.nodes[2].attrs['data-reveal-state'],'waiting');
 e.fire(e.nodes[2]);assert.equal(e.nodes[2].attrs['data-reveal-state'],'entering');e.advance(1000);sweep();assert.equal(e.nodes[2].attrs['data-reveal-state'],'entering');
});
