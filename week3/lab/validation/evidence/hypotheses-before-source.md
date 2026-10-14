# Baseline hypotheses — recorded before reading diff implementation

Initial executed reproduction: native invalid Date versus fixed valid date,
`day => NaN`, `month => 0` on npm dayjs 1.11.23.

1. H1: integer truncation/default rounding converts a non-number into zero.
   Prediction: requesting floating point output should restore NaN.
2. H2: calendar units use a different calculation path that converts an invalid
   intermediate result into zero. Prediction: month/quarter/year share the
   result even in floating mode; smaller units propagate NaN.
3. H3: invalid input parsing or operand direction causes the discrepancy.
   Prediction: changing invalid input construction or swapping operands changes
   the grouping, validity, or result.

Next tests: cross units × integer/float × both operand directions; use native
invalid Date, NaN and a bad string; include both-invalid and valid controls.
Only after these tests will diff and its helper source be traced.
