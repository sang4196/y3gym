/* SPIKE only. body_html is trusted solely from the existing same-origin
 * public serializer's allowlist sanitizer. Never accept an arbitrary API URL,
 * CMS/raw HTML or preview DTO here. This is not an additional sanitizer. */
(async function () {
  'use strict';
  const root = document.getElementById('public-client');
  const status = document.getElementById('client-status');
  const article = document.getElementById('client-post');
  try {
    const id = root.dataset.postId;
    if (!/^\d+$/.test(id)) throw new Error('Invalid ID');
    const response = await fetch(`/spike/posts/${id}/json/`, {
      credentials: 'omit', cache: 'no-store', mode: 'same-origin', redirect: 'error',
    });
    if (response.status === 404) {
      status.textContent = '공개 게시글을 찾을 수 없습니다 (404).';
      return;
    }
    if (!response.ok) throw new Error('Request failed');
    const { data } = await response.json();
    if (!data || data.id !== id || typeof data.title !== 'string' ||
        typeof data.category !== 'string' || typeof data.body_html !== 'string') {
      throw new Error('Invalid public response');
    }
    document.getElementById('client-title').textContent = data.title;
    document.getElementById('client-category').textContent = data.category;
    const cover = document.getElementById('client-cover');
    if (data.cover_image) {
      const img = document.createElement('img');
      img.src = data.cover_image.url;
      img.alt = data.cover_image.alt;
      img.width = data.cover_image.width;
      img.height = data.cover_image.height;
      cover.appendChild(img);
    }
    document.getElementById('client-body').innerHTML = data.body_html;
    article.querySelectorAll('img').forEach(img => {
      img.addEventListener('error', () => {
        status.textContent = '공개 JSON은 표시했지만 이미지를 불러오지 못했습니다.';
      });
    });
    article.hidden = false;
    status.textContent = '공개 JSON을 받아 표시했습니다. 서식·링크·이미지를 확인해 주세요.';
  } catch (_) {
    article.hidden = true;
    status.textContent = '공개 JSON을 불러오거나 표시하지 못했습니다. 잠시 후 새로고침해 주세요.';
  }
})();
