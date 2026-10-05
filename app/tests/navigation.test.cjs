const {test}=require('node:test');
const assert=require('node:assert/strict');
const {start}=require('../assets/navigation.js');
function events() {
 const handlers=new Map();
 return {handlers,addEventListener(k,fn){if(!handlers.has(k))handlers.set(k,new Set());handlers.get(k).add(fn);},removeEventListener(k,fn){handlers.get(k)?.delete(fn);},emit(k,e={}){for(const fn of [...(handlers.get(k)||[])])fn(e);}};
}
function setup(options={}) {
 const doc=events(),win=events();
 function el(parent=null,attrs={}) {
  return {...events(),parent,attrs,hidden:false,
   hasAttribute(k){return Object.hasOwn(this.attrs,k);},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];},
   contains(other){return !!other && (other===this || this.contains(other.parent));},
   focus(){doc.activeElement=this;doc.emit('focusin',{target:this});},
   closest(){return this.attrs.href?this:this.parent?.closest();}};
 }
 const body=el(),header=el(body),brand=el(header,{href:'/'}),toggle=el(header),panel=el(header),link=el(panel,{href:'/branches/#branch-1'}),outside=el(body,{href:'/elsewhere/'}),child=el(link);
 toggle.hidden=true;toggle.attrs['aria-expanded']='false';toggle.attrs['aria-label']='메뉴 열기';
 header.querySelector=s=>({'[data-menu-toggle]':toggle,'[data-menu-panel]':panel,'.brand':brand}[s]);
 panel.querySelector=()=>link;doc.querySelector=()=>options.noHeader?null:header;doc.activeElement=body;
 const media={...events(),matches:options.mobile!==false};win.document=doc;
 win.getComputedStyle=()=>({getPropertyValue:()=>options.noCSS?'':' 1 '});
 if(options.noComputedStyle)delete win.getComputedStyle;
 if(!options.noMedia)win.matchMedia=()=>media;
 if(options.installError)doc.addEventListener=()=>{throw Error('listener failed');};
 for(const key of ['fetch','scrollTo','scrollBy','localStorage','sessionStorage'])Object.defineProperty(win,key,{get(){throw Error('unexpected side effect');}});
 let prevented=false;
 function click(target=toggle){const e={target,preventDefault(){prevented=true;}};target.emit('click',e);doc.emit('click',e);return e;}
 const resize=mobile=>{media.matches=mobile;media.emit('change',{matches:mobile});};
 const boot=()=>start(win);
 return {win,doc,header,brand,toggle,panel,link,child,outside,media,boot,click,resize,prevented:()=>prevented};
}
function closed(e){assert.equal(e.toggle.hidden,false);assert.equal(e.panel.hidden,true);assert.equal(e.toggle.attrs['aria-expanded'],'false');assert.equal(e.toggle.attrs['aria-label'],'메뉴 열기');}
function opened(e){assert.equal(e.panel.hidden,false);assert.equal(e.toggle.attrs['aria-expanded'],'true');assert.equal(e.toggle.attrs['aria-label'],'메뉴 닫기');}
test('SSR has usable navigation and hidden toggle; mobile initializes then toggles repeatedly',()=>{
 const e=setup();assert.equal(e.panel.hidden,false);assert.equal(e.toggle.hidden,true);e.boot();closed(e);
 e.click();opened(e);e.click();closed(e);e.click();opened(e);assert.equal(e.prevented(),false);
});
test('desktop shows one navigation, does not respond to hidden toggle',()=>{
 const e=setup({mobile:false});e.boot();assert.equal(e.toggle.hidden,true);assert.equal(e.panel.hidden,false);e.click();assert.equal(e.panel.hidden,false);assert.equal(e.toggle.attrs['aria-expanded'],'false');
});
test('Escape closes and returns focused menu link to toggle without trapping Tab',()=>{
 const e=setup();e.boot();e.click();e.link.focus();let prevented=false;
 e.doc.emit('keydown',{key:'Tab',preventDefault(){throw Error('Tab must remain native');}});opened(e);
 e.doc.emit('keydown',{key:'Escape',preventDefault(){prevented=true;}});closed(e);assert.equal(e.doc.activeElement,e.toggle);assert.equal(prevented,true);
});
test('Escape on already closed menu is untouched',()=>{
 const e=setup();e.boot();e.doc.emit('keydown',{key:'Escape',preventDefault(){throw Error('closed');}});closed(e);
});
test('nested link click closes without cancelling cross-page or fragment navigation',()=>{
 for(const href of ['/branches/','#branch-1','/branches/#branch-1']){
  const e=setup();e.link.attrs.href=href;e.boot();e.click();e.link.focus();e.click(e.child);closed(e);assert.equal(e.prevented(),false);assert.equal(e.doc.activeElement,e.toggle);
 }
});
test('outside click closes without stealing outside focus; nonfocusable outside click repairs hidden focus',()=>{
 const e=setup();e.boot();e.click();e.link.focus();e.outside.focus();closed(e);assert.equal(e.doc.activeElement,e.outside);
 e.click();e.link.focus();e.click(e.outside);closed(e);assert.equal(e.doc.activeElement,e.toggle);assert.equal(e.prevented(),false);
});
test('focus can move from toggle through menu and leave naturally',()=>{
 const e=setup();e.boot();e.click();e.toggle.focus();opened(e);e.link.focus();opened(e);e.outside.focus();closed(e);assert.equal(e.doc.activeElement,e.outside);
});
test('resize desktop to mobile moves focused link to visible toggle before hiding panel',()=>{
 const e=setup({mobile:false});e.boot();e.link.focus();e.resize(true);closed(e);assert.equal(e.doc.activeElement,e.toggle);
});
test('resize mobile to desktop moves toggle focus to first visible link; repeated resize stable',()=>{
 const e=setup();e.boot();e.toggle.focus();e.resize(false);assert.equal(e.toggle.hidden,true);assert.equal(e.panel.hidden,false);assert.equal(e.doc.activeElement,e.link);
 e.resize(true);closed(e);e.click();e.resize(false);assert.equal(e.panel.hidden,false);assert.equal(e.toggle.attrs['aria-expanded'],'false');
});
test('pagehide and bfcache pageshow reset disclosure safely',()=>{
 const e=setup();e.boot();e.click();e.link.focus();e.win.emit('pagehide');closed(e);assert.equal(e.doc.activeElement,e.toggle);
 e.win.emit('pageshow',{persisted:true});closed(e);e.click();opened(e);e.win.emit('pageshow',{persisted:true});closed(e);
});
test('duplicate initialization does not register a second toggle handler',()=>{
 const e=setup();e.boot();e.boot();assert.equal(e.toggle.handlers.get('click').size,1);e.click();opened(e);
});
test('absent media API or listener installation failure leaves navigation usable',()=>{
 for(const options of [{noMedia:true},{installError:true}]){
  const e=setup(options);assert.doesNotThrow(e.boot);assert.equal(e.panel.hidden,false);assert.equal(e.toggle.hidden,true);assert.equal(e.header.hasAttribute('data-nav-ready'),false);assert.equal(e.media.handlers.get('change')?.size||0,0);
 }
 assert.doesNotThrow(setup({noHeader:true}).boot);
});
test('runtime callback failure fails visible and detaches handlers',()=>{
 const e=setup();e.boot();e.click();e.toggle.focus();e.doc.emit('click',{target:{closest(){throw Error('callback failure');}}});
 assert.equal(e.panel.hidden,false);assert.equal(e.toggle.hidden,true);assert.equal(e.doc.activeElement,e.brand);assert.equal(e.toggle.handlers.get('click').size,0);
});
test('print cancellation preserves disclosure state and live toggle handlers',()=>{
 for(const initiallyOpen of [false,true]){
  const e=setup();e.boot();if(initiallyOpen)e.click();e.toggle.focus();
  e.win.emit('beforeprint');e.win.emit('afterprint');
  assert.equal(e.panel.hidden,!initiallyOpen);assert.equal(e.toggle.hidden,false);assert.equal(e.doc.activeElement,e.toggle);
  e.click();assert.equal(e.panel.hidden,initiallyOpen);e.click();assert.equal(e.panel.hidden,!initiallyOpen);
 }
});

test('focus returning to header brand closes the disclosure',()=>{
 const e=setup();e.boot();e.click();e.link.focus();e.brand.focus();closed(e);assert.equal(e.doc.activeElement,e.brand);
});

test('old or missing CSS never hides SSR links or exposes an unstyled toggle',()=>{
 for(const options of [{noCSS:true},{noComputedStyle:true}]){
  const e=setup(options);e.boot();assert.equal(e.panel.hidden,false);assert.equal(e.toggle.hidden,true);
  assert.equal(e.header.hasAttribute('data-nav-ready'),false);assert.equal(e.media.handlers.size,0);
 }
});
