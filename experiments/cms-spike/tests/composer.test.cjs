// Unit contracts only: this does not render a browser or prove Draft.js focus behavior.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function setup() {
  const listeners = {};
  class ImageSource {
    getChooserConfig(entity) { return { entity, url: entity ? 'format-only' : 'chooser' }; }
    filterEntityData(data) { return data; }
  }
  const Toolbar = () => {};
  let clicks = 0;
  const document = {
    addEventListener(name, fn, capture) { listeners[name] = { fn, capture }; },
    querySelector(selector) { assert.equal(selector, '.w-preview [data-w-preview-target="newTab"]'); return { click() { clicks++; } }; },
  };
  const window = { React: { createElement: (type, props, ...children) => ({ type, props, children }) },
    draftail: { ImageModalWorkflowSource: ImageSource }, Draftail: { Toolbar } };
  vm.runInNewContext(fs.readFileSync('posts/static/posts/composer.js', 'utf8'), { window, document });
  return { listeners, Toolbar, ImageSource, window, clicks: () => clicks };
}
test('only Post init receives accessible toolbar and local image overrides', () => {
  const env = setup();
  const options = { entityTypes: [{ type: 'IMAGE', chooserUrls: { imageChooser: '/protected/chooser/' } }, { type: 'LINK' }], inlineStyles: [{ type: 'BOLD' }] };
  env.listeners['w-draftail:init'].fn({ target: { matches: () => false }, detail: options });
  assert.equal(options.topToolbar, undefined);
  env.listeners['w-draftail:init'].fn({ target: { matches: () => true }, detail: options });
  assert.equal(env.listeners['w-draftail:init'].capture, true);
  assert.equal(typeof options.topToolbar, 'function');
  let toggled;
  const toolbar = options.topToolbar({ inlineStyles: options.inlineStyles, blockTypes: [], entityTypes: [], currentStyles: new Set(['BOLD']), toggleInlineStyle: (value) => toggled = value });
  const bold = toolbar.children[0];
  assert.equal(bold.props['aria-pressed'], true);
  assert.equal(bold.props.type, 'button');
  bold.props.onClick();
  assert.equal(toggled, 'BOLD');
  assert.equal(options.entityTypes[1].source, undefined);
  const image = options.entityTypes[0];
  assert.equal(image.chooserUrls.imageChooser, '/protected/chooser/');
  const source = new image.source();
  assert.ok(source instanceof env.ImageSource);
  assert.equal(source.getChooserConfig({ id: 7 }).url, 'chooser');
  assert.equal(options.inlineStyles[0].label, '굵게');
  let edit = 0, remove = 0;
  const tree = image.block({ block: { getKey: () => 'image-block' }, blockProps: { entity: { getData: () => ({ src: '/cms-files/test.png', alt: 'test' }) }, onEditEntity: () => edit++, onRemoveEntity: () => remove++ } });
  const actions = tree.children[1].children[1].children;
  actions.forEach(button => assert.equal(button.props.type, 'button'));
  actions[0].props.onClick(); actions[1].props.onClick();
  assert.equal(edit, 1); assert.equal(remove, 1);
});
test('preview forwards explicit user click to official new-tab action', () => {
  const env = setup();
  env.listeners.click.fn({ target: { closest: () => null } });
  assert.equal(env.clicks(), 0);
  env.listeners.click.fn({ target: { closest: () => ({}) } });
  assert.equal(env.clicks(), 1);
});
