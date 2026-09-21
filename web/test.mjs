import assert from "node:assert/strict";
import { FACTORS, calculateScore } from "./caprini.mjs";

assert.equal(FACTORS.length, 38);
assert.deepEqual(calculateScore({ age: 40 }).score, 0);
assert.deepEqual(calculateScore({ age: 41 }).score, 1);
assert.deepEqual(calculateScore({ age: 61 }).score, 2);
assert.deepEqual(calculateScore({ age: 75 }).score, 3);
assert.deepEqual(calculateScore({ selected: ["stroke_lt_1mo"] }).riskTier, "High Risk");
assert.deepEqual(calculateScore({ age: 68, selected: ["malignancy", "major_open_surgery_gt_45min"] }).score, 6);
assert.equal(calculateScore({ selected: ["elective_lea"] }).scopeNotes.length, 1);
assert.throws(() => calculateScore({ age: 131 }), /between 0 and 130/);
console.log("Browser scoring smoke tests passed");
