/* =========================================================
   DASHBOARD LOGIC (PHASE 1 – PROVENANCE SAFE)
   - Handles PDF / DOCX uploads
   - Calendar sync (Header ↔ Filters)
   - Persists State & Month
   - Clean handoff to Analyze page
   - ML / RAG ready
========================================================= */

/* =========================
   DOM REFERENCES
========================= */

const headerDatePicker = document.getElementById("headerDatePicker");
const calendarBtn = document.getElementById("calendarBtn");

const fileInput = document.getElementById("fileUpload");
const stateSelect = document.getElementById("stateSelect");
const datePicker = document.getElementById("datePicker");
const tableBody = document.getElementById("documentsTable");

/* =========================
   IN-MEMORY STORE
========================= */

const documents = [];

/* =========================
   HEADER CALENDAR LOGIC
========================= */

if (calendarBtn && headerDatePicker) {
  calendarBtn.addEventListener("click", () => {
    if (typeof headerDatePicker.showPicker === "function") {
      headerDatePicker.showPicker();
    } else {
      headerDatePicker.focus();
      headerDatePicker.click();
    }
  });

  headerDatePicker.addEventListener("change", () => {
    if (datePicker) datePicker.value = headerDatePicker.value;
  });
}

if (datePicker && headerDatePicker) {
  datePicker.addEventListener("change", () => {
    headerDatePicker.value = datePicker.value;
  });
}

/* =========================
   UTILITIES
========================= */

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function getFileType(fileName) {
  if (fileName.toLowerCase().endsWith(".pdf")) return "PDF";
  if (fileName.toLowerCase().endsWith(".docx")) return "DOCX";
  return "Unknown";
}

/* =========================
   TABLE RENDERING
========================= */

function renderTable() {
  if (!tableBody) return;

  tableBody.innerHTML = "";

  if (documents.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color:#6b7280;">
          No documents uploaded yet
        </td>
      </tr>
    `;
    return;
  }

  documents.forEach((doc, index) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${doc.name}</td>
      <td>${doc.state}</td>
      <td>${formatDate(doc.date)}</td>
      <td>${doc.type}</td>
      <td>${doc.status}</td>
      <td>
        <button class="action-btn" onclick="analyzeDocument(${index})">
          Analyze
        </button>
      </td>
    `;

    tableBody.appendChild(row);
  });
}

/* =========================
   FILE UPLOAD HANDLER
========================= */

if (fileInput) {
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    if (!stateSelect.value) {
      alert("Please select a state before uploading.");
      fileInput.value = "";
      return;
    }

    if (!datePicker.value) {
      alert("Please select a date before uploading.");
      fileInput.value = "";
      return;
    }

    const type = getFileType(file.name);
    if (type === "Unknown") {
      alert("Only PDF and DOCX files are supported.");
      fileInput.value = "";
      return;
    }

    const documentEntry = {
      name: file.name,
      state: stateSelect.value,
      date: datePicker.value,
      type,
      status: "Uploaded",
      file
    };

    documents.push(documentEntry);
    renderTable();
    fileInput.value = "";
  });
}

/* =========================
   ANALYZE HANDOFF
========================= */

function analyzeDocument(index) {
  const doc = documents[index];
  if (!doc) return;

  // Persist provenance (CRITICAL)
  sessionStorage.setItem("negd-state", doc.state);

  // Convert date → YYYY-MM
  const monthValue = doc.date.slice(0, 7);
  sessionStorage.setItem("negd-month", monthValue);

  // Redirect to Analyze page
  window.location.href = "analyze.html";
}

/* =========================
   INITIAL RENDER
========================= */

renderTable();
