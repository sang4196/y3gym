// Installed Draft.js state transitions and installed Wagtail source methods, not a browser.
// Bundles are evaluated in a Node VM only; on-disk packages are never modified.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const cp = require('node:child_process');
const root = path.resolve(__dirname, '..');
const bundleDir = cp.execFileSync(path.join(root, '.venv/bin/python'), ['-c',
  "import wagtail,pathlib; print(pathlib.Path(wagtail.__file__).parent/'admin/static/wagtailadmin/js')"], { encoding: 'utf8' }).trim();
function setup() {
  const ctx = { console, setTimeout, clearTimeout };
  ctx.window = ctx; ctx.self = ctx; vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(bundleDir, 'vendor.js'), 'utf8'), ctx);
  const bundle = fs.readFileSync(path.join(bundleDir, 'draftail.js'), 'utf8');
  const bootstrap = 'var o=r.O(void 0,[321],()=>r(4037));o=r.O(o)';
  assert.ok(bundle.includes(bootstrap), 'Review loader against installed Wagtail when bundle changes');
  vm.runInContext(bundle.replace(bootstrap, 'globalThis.installedRequire=r'), ctx);
  const D = ctx.installedRequire(8335);
  ctx.i = ctx.installedRequire(2427); ctx.React = ctx.i; ctx.DraftJS = D;
  const baseStart = bundle.indexOf('class Ve extends i.Component');
  const baseEnd = bundle.indexOf('Ve.propTypes=', baseStart);
  assert.ok(baseStart > 0 && baseEnd > baseStart);
  vm.runInContext(bundle.slice(baseStart, baseEnd), ctx);
  const imageStart = bundle.indexOf('ImageModalWorkflowSource:class extends Ve');
  const imageEnd = bundle.indexOf(',EmbedModalWorkflowSource:', imageStart);
  assert.ok(imageStart > 0 && imageEnd > imageStart);
  vm.runInContext('globalThis.InstalledImageSource=' + bundle.slice(imageStart + 'ImageModalWorkflowSource:'.length, imageEnd), ctx);
  ctx.draftail = { ImageModalWorkflowSource: ctx.InstalledImageSource };
  const listeners = {};
  ctx.document = { addEventListener: (name, fn) => listeners[name] = fn };
  vm.runInContext(fs.readFileSync(path.join(root, 'posts/static/posts/composer.js'), 'utf8'), ctx);
  function widget() {
    const options = { entityTypes: [{ type: 'IMAGE', chooserUrls: { imageChooser: '/admin/images/chooser/' } }] };
    listeners['w-draftail:init']({ target: { matches: () => true }, detail: options });
    return options.entityTypes[0];
  }
  // Execute the installed onRequestSource method to retain its LINK-at-caret behavior.
  const request = bundle.match(/onRequestSource\(t\)\{([\s\S]*?)\}onCompleteSource/);
  assert.ok(request);
  const selectionEntity = bundle.match(/getSelectionEntity\(t\)\{([\s\S]*?)\},getEntitySelection/);
  const selectedBlock = bundle.match(/getSelectedBlock\(t\)\{([\s\S]*?)\},/);
  assert.ok(selectionEntity && selectedBlock);
  vm.runInContext('globalThis.at={getSelectedBlock(t){' + selectedBlock[1] + '},getSelectionEntity(t){' + selectionEntity[1] + '}}', ctx);
  vm.runInContext('globalThis.requestSource=function(t){' + request[1] + '}', ctx);
  return { D, ctx, widget };
}
function rawBlock(key, type, text, entityKey) {
  return { key, type, text, depth: 0, inlineStyleRanges: [],
    entityRanges: entityKey == null ? [] : [{ offset: 0, length: text.length, key: entityKey }], data: {} };
}
function state(env) {
  const { D } = env;
  let value = D.EditorState.createWithContent(D.convertFromRaw({ blocks: [
    rawBlock('text', 'unstyled', 'before', null), rawBlock('first', 'atomic', ' ', 0),
    rawBlock('middle', 'unstyled', 'between', null), rawBlock('second', 'atomic', ' ', 0),
    rawBlock('link', 'unstyled', 'linked', 1),
  ], entityMap: {
    0: { type: 'IMAGE', mutability: 'IMMUTABLE', data: { id: 1, src: '/cms-files/old.png', alt: 'old alt', format: 'left' } },
    1: { type: 'LINK', mutability: 'MUTABLE', data: { url: 'https://example.com/' } },
  } }));
  return D.EditorState.acceptSelection(value, D.SelectionState.createEmpty('link').merge({ anchorOffset: 2, focusOffset: 2, hasFocus: true }));
}
const choice = { id: 7, preview: { url: '/cms-files/new.png' }, alt: 'new alt', format: 'fullwidth' };
function open(env, image, editorState, blockKey) {
  let source, completed, closed = false, cancelled = false;
  const content = editorState.getCurrentContent();
  const start = (entityKey, entity) => {
    source = new image.source({ editorState, entityKey, entity, entityType: image,
      onComplete: (next) => completed = next, onClose: () => cancelled = true });
    source.workflow = { close: () => closed = true };
  };
  if (blockKey) {
    const block = content.getBlockForKey(blockKey), entityKey = block.getEntityAt(0);
    const element = image.block({ block, blockProps: { entityKey, entity: content.getEntity(entityKey),
      onEditEntity: () => start(entityKey, content.getEntity(entityKey)), onRemoveEntity() {} } });
    element.props.children[1].props.children[1].props.children[0].props.onClick();
  } else {
    env.ctx.requestSource.call({ getEditorState: () => editorState,
      toggleSource: (type, key, entity) => { assert.equal(type, 'IMAGE'); start(key, entity); } }, 'IMAGE');
  }
  return { source, result: () => ({ completed, closed, cancelled }) };
}
function dataAt(state, key) {
  const content = state.getCurrentContent();
  return content.getEntity(content.getBlockForKey(key).getEntityAt(0)).getData();
}
function raw(env, state) { return JSON.stringify(env.D.convertToRaw(state.getCurrentContent())); }

