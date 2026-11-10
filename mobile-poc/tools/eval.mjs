const [ws, expr] = process.argv.slice(2);
const s = new WebSocket(ws);
s.onopen = () => s.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: { expression: expr, awaitPromise: true, returnByValue: true } }));
s.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id === 1) { console.log(JSON.stringify(d.result?.result?.value ?? d.result)); s.close(); } };
