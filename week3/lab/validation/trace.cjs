// Read-only diagnostic: executes the unchanged monthDiff function extracted
// from the version-tagged source and compares it with the installed package.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const dayjs = require('dayjs');
const source = fs.readFileSync(`${__dirname}/vendor/dayjs-1.11.23/src/utils.js`, 'utf8');
const start = source.indexOf('const monthDiff =');
const end = source.indexOf('const prettyUnit =');
assert.ok(start >= 0 && end > start);
const helpers = vm.runInNewContext(`${source.slice(start, end)}\n;({monthDiff, absFloor})`, { C: { M: 'month' } });
const invalid = dayjs(new Date(NaN));
const valid = dayjs('2024-01-15');
for (const [name, a, b] of [['invalid-valid', invalid, valid], ['valid-invalid', valid, invalid]]) {
  // Diagnostic arithmetic mirrors utils.js lines 20-25; it does not replace it.
  const wholeMonthDiff = (b.year() - a.year()) * 12 + b.month() - a.month();
  const anchor = a.clone().add(wholeMonthDiff, 'month');
  const c = b - anchor < 0;
  const anchor2 = a.clone().add(wholeMonthDiff + (c ? -1 : 1), 'month');
  const beforeFallback = -(wholeMonthDiff + (b - anchor) / (c ? anchor - anchor2 : anchor2 - anchor));
  const afterFallback = +(beforeFallback || 0);
  assert.ok(Number.isNaN(beforeFallback));
  assert.equal(afterFallback, 0);
  assert.equal(helpers.monthDiff(a, b), 0);
  assert.equal(a.$utils().m(a, b), 0);
  assert.equal(a.diff(b, 'month', true), 0);
  console.log(`${name}: wholeMonthDiff=${wholeMonthDiff}; anchor=${anchor.valueOf()}; anchor2=${anchor2.valueOf()}; beforeFallback=${beforeFallback}; afterFallback=${afterFallback}; sourceHelper=${helpers.monthDiff(a, b)}; publishedHelper=${a.$utils().m(a, b)}`);
}
assert.ok(Number.isNaN(helpers.absFloor(NaN)));
assert.ok(Number.isNaN(valid.$utils().a(NaN)));
console.log('absFloor(NaN)=NaN in tagged source and published package');
console.log('PASS: source helper, published helper, floating diff and diagnostic intermediate agree');
