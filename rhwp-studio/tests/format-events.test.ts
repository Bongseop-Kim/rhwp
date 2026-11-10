import assert from 'node:assert/strict';
import test from 'node:test';
import { createFormatStateForwarder } from '../src/embed/format-events.ts';

test('서식 상태는 값이 바뀔 때만 공개 필드로 보낸다', () => {
  const forward = createFormatStateForwarder();
  const first = forward.char({ bold: true, fontFamily: '함초롬바탕' });
  assert.deepEqual(first, {
    schemaVersion: 1, bold: true, italic: false, underline: false, strikethrough: false,
    alignment: '', list: 'none',
  });
  assert.equal(forward.char({ bold: true, fontSize: 12 }), null, '공개 필드가 같으면 다시 보내지 않는다');
  const para = forward.para({ alignment: 'center', headType: 'Bullet', lineSpacing: 160 });
  assert.equal(para?.alignment, 'center');
  assert.equal(para?.list, 'bullet');
  assert.equal(para?.bold, true, '문단 갱신은 직전 글자 상태를 유지한다');
  assert.equal(forward.para({ alignment: 'center', headType: 'Number' })?.list, 'number');
});
