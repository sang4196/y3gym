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
      return h('figure', { className: 'product-body-image', contentEditable: false },
        h('img', { src, alt: alt || '' }),
        h('figcaption', null,
        h('details', { className: 'product-body-image__options' },
          h('summary', null, '이미지 옵션'),
          h('span', null, alt ? `이미지 설명: ${alt}` : '설명 없는 장식 이미지'),
          h('div', { className: 'product-body-image__actions' },
            h('button', { type: 'button', className: 'button button-small', onClick: replace }, '이미지 선택·교체'),
            h('button', { type: 'button', className: 'button button-small button-secondary', onClick: onRemoveEntity }, '본문에서 제거')))));
    }
    return { source: ChooseImageSource, block: BodyImage };
  }

  // Capture runs before Wagtail's document bubble listener initializes React.
  document.addEventListener('w-draftail:init', (event) => {
    if (!event.target.matches('[data-product-post-editor]')) return;
    const options = event.detail;
    options.topToolbar = window.Draftail.Toolbar;
    options.placeholder = '여기에 본문을 입력하세요.';
    const imageUI = createImageUI();
    options.entityTypes = (options.entityTypes || []).map((control) => control.type === 'IMAGE'
      ? { ...control, ...imageUI }
      : control);
  }, true);

})();
