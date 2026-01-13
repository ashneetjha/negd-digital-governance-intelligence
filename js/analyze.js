/* =========================================================
   ANALYZE PAGE LOGIC (PHASE 1 – REAL DATA PIPELINE)
   - PDF.js + Mammoth.js
   - Transparent rule-based analysis
   - Persists data for Summary page
   - ML / RAG replaceable
========================================================= */

const fileInput = document.getElementById("analyzeFile");
const textOutput = document.getElementById("textOutput");

const headingsEl = document.getElementById("headingsCount");
const keywordsEl = document.getElementById("keywordsCount");
const wordCountEl = document.getElementById("wordCount");

// Optional: state & month carried from dashboard (future-ready)
const storedState = sessionStorage.getItem("negd-state") || "";
const storedMonth = sessionStorage.getItem("negd-month") || "";

const KEYWORDS = ["digilocker", "integration", "adoption", "progress"];

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  let text = "";

  if (file.name.toLowerCase().endsWith(".pdf")) {
    text = await extractPdfText(file);
  } else if (file.name.toLowerCase().endsWith(".docx")) {
    text = await extractDocxText(file);
  } else {
    alert("Unsupported file type");
    return;
  }

  runRuleBasedAnalysis(text);
});

/* =========================
   PDF EXTRACTION
========================= */

async function extractPdfText(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

  let fullText = "";

  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const pageText = content.items.map(item => item.str).join(" ");
    fullText += pageText + "\n";
  }

  textOutput.textContent = fullText.slice(0, 5000);
  return fullText;
}

/* =========================
   DOCX EXTRACTION
========================= */

async function extractDocxText(file) {
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  textOutput.textContent = result.value.slice(0, 5000);
  return result.value;
}

/* =========================
   RULE-BASED ANALYSIS
========================= */

function runRuleBasedAnalysis(text) {
  if (!text) return;

  const lines = text.split("\n").map(l => l.trim()).filter(Boolean);

  // Simple, explainable heuristics
  const headingsCount = lines.filter(
    l => l.length < 80 && l === l.toUpperCase()
  ).length;

  const words = text.split(/\s+/).filter(Boolean);
  const wordCount = words.length;

  const keywordMatches = KEYWORDS.filter(k =>
    text.toLowerCase().includes(k)
  ).length;
  // Update UI
  headingsEl.textContent = headingsCount;
  keywordsEl.textContent = keywordMatches;
  wordCountEl.textContent = wordCount;
  /* =========================
     PERSIST FOR SUMMARY PAGE
  ========================= */
  sessionStorage.setItem(
    "negd-analysis",
    JSON.stringify({
      text,
      wordCount,
      headingsCount,
      keywordMatches,
      state: storedState,
      month: storedMonth,
      analyzedAt: new Date().toISOString()
    })
  );
}