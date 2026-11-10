import assert from 'node:assert/strict';
import test from 'node:test';
import { createFormatStateForwarder } from '../src/embed/format-events.ts';

test('서식 상태는 값이 바뀔 때만 공개 필드로 보낸다', () => {
  const forward = createFormatStateForwarder();
  assert.equal(forward.char({ bold: true, fontFamily: '함초롬바탕' }), null, '문단 정보 전에는 보내지 않는다');
  assert.deepEqual(forward.para({ alignment: 'center', headType: 'Bullet', lineSpacing: 160 }), {
    schemaVersion: 1, bold: true, italic: false, underline: false, strikethrough: false,
    alignment: 'center', list: 'bullet',
  });
  assert.equal(forward.char({ bold: true, fontSize: 12 }), null, '공개 필드가 같으면 다시 보내지 않는다');
  assert.equal(forward.char({ bold: false })?.alignment, 'center', '글자 갱신은 직전 문단 상태를 유지한다');
  assert.equal(forward.para({ alignment: 'center', headType: 'Number' })?.list, 'number');
});
