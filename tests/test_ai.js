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
// Easy and Normal (the SLIP values in src/page.html) against a perfect player, 100 games per level and rule set.
// In the drawn rule sets the perfect player must never lose and should win some games.
for (const key of ['A', 'B']) {
  const E = makeEngine(sets[key]);
  for (const [level, slip] of [['easy', 0.5], ['normal', 0.2]]) {
    const tally = { perfect: 0, ai: 0, draw: 0 };
    for (let g = 0; g < 100; g++) {
      const perfect = g % 2;
      let s = { b: Array(9).fill(0), k: [0, 0], p: 0 }, res = 'draw';
      for (let ply = 0; ply < 80; ply++) {
        let L = E.legal(s);
        if (!L.length) { const o = { ...s, p: 1 - s.p }; if (!E.legal(o).length) break; s = o; L = E.legal(s); }
        const m = s.p === perfect ? E.choose(s) : E.choose(s, slip);
        if (!L.includes(m)) throw new Error(`${key} ${level}: illegal move ${m}`);
        const nx = E.next(s, m);
        if (nx.line) { res = s.p === perfect ? 'perfect' : 'ai'; break; }
        s = nx.st;
      }
      tally[res]++;
    }
    const ok = tally.ai === 0 && tally.perfect > 0;
    console.log(key, level, 'AI vs perfect player', JSON.stringify(tally), ok ? 'ok' : 'FAIL');
    if (!ok) process.exitCode = 1;
  }
}
