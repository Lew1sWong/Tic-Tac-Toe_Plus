const fs = require('fs');
eval(fs.readFileSync(require('path').join(__dirname, '..', 'src', 'engine.js'), 'utf8') + ';globalThis.makeEngine=makeEngine;');
const sets = { A: { diag: true, stay: true, order: 'asc', cyclic: false }, B: { diag: true, stay: true, order: 'desc', cyclic: true }, O: { diag: false, stay: false, order: 'desc', cyclic: false } };
for (const [key, cfg] of Object.entries(sets)) {
  const E = makeEngine(cfg);
  for (const human of [0, 1]) {
    const tally = { human: 0, ai: 0, draw: 0 };
    for (let g = 0; g < 300; g++) {
      let s = { b: Array(9).fill(0), k: [0, 0], p: 0 }, res = 'draw';
      for (let ply = 0; ply < 80; ply++) {
        let L = E.legal(s);
        if (!L.length) { const o = { ...s, p: 1 - s.p }; if (!E.legal(o).length) break; s = o; L = E.legal(s); }
        const m = s.p === human ? L[Math.floor(Math.random() * L.length)] : E.choose(s);
        const nx = E.next(s, m);
        if (nx.line) { res = s.p === human ? 'human' : 'ai'; break; }
        s = nx.st;
      }
      tally[res]++;
    }
    console.log(key, 'random human as', human ? 'Black' : 'White', JSON.stringify(tally));
  }
}
