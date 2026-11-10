import type { EventBus } from '../core/event-bus';

/**
 * 캐럿 서식 상태 이벤트(`format-state-events-v1`) — 부모 페이지에 보내는 값.
 *
 * 임베드 페이지가 studio 툴바를 숨기고 자기 툴바를 그릴 때, 버튼의 켜짐 상태를 알 수 있게 한다.
 * studio 안의 `cursor-format-changed`·`cursor-para-changed` 는 캐럿이 움직일 때마다 나오므로
 * **값이 바뀔 때만** 보낸다. 내부 속성 전체가 아니라 툴바가 쓰는 공개 필드만 싣는다.
 */
export interface RhwpFormatStateV1 {
  schemaVersion: 1;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  strikethrough: boolean;
  /** 'left' | 'center' | 'right' | 'justify' | 'distribute' | 'split', 모르면 '' */
  alignment: string;
  /** 문단 머리 종류. 'none' | 'bullet' | 'number' | 'outline' */
  list: 'none' | 'bullet' | 'number' | 'outline';
}

interface CharLike {
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  strikethrough?: boolean;
}

interface ParaLike {
  alignment?: string;
  headType?: string;
}

function listOf(headType: string | undefined): RhwpFormatStateV1['list'] {
  switch (headType) {
    case 'Bullet': return 'bullet';
    case 'Number': return 'number';
    case 'Outline': return 'outline';
    default: return 'none';
  }
}

/** 글자·문단 속성을 받아 바뀐 경우에만 이벤트를 만든다. */
export function createFormatStateForwarder(): {
  char(props: unknown): RhwpFormatStateV1 | null;
  para(props: unknown): RhwpFormatStateV1 | null;
} {
  let char: CharLike | null = null;
  let para: ParaLike | null = null;
  let last = '';
  const emit = (): RhwpFormatStateV1 | null => {
    // 캐럿 갱신은 글자 → 문단 순으로 두 번 알린다. 반쪽 상태(정렬 '')를 보내지 않는다.
    if (!char || !para) return null;
    const state: RhwpFormatStateV1 = {
      schemaVersion: 1,
      bold: !!char.bold,
      italic: !!char.italic,
      underline: !!char.underline,
      strikethrough: !!char.strikethrough,
      alignment: typeof para.alignment === 'string' ? para.alignment : '',
      list: listOf(para.headType),
    };
    const key = JSON.stringify(state);
    if (key === last) return null;
    last = key;
    return state;
  };
  return {
    char(props) {
      char = (props ?? {}) as CharLike;
      return emit();
    },
    para(props) {
      para = (props ?? {}) as ParaLike;
      return emit();
    },
  };
}

export function subscribeFormatStateChanges(
  bus: Pick<EventBus, 'on'>,
  listener: (payload: RhwpFormatStateV1) => void,
): () => void {
  // 연결마다 새로 센다 — 직전 상태가 다른 세션으로 새지 않게.
  const forward = createFormatStateForwarder();
  const send = (event: RhwpFormatStateV1 | null) => {
    if (event) listener(event);
  };
  const offChar = bus.on('cursor-format-changed', (props) => send(forward.char(props)));
  const offPara = bus.on('cursor-para-changed', (props) => send(forward.para(props)));
  return () => {
    offChar();
    offPara();
  };
}
