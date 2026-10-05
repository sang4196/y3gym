const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createController, loadSDK} = require('../assets/naver-maps.js');
const item = (id='1', latitude=37.2) => ({id, location:{latitude,longitude:127.1}});
const config = (...items) => ({keyId:'TEST_PUBLIC',items});
function setup() {
  const state={scripts:[],maps:[],markers:[],timers:new Map(),elements:new Map(),destroyed:0,removed:0};
  for (const id of ['1','2']) state.elements.set('naver-map-'+id,{isConnected:true,hidden:true,replaceChildren(){this.cleared=true;}});
  const sdk={
    LatLng: class {constructor(lat,lng){this.lat=lat;this.lng=lng;}},
    Map: class {constructor(element,options){this.element=element;this.options=options;state.maps.push(this);}destroy(){state.destroyed++;}},
    Marker: class {constructor(options){this.options=options;state.markers.push(this);}setMap(map){assert.equal(map,null);state.removed++;}},
  };
  let timer=0;
  const win={document:{head:{appendChild(script){state.scripts.push(script);}},
    createElement(tag){assert.equal(tag,'script');return {remove(){this.removed=true;}};},
    getElementById:id=>state.elements.get(id)},
    setTimeout(callback,delay){assert.equal(delay,10000);state.timers.set(++timer,callback);return timer;},
    clearTimeout(id){state.timers.delete(id);}};
  const ready=()=>{win.naver={maps:sdk};win.__y3gymNaverReady();};
  return {win,state,sdk,ready,controller:createController(win)};
}

test('missing key, null/invalid coordinates or absent DOM cause zero SDK requests',async()=>{
  const e=setup();
  for (const value of [null,config(),{...config(item()),keyId:''},{...config(item()),keyId:'bad&secret=TEST'},
      {...config(item()),keyId:'TEST\n'},{...config(item()),keyId:undefined},
      config({id:'1',location:null}),config(item('1',NaN)),config(item('1',91)),config(item('1',true)),
      config(item('bad')),config(item('3'))]) {
    assert.equal(await e.controller.render(value),'empty');
  }
  assert.equal(e.state.scripts.length,0);assert.equal(e.state.maps.length,0);
});

test('multiple branches share official ncpKeyId SDK; coordinates copied, duplicate IDs ignored',async()=>{
  const e=setup(),value=config(item(),item('2'),item());
  const pending=e.controller.render(value);
  value.items[0].location.latitude=80;
  assert.equal(e.state.scripts.length,1);
  assert.equal(e.state.scripts[0].src,'https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=TEST_PUBLIC&callback=__y3gymNaverReady');
  e.ready();assert.equal(await pending,'shown');
  assert.equal(e.state.maps.length,2);assert.equal(e.state.markers.length,2);
  assert.equal(e.state.maps[0].options.center.lat,37.2);
  assert.equal(e.state.maps[0].options.center.lng,127.1);
  assert.deepEqual(Object.keys(e.state.maps[0].options),['center','zoom']); // SDK attribution defaults retained.
  assert.equal(e.state.timers.size,0);
});

test('repeated render does not duplicate active maps or load SDK twice',async()=>{
  const e=setup();const first=e.controller.render(config(item()));e.ready();await first;
  assert.equal(await e.controller.render(config(item())),'shown');
  assert.equal(e.state.scripts.length,1);assert.equal(e.state.destroyed,1);assert.equal(e.state.removed,1);
});

test('latest render wins while SDK pending; earlier address-location request is stale',async()=>{
  const e=setup();const old=e.controller.render(config(item()));
  const latest=e.controller.render(config(item('2',38)));
  e.ready();assert.equal(await old,'stale');assert.equal(await latest,'shown');
  assert.equal(e.state.maps.length,1);assert.equal(e.state.maps[0].options.center.lat,38);
  assert.equal(e.state.elements.get('naver-map-1').hidden,true);
});

test('new null data invalidates pending work; pagehide ignores late SDK result',async()=>{
  for (const invalidate of [e=>e.controller.render(config()),e=>e.controller.dispose()]) {
    const e=setup(),pending=e.controller.render(config(item()));
    await invalidate(e);e.ready();assert.equal(await pending,'stale');assert.equal(e.state.maps.length,0);
  }
});

for (const reason of ['network','auth','timeout']) test(reason+' hides map and ignores late success without automatic retry',async()=>{
  const e=setup();const pending=e.controller.render(config(item()));
  const late=e.win.__y3gymNaverReady;
  if (reason==='network') e.state.scripts[0].onerror();
  if (reason==='auth') e.win.navermap_authFailure();
  if (reason==='timeout') [...e.state.timers.values()][0]();
  assert.equal(await pending,'unavailable');
  e.win.naver={maps:e.sdk};late();
  assert.equal(e.state.maps.length,0);assert.equal(e.state.elements.get('naver-map-1').hidden,true);
  assert.equal(await e.controller.render(config(item())),'unavailable');assert.equal(e.state.scripts.length,1);
});

test('SDK constructor exception clears partial maps; address/contact DOM is never touched',async()=>{
  const e=setup();e.sdk.Marker=class {constructor(){throw new Error('TEST provider error');}};
  const pending=e.controller.render(config(item()));e.ready();assert.equal(await pending,'unavailable');
  assert.equal(e.state.destroyed,1);assert.equal(e.state.elements.get('naver-map-1').hidden,true);
  assert.equal(e.state.elements.get('naver-map-1').cleared,true);
});

test('disconnected target ignored and another SDK key refused in same page',async()=>{
  const e=setup();const pending=e.controller.render(config(item()));
  e.state.elements.get('naver-map-1').isConnected=false;e.ready();await pending;
  assert.equal(e.state.maps.length,0);
  await assert.rejects(loadSDK(e.win,'OTHER_PUBLIC'),/configuration/);
  assert.equal(e.state.scripts.length,1);
});

test('authentication failure after SDK callback removes visible maps and prevents reuse',async()=>{
  const e=setup(),pending=e.controller.render(config(item()));e.ready();await pending;
  e.win.navermap_authFailure();
  assert.equal(e.state.destroyed,1);assert.equal(e.state.elements.get('naver-map-1').hidden,true);
  assert.equal(await e.controller.render(config(item())),'unavailable');
  assert.equal(e.state.maps.length,1);assert.equal(e.state.scripts.length,1);
});
