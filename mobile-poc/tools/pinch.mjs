// ponytail: CDP로 두 손가락 핀치를 보낸다. node pinch.mjs <ws-url> <cx> <cy> <fromGap> <toGap>
const [ws, cx, cy, from, to] = process.argv.slice(2);
const sock = new WebSocket(ws);
let id = 0;
const pending = new Map();
sock.onmessage = (m) => {
  const msg = JSON.parse(m.data);
  if (pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
};
const send = (method, params = {}) => new Promise((r) => {
  pending.set(++id, r);
  sock.send(JSON.stringify({ id, method, params }));
});
const pts = (gap) => [
  { x: +cx - gap / 2, y: +cy, id: 0 },
  { x: +cx + gap / 2, y: +cy, id: 1 },
];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
sock.onopen = async () => {
  await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts(+from) });
  for (let i = 1; i <= 12; i++) {
    await send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: pts(+from + ((+to - +from) * i) / 12) });
    await sleep(30);
  }
  const r = await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  console.log('done', JSON.stringify(r.error ?? 'ok'));
  sock.close();
};
