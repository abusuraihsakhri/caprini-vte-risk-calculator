export const FACTORS = [
  ["age_41_60", "Age 41–60 years", 1],
  ["minor_surgery_lt_45min", "Minor surgery (<45 min)", 1],
  ["bmi_gt_25", "BMI >25 kg/m²", 1],
  ["swollen_legs", "Swollen legs (current)", 1],
  ["varicose_veins", "Varicose veins", 1],
  ["pregnancy_or_postpartum", "Pregnancy or postpartum", 1],
  ["recurrent_miscarriage", "History of unexplained/recurrent spontaneous abortion", 1],
  ["oral_contraceptives_or_hrt", "Oral contraceptives or hormone replacement therapy", 1],
  ["sepsis_lt_1mo", "Sepsis (<1 month)", 1],
  ["serious_lung_disease_lt_1mo", "Serious lung disease, including pneumonia (<1 month)", 1],
  ["abnormal_pulmonary_function", "Abnormal pulmonary function", 1],
  ["acute_mi", "Acute myocardial infarction (<1 month)", 1],
  ["chf_lt_1mo", "Congestive heart failure (<1 month)", 1],
  ["inflammatory_bowel_disease", "History of inflammatory bowel disease", 1],
  ["medical_patient_bed_rest", "Medical patient currently at bed rest", 1],
  ["age_61_74", "Age 61–74 years", 2],
  ["arthroscopic_surgery", "Arthroscopic surgery", 2],
  ["major_open_surgery_gt_45min", "Major open surgery (>45 min)", 2],
  ["laparoscopic_surgery_gt_45min", "Laparoscopic surgery (>45 min)", 2],
  ["malignancy", "Malignancy (present or previous)", 2],
  ["bed_rest_gt_72h", "Confined to bed (>72 h)", 2],
  ["immobilizing_plaster_cast", "Immobilizing plaster cast", 2],
  ["central_venous_access", "Central venous access", 2],
  ["age_75_plus", "Age ≥75 years", 3],
  ["history_of_vte", "History of VTE (DVT/PE)", 3],
  ["family_history_of_vte", "Family history of VTE", 3],
  ["factor_v_leiden", "Factor V Leiden", 3],
  ["prothrombin_20210a", "Prothrombin 20210A", 3],
  ["lupus_anticoagulant", "Lupus anticoagulant", 3],
  ["anticardiolipin_antibodies", "Anticardiolipin antibodies", 3],
  ["elevated_homocysteine", "Elevated serum homocysteine", 3],
  ["hit", "Heparin-induced thrombocytopenia", 3],
  ["other_thrombophilia", "Other congenital/acquired thrombophilia", 3],
  ["stroke_lt_1mo", "Stroke (<1 month)", 5],
  ["multiple_trauma_lt_1mo", "Multiple/serious trauma (<1 month)", 5],
  ["elective_lea", "Elective major lower-extremity arthroplasty", 5],
  ["hip_pelvis_leg_fracture_lt_1mo", "Hip, pelvis, or leg fracture (<1 month)", 5],
  ["acute_spinal_cord_injury_lt_1mo", "Acute spinal cord injury with paralysis (<1 month)", 5],
];

const AGE_KEYS = new Set(["age_41_60", "age_61_74", "age_75_plus"]);
const FACTOR_POINTS = new Map(FACTORS.map(([key, , points]) => [key, points]));
const NON_GENERAL_SURGERY_SCOPE_KEYS = new Set([
  "arthroscopic_surgery",
  "elective_lea",
  "hip_pelvis_leg_fracture_lt_1mo",
  "acute_spinal_cord_injury_lt_1mo",
  "multiple_trauma_lt_1mo",
  "medical_patient_bed_rest",
]);

export const PROPHYLAXIS = {
  "Very Low Risk": ["Early ambulation; no specific pharmacologic or mechanical prophylaxis is recommended for general/abdominal-pelvic surgery."],
  "Low Risk": ["Mechanical prophylaxis, preferably intermittent pneumatic compression (IPC), is suggested for general/abdominal-pelvic surgery."],
  "Moderate Risk": [
    "If major-bleeding risk is not high: LMWH, low-dose unfractionated heparin (LDUH), or mechanical prophylaxis (preferably IPC) may be used.",
    "If major-bleeding risk is high or bleeding consequences would be severe: use mechanical prophylaxis (preferably IPC) until bleeding risk decreases.",
  ],
  "High Risk": [
    "If major-bleeding risk is not high: pharmacologic prophylaxis with LMWH or LDUH is recommended; adding mechanical prophylaxis (IPC or elastic stockings) is suggested.",
    "If major-bleeding risk is high or bleeding consequences would be severe: use mechanical prophylaxis (preferably IPC) until bleeding risk decreases and pharmacologic prophylaxis can be considered.",
  ],
};

function ageFactor(age) {
  if (age == null || age === "") return null;
  const parsed = Number(age);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 130) throw new Error("Age must be between 0 and 130 years.");
  if (parsed >= 75) return "age_75_plus";
  if (parsed >= 61) return "age_61_74";
  if (parsed >= 41) return "age_41_60";
  return null;
}

export function calculateScore({ age = null, selected = [] } = {}) {
  const active = new Map();
  const ageKey = ageFactor(age);
  if (ageKey) active.set(ageKey, FACTOR_POINTS.get(ageKey));

  for (const key of selected) {
    if (AGE_KEYS.has(key)) continue;
    const points = FACTOR_POINTS.get(key);
    if (points) active.set(key, points);
  }

  const score = [...active.values()].reduce((sum, value) => sum + value, 0);
  let riskTier;
  let vteRate;
  if (score === 0) [riskTier, vteRate] = ["Very Low Risk", 0.005];
  else if (score <= 2) [riskTier, vteRate] = ["Low Risk", 0.015];
  else if (score <= 4) [riskTier, vteRate] = ["Moderate Risk", 0.03];
  else [riskTier, vteRate] = ["High Risk", 0.06];

  const extended = [];
  if (riskTier === "High Risk" && active.has("malignancy")) {
    extended.push("If this patient is undergoing abdominal or pelvic cancer surgery and major-bleeding risk is not high, CHEST 2012 recommends extended-duration LMWH prophylaxis for 4 weeks.");
  }

  const scopeNotes = [];
  if ([...active.keys()].some((key) => NON_GENERAL_SURGERY_SCOPE_KEYS.has(key))) {
    scopeNotes.push("Orthopedic, trauma, spinal-cord-injury, and medical-inpatient contexts require population-specific prophylaxis guidance; do not apply the general/abdominal-pelvic prophylaxis mapping without checking the relevant guideline.");
  }

  return {
    score,
    riskTier,
    vteRate,
    activeFactors: [...active.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])),
    prophylaxis: [...PROPHYLAXIS[riskTier]],
    extended,
    scopeNotes,
  };
}
