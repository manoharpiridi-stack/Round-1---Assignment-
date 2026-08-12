/**
 * Defines every field on the "Log Customer Complaint" form, grouped
 * into the same 4 sections shown in the demo video.
 *
 * TO ADD A FIELD: add one object to the right section below. It will
 * automatically show up in the form (ComplaintForm.jsx just maps over
 * this array). Remember to also add the matching key on the backend
 * (models.py, schemas.py, agent.py FORM_FIELDS) so the AI can fill it.
 */
export const FORM_SECTIONS = [
  {
    title: "1. Origin & Customer Details",
    fields: [
      { key: "complaint_source", label: "Complaint Source", type: "text" },
      { key: "customer_name", label: "Customer Name", type: "text" },
    ],
  },
  {
    title: "2. Product & Batch Identification",
    fields: [
      { key: "product_name", label: "Product Name", type: "text" },
      { key: "product_strength", label: "Product Strength/Grade", type: "text" },
      { key: "batch_lot_number", label: "Batch / Lot Number", type: "text" },
      { key: "affected_quantity", label: "Affected Quantity", type: "text" },
      { key: "manufacturing_date", label: "Manufacturing Date", type: "text" },
      { key: "expiry_date", label: "Expiry Date", type: "text" },
    ],
  },
  {
    title: "3. Facility & Material Impact",
    fields: [
      {
        key: "originating_site_block",
        label: "Originating Site Block",
        type: "select",
        options: ["", "Manufacturing", "Packaging", "Warehouse", "QC", "Distribution"],
      },
      { key: "impacted_npm", label: "Impacted Non-Product Materials (NPM)", type: "text" },
    ],
  },
  {
    title: "4. Defect Analysis",
    fields: [
      { key: "complaint_category", label: "Complaint Category", type: "text" },
      { key: "complaint_description", label: "Complaint Description", type: "textarea" },
    ],
  },
];

export const EMPTY_FIELDS = FORM_SECTIONS.reduce((acc, section) => {
  section.fields.forEach((f) => (acc[f.key] = ""));
  return acc;
}, {
  severity: "",
  suggested_next_action: "",
  initial_risk_assessment: "",
  completeness_note: "",
  root_cause_note: "",
  capa_recommendation: "",
  ai_summary: "",
  duplicate_warning: "",
});

// The five optional "bonus" AI features. Each maps to one backend
// endpoint (see api.js) and one read-only field on the form
// (ComplaintForm.jsx renders these under "5. AI Insights").
export const BONUS_TOOLS = [
  { key: "completeness", label: "🔍 Check Completeness", field: "completeness_note", apiMethod: "checkCompleteness" },
  { key: "root_cause", label: "🧭 Suggest Root Cause", field: "root_cause_note", apiMethod: "recommendRootCause" },
  { key: "capa", label: "🛠️ Recommend CAPA", field: "capa_recommendation", apiMethod: "recommendCapa" },
  { key: "summary", label: "📝 Summarize", field: "ai_summary", apiMethod: "generateSummary" },
  { key: "duplicate", label: "🔁 Check Duplicates", field: "duplicate_warning", apiMethod: "detectDuplicates" },
];
