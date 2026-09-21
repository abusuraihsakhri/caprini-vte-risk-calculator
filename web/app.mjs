import { FACTORS, calculateScore } from "./caprini.mjs";

const factorLabels = new Map(FACTORS.map(([key, label]) => [key, label]));
const factorGroups = new Map([1, 2, 3, 5].map((points) => [points, FACTORS.filter((factor) => factor[2] === points && !factor[0].startsWith("age_"))]));

const $ = (selector) => document.querySelector(selector);
const ageInput = $("#age");
const factorList = $("#factor-list");
const scoreValue = $("#score-value");
const tierValue = $("#tier-value");
const rateValue = $("#rate-value");
const activeValue = $("#active-value");
const guidance = $("#guidance");
const selectedCount = $("#selected-count");
const errorBox = $("#error-box");
let activeTab = 1;
const selected = new Set();

function renderFactors() {
  factorList.replaceChildren();
  for (const [key, label, points] of factorGroups.get(activeTab)) {
    const item = document.createElement("label");
    item.className = "factor-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = key;
    checkbox.checked = selected.has(key);

    const copy = document.createElement("span");
    copy.className = "factor-copy";
    const text = document.createElement("span");
    text.textContent = label;
    const pointLabel = document.createElement("small");
    pointLabel.textContent = `+${points}`;
    copy.append(text, pointLabel);
    item.append(checkbox, copy);
    factorList.append(item);
  }
}

function selectedKeys() {
  return [...selected];
}

function renderResult(result) {
  scoreValue.textContent = result.score;
  tierValue.textContent = result.riskTier;
  rateValue.textContent = `${(result.vteRate * 100).toFixed(1)}%`;
  activeValue.textContent = result.activeFactors.length;
  selectedCount.textContent = `${result.activeFactors.length} active factor${result.activeFactors.length === 1 ? "" : "s"}`;

  const fragments = [];
  const summary = document.createElement("div");
  summary.className = "guidance-section";
  const summaryHeading = document.createElement("h3");
  summaryHeading.textContent = "Guideline-scoped summary";
  summary.append(summaryHeading);
  const list = document.createElement("ul");
  for (const line of result.prophylaxis) {
    const li = document.createElement("li");
    li.textContent = line;
    list.append(li);
  }
  summary.append(list);
  fragments.push(summary);

  if (result.extended.length) {
    const extended = document.createElement("div");
    extended.className = "guidance-section";
    const extendedHeading = document.createElement("h3");
    extendedHeading.textContent = "Extended-duration note";
    extended.append(extendedHeading);
    const p = document.createElement("p");
    p.textContent = result.extended[0];
    extended.append(p);
    fragments.push(extended);
  }

  if (result.scopeNotes.length) {
    const scope = document.createElement("div");
    scope.className = "guidance-section warning";
    const scopeHeading = document.createElement("h3");
    scopeHeading.textContent = "Population scope";
    scope.append(scopeHeading);
    const p = document.createElement("p");
    p.textContent = result.scopeNotes[0];
    scope.append(p);
    fragments.push(scope);
  }

  const active = document.createElement("div");
  active.className = "guidance-section active-breakdown";
  const activeHeading = document.createElement("h3");
  activeHeading.textContent = "Active factors";
  active.append(activeHeading);
  const activeList = document.createElement("div");
  activeList.className = "chips";
  for (const [key, points] of result.activeFactors) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${factorLabels.get(key) ?? key} +${points}`;
    activeList.append(chip);
  }
  if (!result.activeFactors.length) activeList.textContent = "No scored factors selected.";
  active.append(activeList);
  fragments.push(active);

  guidance.replaceChildren(...fragments);
}

function calculate() {
  errorBox.hidden = true;
  try {
    const result = calculateScore({ age: ageInput.value, selected: selectedKeys() });
    renderResult(result);
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
}

function reset() {
  ageInput.value = "";
  selected.clear();
  renderFactors();
  calculate();
}

$("#tabs").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-points]");
  if (!button) return;
  activeTab = Number(button.dataset.points);
  document.querySelectorAll("button[data-points]").forEach((tab) => {
    const isActive = tab === button;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-pressed", String(isActive));
  });
  renderFactors();
});

$("#calculate").addEventListener("click", calculate);
$("#reset").addEventListener("click", reset);
ageInput.addEventListener("input", calculate);
factorList.addEventListener("change", (event) => {
  if (!event.target.matches('input[type="checkbox"]')) return;
  if (event.target.checked) selected.add(event.target.value);
  else selected.delete(event.target.value);
  calculate();
});

$("#theme-toggle").addEventListener("click", () => {
  const current = document.documentElement.dataset.theme;
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("caprini-theme", next);
  $("#theme-toggle").setAttribute("aria-label", `Switch to ${next === "dark" ? "light" : "dark"} theme`);
});

document.documentElement.dataset.theme = localStorage.getItem("caprini-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
$("#theme-toggle").setAttribute("aria-label", `Switch to ${document.documentElement.dataset.theme === "dark" ? "light" : "dark"} theme`);
document.querySelectorAll("button[data-points]").forEach((tab) => tab.setAttribute("aria-pressed", String(tab.classList.contains("active"))));
renderFactors();
calculate();