test('actual LINK-at-caret request inserts an IMAGE and completes chooser', () => {
  const env = setup(), original = state(env), originalRaw = raw(env, original);
  const flow = open(env, env.widget(), original);
  assert.equal(flow.source.props.entity.getType(), 'LINK');
  flow.source.onChosen(choice);
  const { completed, closed } = flow.result();
  assert.ok(closed && completed);
  assert.equal(completed.getCurrentContent().getBlocksAsArray().filter(b => b.getType() === 'atomic').length, 3);
  assert.equal(dataAt(completed, 'first').id, 1); assert.equal(dataAt(completed, 'second').id, 1);
  const links = Object.values(env.D.convertToRaw(completed.getCurrentContent()).entityMap).filter(e => e.type === 'LINK');
  assert.equal(links[0].data.url, 'https://example.com/');
  assert.equal(raw(env, original), originalRaw);
});
for (const target of ['first', 'second']) {
  test(`shared IMAGE entity: only ${target} placement changes, selection and undo preserved`, () => {
    const env = setup(), original = state(env), before = raw(env, original);
    const flow = open(env, env.widget(), original, target);
    flow.source.onChosen(choice);
    const { completed, closed } = flow.result();
    assert.ok(closed && completed);
    const other = target === 'first' ? 'second' : 'first';
    assert.equal(dataAt(completed, target).id, 7);
    assert.equal(dataAt(completed, target).alt, 'new alt');
    assert.equal(dataAt(completed, target).format, 'fullwidth');
    assert.equal(JSON.stringify(dataAt(completed, other)), JSON.stringify(dataAt(original, other)));
    for (const key of ['text', 'middle', 'link']) assert.ok(completed.getCurrentContent().getBlockForKey(key).equals(original.getCurrentContent().getBlockForKey(key)));
    assert.ok(completed.getSelection().equals(original.getSelection()));
    assert.equal(raw(env, original), before);
    assert.equal(raw(env, env.D.EditorState.undo(completed)), before);
  });
}
for (const target of [null, 'first', 'second']) {
  test(`installed chooser cancel is content/selection neutral (${target || 'insert'}); next insert is independent`, () => {
    const env = setup(), image = env.widget(), original = state(env), before = raw(env, original);
    const selection = original.getSelection();
    const flow = open(env, image, original, target);
    let prevented = false;
    flow.source.onClose({ preventDefault() { prevented = true; } });
    assert.ok(prevented && flow.result().cancelled);
    assert.equal(flow.result().completed, undefined);
    assert.equal(raw(env, original), before); assert.ok(original.getSelection().equals(selection));
    const next = open(env, image, original); next.source.onChosen(choice);
    assert.equal(dataAt(next.result().completed, 'second').id, 1);
    assert.equal(next.result().completed.getCurrentContent().getBlocksAsArray().filter(b => b.getType() === 'atomic').length, 3);
  });
}
