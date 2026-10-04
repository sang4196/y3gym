// Minimal DOM/fetch doubles: request and state contracts, NOT browser rendering.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('posts/static/posts/public-client.js', 'utf8');
async function run(fetchImpl) {
  const nodes = Object.fromEntries(['public-client', 'client-status', 'client-post',
    'client-title', 'client-category', 'client-cover', 'client-body'].map(id => [id, {
      textContent: '', innerHTML: '', hidden: true, children: [],
      appendChild(child) { this.children.push(child); },
    }]));
  nodes['public-client'].dataset = { postId: '1' };
  nodes['client-post'].querySelectorAll = () => nodes['client-cover'].children;
  let request;
  await vm.runInNewContext(source, {
    document: {
      getElementById: id => nodes[id],
      createElement: () => ({ events: {}, addEventListener(name, fn) { this.events[name] = fn; } }),
    },
    fetch: async (url, options) => { request = { url, ...options }; return fetchImpl(); },
  });
  return { nodes, request };
}
test('fetches public DTO without credentials, then updates DOM; image error is visible', async () => {
  const data = { id: '1', title: '<b>plain title</b>', category: 'notice',
    body_html: '<p><b>Bold</b><i>Italic</i><a href="https://example.com/">Link</a><img src="/spike/display/2/" alt="body"></p>',
    cover_image: { url: '/spike/display/1/', alt: 'cover', width: 800, height: 600 } };
  const { nodes, request } = await run(() => ({ ok: true, status: 200, json: async () => ({ data }) }));
  assert.deepEqual(request, { url: '/spike/posts/1/json/', credentials: 'omit', cache: 'no-store', mode: 'same-origin', redirect: 'error' });
  assert.equal(nodes['client-title'].textContent, data.title);
  assert.equal(nodes['client-body'].innerHTML, data.body_html);
  assert.equal(nodes['client-cover'].children[0].src, '/spike/display/1/');
  assert.equal(nodes['client-post'].hidden, false);
  nodes['client-cover'].children[0].events.error();
  assert.match(nodes['client-status'].textContent, /이미지를 불러오지/);
});
test('404 is distinct and leaves content hidden', async () => {
  const { nodes } = await run(() => ({ ok: false, status: 404 }));
  assert.match(nodes['client-status'].textContent, /404/);
  assert.equal(nodes['client-post'].hidden, true);
});
test('network, HTTP and malformed DTO errors leave generic failure without response leakage', async () => {
  for (const response of [() => { throw new Error('internal detail'); },
    () => ({ ok: false, status: 500 }),
    () => ({ ok: true, status: 200, json: async () => ({ data: { id: '2' } }) })]) {
    const { nodes } = await run(response);
    assert.equal(nodes['client-post'].hidden, true);
    assert.match(nodes['client-status'].textContent, /표시하지 못했습니다/);
    assert.doesNotMatch(nodes['client-status'].textContent, /internal detail/);
  }
});
