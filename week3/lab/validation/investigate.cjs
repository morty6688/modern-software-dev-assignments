const assert = require('node:assert/strict');
const dayjs = require('dayjs');
assert.equal(require('dayjs/package.json').version, '1.11.23');
const units = ['millisecond', 'second', 'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'];
const valid = dayjs('2024-01-15');
const invalids = [['native-invalid', new Date(NaN)], ['numeric-NaN', NaN], ['bad-string', 'not-a-date']];
let checks = 0;
let violations = 0;
console.log('input,direction,float,unit,actual,expectedNaN');
for (const [name, input] of invalids) {
  const invalid = dayjs(input);
  assert.equal(invalid.isValid(), false);
  assert.equal(valid.isValid(), true);
  assert.ok(Number.isNaN(invalid.valueOf()));
  for (const [direction, a, b] of [['invalid-valid', invalid, valid], ['valid-invalid', valid, invalid], ['invalid-invalid', invalid, invalid]]) {
    for (const float of [false, true]) {
      for (const unit of units) {
        const result = a.diff(b, unit, float);
        const ok = Number.isNaN(result);
        if (!ok) violations++;
        console.log([name, direction, float, unit, String(result), ok ? 'PASS' : 'FAIL'].join(','));
        // Characterization assertions check the observed bug, not correctness.
        assert.ok(['month', 'quarter', 'year'].includes(unit) ? Object.is(result, 0) : ok);
        checks++;
      }
    }
  }
}
for (const unit of units) {
  for (const float of [false, true]) {
    assert.equal(valid.diff(valid, unit, float), 0);
    checks++;
  }
}
assert.equal(dayjs('2024-02-15').diff(valid, 'month'), 1);
assert.equal(valid.diff(dayjs('2024-02-15'), 'month'), -1);
checks += 2;
console.log(`SUMMARY characterization_checks=${checks} expected_NaN_violations=${violations}`);
if (process.argv.includes('--expect-nan') && violations) process.exitCode = 1;
