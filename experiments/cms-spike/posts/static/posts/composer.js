/* Wagtail 7.4.3: scoped w-draftail:init options, Draftail Toolbar and image source. */
(() => {
  'use strict';
  const h = window.React.createElement;

  function createImageUI() {
    // One closure per widget; source props contain entityKey but no blockKey.
    // Only an explicit image button supplies the exact placement to replace.
    let requestedPlacement = null;

    class ChooseImageSource extends window.draftail.ImageModalWorkflowSource {
      constructor(props) {
        super(props);
        this.placement = requestedPlacement;
        requestedPlacement = null;
      }

      onChosen(data) {
        const { editorState, onComplete } = this.props;
        const { EditorState, Modifier, SelectionState, AtomicBlockUtils } = window.DraftJS;
        const selection = editorState.getSelection();
        let content = editorState.getCurrentContent();
        const imageData = this.filterEntityData(data);
        let next;
        if (this.placement) {
          const { blockKey, entityKey } = this.placement;
          const block = content.getBlockForKey(blockKey);
          if (!block || block.getType() !== 'atomic' || block.getEntityAt(0) !== entityKey
              || content.getEntity(entityKey).getType() !== 'IMAGE') {
            this.workflow.close();
            onComplete(editorState);
            return;
          }
          // Never merge data into a shared entity: replace only this block's reference.
          content = content.createEntity('IMAGE', 'IMMUTABLE', imageData);
          const key = content.getLastCreatedEntityKey();
          const range = SelectionState.createEmpty(blockKey).merge({ focusOffset: block.getLength() });
          content = Modifier.applyEntity(content, range, key).merge({
            selectionBefore: selection, selectionAfter: selection,
          });
          next = EditorState.acceptSelection(EditorState.push(editorState, content, 'apply-entity'), selection);
        } else {
          // Draftail may pass the caret's LINK entity here. Insertion never edits it.
          content = content.createEntity('IMAGE', 'IMMUTABLE', imageData);
          const key = content.getLastCreatedEntityKey();
          next = AtomicBlockUtils.insertAtomicBlock(EditorState.set(editorState, { currentContent: content }), key, ' ');
        }
        this.workflow.close();
        onComplete(next);
      }

      getChooserConfig() {
        return super.getChooserConfig(null);
      }
    }

    function BodyImage({ block, blockProps }) {
      const { entity, entityKey, onEditEntity, onRemoveEntity } = blockProps;
      const { src, alt } = entity.getData();
      const replace = () => {
        requestedPlacement = { blockKey: block.getKey(), entityKey };
        onEditEntity();
      };
      return h('figure', { className: 'spike-body-image', contentEditable: false },
        h('img', { src, alt: alt || '' }),
        h('figcaption', null,
          h('span', null, alt ? `이미지 설명: ${alt}` : '설명 없는 장식 이미지'),
          h('div', { className: 'spike-body-image__actions' },
            h('button', { type: 'button', className: 'button button-small', onClick: replace }, '이미지 선택·교체'),
            h('button', { type: 'button', className: 'button button-small button-secondary', onClick: onRemoveEntity }, '본문에서 제거'))));
    }
    return { source: ChooseImageSource, block: BodyImage };
  }

  function Toolbar(props) {
    const button = (control, action, pressed) => h('button', {
      key: control.type, type: 'button', className: 'spike-format-button',
      'aria-pressed': pressed,
      onMouseDown: (event) => event.preventDefault(),
      onClick: () => action(control.type),
    }, names[control.type]);
    // Normal Tab/Shift+Tab and Enter/Space work without moving the mouse selection.
    return h('div', { className: 'spike-format-bar', role: 'group', 'aria-label': '본문 서식' },
      ...props.inlineStyles.map((item) => button(item, props.toggleInlineStyle, props.currentStyles.has(item.type))),
      ...props.blockTypes.map((item) => button(item, props.toggleBlockType, props.currentBlock === item.type)),
      ...props.entityTypes.map((item) => button(item, props.onRequestSource, undefined)));
  }

  const names = {
    'header-two': '소제목', BOLD: '굵게', ITALIC: '기울임',
    'ordered-list-item': '번호 목록', 'unordered-list-item': '글머리 목록',
    LINK: '링크', IMAGE: '이미지 넣기',
  };
  function label(control) {
    return names[control.type]
      ? { ...control, icon: null, label: names[control.type], description: names[control.type] }
      : control;
  }

  // Capture runs before Wagtail's document bubble listener initializes React.
  document.addEventListener('w-draftail:init', (event) => {
    if (!event.target.matches('[data-spike-post-editor]')) return;
    const options = event.detail;
    options.topToolbar = Toolbar;
    options.placeholder = '여기에 본문을 입력하세요.';
    options.blockTypes = (options.blockTypes || []).map(label);
    options.inlineStyles = (options.inlineStyles || []).map(label);
    const imageUI = createImageUI();
    options.entityTypes = (options.entityTypes || []).map((control) => control.type === 'IMAGE'
      ? { ...label(control), ...imageUI }
      : label(control));
  }, true);

  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-spike-preview]');
    if (!button) return;
    // Reuse the official controller: it POSTs unsaved form data then opens preview.
    // No direct GET bypass, session reading, or separate preview state implementation.
    const link = document.querySelector('.w-preview [data-w-preview-target="newTab"]');
    if (link) link.click();
    else window.alert('이 화면에서 미리보기를 사용할 수 없습니다. 기존 Preview 메뉴를 확인하세요.');
  });
})();
