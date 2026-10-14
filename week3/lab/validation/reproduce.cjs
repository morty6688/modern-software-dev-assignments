const dayjs = require('dayjs');
const invalid = dayjs(new Date(NaN));
const valid = dayjs('2024-01-15');
console.log('day:', invalid.diff(valid, 'day'));
console.log('month:', invalid.diff(valid, 'month'));
