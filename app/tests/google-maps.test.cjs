const {test}=require('node:test');
const assert=require('node:assert/strict');
const maps=require('../assets/google-maps.js');
const admin=require('../assets/branch-google-map.js');
const URL='https://www.google.com/maps/embed?pb=!1m18!2m3!1d123!2d456!3d789!2sTEST';
const HTML=`<iframe src="${URL}" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>`;
function node(value='') {
 const handlers={};
 const n={value,dataset:{},hidden:true,disabled:false,textContent:'',attrs:{},children:[],
 addEventListener(k,cb){(handlers[k]??=[]).push(cb);},emit(k,e={}){for(const cb of handlers[k]||[])cb(e);},
 setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];},appendChild(el){this.children.push(el);el.parent=this;},
 remove(){this.removed=true;if(this.parent)this.parent.children=this.parent.children.filter(el=>el!==this);},focus(){this.focused=true;}};
 Object.defineProperty(n,'innerHTML',{set(){throw Error('raw markup forbidden');}});return n;
}
function setup(isAdmin=false) {
 const win=node(),s={frames:[],timers:new Map()};let count=0;
 win.document={createElement(tag){assert.equal(tag,'iframe');const f=node();s.frames.push(f);return f;}};
 win.setTimeout=(fn,ms)=>{s.timers.set(++count,{fn,ms});return count;};win.clearTimeout=id=>s.timers.delete(id);
 for(const key of ['fetch','XMLHttpRequest','localStorage','sessionStorage','DOMParser'])Object.defineProperty(win,key,{get(){throw Error('forbidden '+key);}});
 const controls={};for(const name of ['open','close','confirm','status','canvas'])controls[name]=node();
 const fields={};for(const name of ['google_map_input','address','edit_version','map_confirmation','map_confirmation_address','map_confirmation_version','map_confirmation_url'])fields[name]=node();
 fields.google_map_input.value=HTML;fields.address.value='TEST address';fields.edit_version.value='4';
 const form=node();form.elements={namedItem:name=>fields[name]};
 const area=node();area.dataset={embedUrl:URL,mapTitle:'TEST 지점 Google 지도'};
 area.querySelector=selector=>selector==='[data-saved-map-status]' ? (controls.saved??=node()) : controls[selector.slice(10,-1)];
 area.closest=()=>form;
 const c=isAdmin?admin.mount(win,area,maps):maps.mount(win,area);
 return {win,s,controls,fields,form,area,c};
}
test('official pasted HTML and URL preserve pb without DOM execution',()=>{
 assert.equal(maps.parseInput(HTML),URL);assert.equal(maps.parseInput(URL),URL);
 assert.equal(maps.parseInput(HTML.replaceAll('!','&#33;')),URL);assert.equal(maps.parseInput(''),'');
});
test('reject executable or ambiguous markup and non-embed URLs',()=>{
 for(const value of [HTML.replace('width=','onload='),HTML.replace('width=','srcdoc='),HTML.replace('width=',`src="${URL}" width=`),HTML+'<script>x</script>',`<div>${HTML}</div>`,HTML.replace('</iframe>','x</iframe>'),`<!--x-->${HTML}`])assert.throws(()=>maps.parseInput(value));
 for(const value of [URL.replace('https:','http:'),URL.replace('.com','.com.evil'),URL.replace('www.','x@www.'),URL.replace('.com','.com:443'),URL.replace('/embed','/embed/v1/place'),URL+'#',URL+'&pb=!2',URL+'&key=TEST',URL+'%0a',URL+'%3C',URL+'%ZZ',URL+'\t','https://maps.app.goo.gl/TEST'])assert.throws(()=>maps.validateURL(value));
});
test('zero frames before click; app fixes attributes, no supplied style, address area untouched',()=>{
 const e=setup();assert.equal(e.s.frames.length,0);e.controls.open.emit('click');
 const f=e.s.frames[0];assert.equal(f.attrs.src,URL);assert.equal(f.attrs.title,'TEST 지점 Google 지도');
 assert.deepEqual(Object.keys(f.attrs).sort(),['allowfullscreen','loading','referrerpolicy','src','title']);
 assert.equal(e.controls.canvas.children.length,1);assert.equal(e.controls.open.disabled,true);
 f.emit('load');assert.match(e.controls.status.textContent,/직접 확인/);assert.equal(e.controls.open.disabled,false);
 assert.equal(e.s.timers.size,0);f.emit('load');assert.equal(e.s.frames.length,1);
});
test('reopen detaches old frame; late old load cannot complete new request',()=>{
 const e=setup();e.c.show(URL);const old=e.s.frames[0];e.c.show(URL+'!2sNEW');
 assert.equal(old.removed,true);assert.equal(old.attrs.src,undefined);old.emit('load');assert.equal(e.controls.open.disabled,true);
 e.s.frames[1].emit('load');assert.equal(e.controls.open.disabled,false);assert.equal(e.controls.canvas.children.length,1);
});
test('timeout hides frame; late load ignored; explicit retry succeeds',()=>{
 const e=setup();e.controls.open.emit('click');const f=e.s.frames[0];[...e.s.timers.values()][0].fn();
 assert.equal(e.controls.canvas.hidden,true);assert.match(e.controls.status.textContent,/응답이 늦/);
 f.emit('load');assert.match(e.controls.status.textContent,/응답이 늦/);
 e.controls.open.emit('click');e.s.frames[1].emit('load');assert.equal(e.controls.canvas.hidden,false);
});
test('error cleans frame and close restores focus',()=>{
 const e=setup();e.controls.open.emit('click');e.s.frames[0].emit('error');assert.equal(e.s.timers.size,0);
 assert.equal(e.controls.canvas.hidden,true);e.controls.close.emit('click');assert.equal(e.controls.open.focused,true);
});
test('pagehide cleans, bfcache never reloads without click, repeated mount ignored',()=>{
 const e=setup();assert.equal(maps.mount(e.win,e.area),undefined);e.controls.open.emit('click');e.win.emit('pagehide');
 assert.equal(e.controls.canvas.children.length,0);e.c.show(URL);assert.equal(e.s.frames.length,1);
 e.win.emit('pageshow',{persisted:true});assert.equal(e.s.frames.length,1);e.controls.open.emit('click');assert.equal(e.s.frames.length,2);
});
test('admin confirms exact URL/address/version only after user action, not iframe load',()=>{
 const e=setup(true);assert.equal(e.s.frames.length,0);e.controls.open.emit('click');assert.equal(e.controls.confirm.disabled,true);
 e.s.frames[0].emit('load');assert.equal(e.fields.map_confirmation.value,'');e.controls.confirm.emit('click');
 assert.equal(e.fields.map_confirmation.value,'true');assert.equal(e.fields.map_confirmation_url.value,URL);
 assert.equal(e.fields.map_confirmation_address.value,'TEST address');assert.equal(e.fields.map_confirmation_version.value,'4');
 e.form.emit('submit');assert.equal(e.fields.map_confirmation.value,'true');
});
test('admin edits invalidate even if edited back; late events do not confirm',()=>{
 for(const field of ['google_map_input','address','edit_version']){
  const e=setup(true);e.controls.open.emit('click');const f=e.s.frames[0];const old=e.fields[field].value;
  e.fields[field].value+='CHANGED';e.fields[field].emit('input');e.fields[field].value=old;e.fields[field].emit('input');
  f.emit('load');assert.equal(e.controls.confirm.disabled,true);assert.equal(e.fields.map_confirmation.value,'');assert.equal(e.controls.canvas.children.length,0);
 }
});
test('admin submit catches programmatic changes and pagehide clears intent',()=>{
 const e=setup(true);e.controls.open.emit('click');e.s.frames[0].emit('load');e.controls.confirm.emit('click');
 e.fields.address.value='OTHER';e.form.emit('submit');assert.equal(e.fields.map_confirmation.value,'');
 e.controls.open.emit('click');e.s.frames[1].emit('load');e.controls.confirm.emit('click');e.win.emit('pagehide');
 assert.equal(e.fields.map_confirmation.value,'');e.win.emit('pageshow',{persisted:true});assert.equal(e.s.frames.length,2);
});
test('admin invalid markup or missing address does not create iframe',()=>{
 const e=setup(true);e.fields.google_map_input.value=HTML+'<script>x</script>';e.controls.open.emit('click');assert.equal(e.s.frames.length,0);
 e.fields.google_map_input.value=HTML;e.fields.address.value='';e.controls.open.emit('click');assert.equal(e.s.frames.length,0);
});

test('reject URL control whitespace before trimming and trailing query separators',()=>{
 for(const raw of ['\n'+URL,URL+'\n',URL+'&'])assert.throws(()=>maps.parseInput(raw));
});
