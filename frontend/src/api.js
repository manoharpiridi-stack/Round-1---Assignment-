/**
 * Every HTTP call to the backend lives in this one file. If the API
 * base URL or a route path changes, this is the only place to edit.
 */
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  createComplaint: () =>
    fetch(`${BASE_URL}/api/complaints`, { method: "POST" }).then(handle),

  getComplaint: (id) =>
    fetch(`${BASE_URL}/api/complaints/${id}`).then(handle),

  listComplaints: () =>
    fetch(`${BASE_URL}/api/complaints`).then(handle),

  commitComplaint: (id) =>
    fetch(`${BASE_URL}/api/complaints/${id}/commit`, { method: "POST" }).then(handle),

  extractText: (complaintId, text) =>
    fetch(`${BASE_URL}/api/copilot/extract-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId, text }),
    }).then(handle),

  extractFile: (complaintId, file) => {
    const formData = new FormData();
    formData.append("complaint_id", complaintId);
    formData.append("file", file);
    return fetch(`${BASE_URL}/api/copilot/extract-file`, {
      method: "POST",
      body: formData,
    }).then(handle);
  },

  correct: (complaintId, message) =>
    fetch(`${BASE_URL}/api/copilot/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId, message }),
    }).then(handle),

  // --- Bonus AI features - all just need the complaint id ---
  checkCompleteness: (complaintId) =>
    fetch(`${BASE_URL}/api/copilot/check-completeness`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId }),
    }).then(handle),

  recommendRootCause: (complaintId) =>
    fetch(`${BASE_URL}/api/copilot/root-cause`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId }),
    }).then(handle),

  recommendCapa: (complaintId) =>
    fetch(`${BASE_URL}/api/copilot/capa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId }),
    }).then(handle),

  generateSummary: (complaintId) =>
    fetch(`${BASE_URL}/api/copilot/summary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId }),
    }).then(handle),

  detectDuplicates: (complaintId) =>
    fetch(`${BASE_URL}/api/copilot/duplicates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_id: complaintId }),
    }).then(handle),
};
