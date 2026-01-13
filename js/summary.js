/* =========================================================
   SUMMARY PAGE LOGIC (PHASE 1 – REAL DATA)
   - Uses actual analysis output
   - No mock narrative
   - Transparent, explainable logic
   - ML / RAG replaceable in Phase 2
========================================================= */

const stateSelect = document.getElementById("summaryState");
const monthInput = document.getElementById("summaryMonth");

const executiveSummaryEl = document.getElementById("executiveSummary");
const adoptionEl = document.getElementById("adoptionStatus");
const strengthsEl = document.getElementById("strengths");
const gapsEl = document.getElementById("gaps");
const caseStudiesEl = document.getElementById("caseStudies");

// Load stored analysis data (from analyze.html)
const analysisData = JSON.parse(
  sessionStorage.getItem("negd-analysis") || "{}"
);

stateSelect.addEventListener("change", generateSummary);
monthInput.addEventListener("change", generateSummary);

// Pre-fill state/month if available
if (analysisData.state) stateSelect.value = analysisData.state;
if (analysisData.month) monthInput.value = analysisData.month;

generateSummary();

/* =========================
   SUMMARY GENERATION
========================= */

function generateSummary() {
  const state = stateSelect.value;
  const month = monthInput.value;

  if (!state || !month) {
    executiveSummaryEl.textContent =
      "Please select both state and reporting month.";
    return;
  }

  if (!analysisData.text) {
    executiveSummaryEl.textContent =
      "No analyzed report data found. Please analyze a report first.";
    return;
  }

  const {
    text,
    wordCount,
    headingsCount,
    keywordMatches
  } = analysisData;

  /* =========================
     ADOPTION CLASSIFICATION
  ========================= */

  let adoptionStatus = "Low Adoption";
  if (keywordMatches >= 3 && wordCount > 1500) {
    adoptionStatus = "High Adoption";
  } else if (keywordMatches >= 1) {
    adoptionStatus = "Moderate Adoption";
  }

  /* =========================
     STRENGTHS & GAPS
  ========================= */

  const strengths = [];
  const gaps = [];

  if (text.toLowerCase().includes("digilocker")) {
    strengths.push("DigiLocker referenced in report");
  } else {
    gaps.push("No explicit DigiLocker reference");
  }

  if (headingsCount >= 5) {
    strengths.push("Structured reporting with clear sections");
  } else {
    gaps.push("Lack of clearly structured sections");
  }

  if (wordCount < 1000) {
    gaps.push("Report lacks sufficient detail");
  }

  /* =========================
     EXECUTIVE SUMMARY
  ========================= */

  executiveSummaryEl.textContent = `
The ${state} submission for ${month} has been analyzed using a
rule-based intelligence framework. The report contains approximately
${wordCount} words and ${headingsCount} identifiable structural sections.
Key digital governance initiatives are ${
    keywordMatches > 0 ? "referenced" : "largely absent"
  } within the document.

Based on content density, structure, and keyword presence, the overall
digital adoption level is assessed as "${adoptionStatus}". The analysis
is grounded directly in submitted report content and is intended to
support internal review and comparison.
  `.trim();
  adoptionEl.textContent = adoptionStatus;
  strengthsEl.textContent = strengths.length
    ? strengths.join("; ")
    : "No strong indicators detected";
  gapsEl.textContent = gaps.length
    ? gaps.join("; ")
    : "No major gaps detected";
  caseStudiesEl.textContent =
    text.toLowerCase().includes("certificate")
      ? "Digital certificate issuance referenced"
      : "No explicit case studies identified";
}