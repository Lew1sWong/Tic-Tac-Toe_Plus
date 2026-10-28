const fs = require('fs');
eval(fs.readFileSync(process.argv[2] || require('path').join(__dirname, '..', 'src', 'engine.js'), 'utf8').match(/function makeEngine[\s\S]*?\n}\n/)[0] + ';globalThis.makeEngine=makeEngine;');
const sets = {
  A: { diag: true, stay: true, order: 'asc', cyclic: false },
  B: { diag: true, stay: true, order: 'desc', cyclic: true },
  O: { diag: false, stay: false, order: 'desc', cyclic: false },
};
const names = ['左上','上中','右上','左中','中心','右中','左下','下中','右下'];
for (const [key, cfg] of Object.entries(sets)) {
  const E = makeEngine(cfg);
  const st = { b: Array(9).fill(0), k: [0, 0], p: 0 };
  let t0 = Date.now();
  const r = E.evalMoves(st);
  const t1 = Date.now() - t0;
  const cnt = { 1: 0, 0: 0, '-1': 0 };
  r.moves.forEach((x) => cnt[x.v]++);
  const after = E.next(st, 4).st;
  const r2 = E.evalMoves(after);
  const hold = r2.moves.filter((x) => x.v <= 0).map((x) => x.m < 100 ? names[x.m] : x.m);
  t0 = Date.now();
  // self-play optimal vs optimal 3 games; also AI as black vs AI
  const results = [];
  for (let g = 0; g < 3; g++) {
    let s = st, line = null, plies = 0;
    while (plies < 60) {
      if (!E.legal(s).length) { const o = { ...s, p: 1 - s.p }; if (!E.legal(o).length) break; s = o; continue; }
      const m = E.choose(s); const nx = E.next(s, m); plies++;
      if (nx.line) { line = s.p === 0 ? 'W' : 'B'; s = nx.st; break; }
      s = nx.st;
    }
    results.push((line || 'draw') + '/' + plies);
  }
  console.log(key, 'value', r.value, 'openings W/D/B', cnt[1], cnt[0], cnt['-1'], `solve ${t1}ms`, 'cached', E.cached(),
    '| after center, black holds:', hold.join(','), '| selfplay', results.join(' '), `${Date.now() - t0}ms`);
}
