import assert from 'node:assert/strict';
import test from 'node:test';
import { RhwpEditor } from '../index.js';

function editorHarness(capabilities = ['format-state-events-v1']) {
  const listeners = new Map();
  const transport = {
    request() { return Promise.resolve(undefined); },
    supports(capability) { return capabilities.includes(capability); },
    on(event, listener) {
      listeners.set(event, listener);
      return () => listeners.delete(event);
    },
    destroy() {},
  };
  return {
    editor: new RhwpEditor({ remove() {} }, transport),
    emit(event, payload) { listeners.get(event)?.(payload); },
  };
}

const plain = {
  schemaVersion: 1, bold: false, italic: false, underline: false, strikethrough: false,
  alignment: 'justify', list: 'none',
};

test('문서를 연 뒤 구독해도 마지막 서식 상태를 한 번 받는다', async () => {
  const { editor, emit } = editorHarness();
  emit('formatStateChanged', plain);
  const received = [];
  const off = editor.onFormatStateChanged((event) => received.push(event));
  await Promise.resolve();
  assert.deepEqual(received, [plain], '늦은 구독자에게 마지막 상태 재전달');
  emit('formatStateChanged', { ...plain, bold: true });
  emit('formatStateChanged', { ...plain, schemaVersion: 2 });
  assert.deepEqual(received.map((event) => event.bold), [false, true], '모르는 schema 는 버린다');
  off();
  emit('formatStateChanged', plain);
  assert.equal(received.length, 2, '해지 후에는 받지 않는다');
});

test('스튜디오가 format-state-events-v1 을 광고하지 않으면 구독이 던진다', () => {
  const { editor } = editorHarness([]);
  assert.throws(() => editor.onFormatStateChanged(() => {}));
});
