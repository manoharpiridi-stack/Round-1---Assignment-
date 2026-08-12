import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { setField, commitComplaint, startNewComplaint } from "../features/complaint/complaintSlice";
import { resetChat } from "../features/chat/chatSlice";
import { FORM_SECTIONS, BONUS_TOOLS } from "../formConfig";
import StatusBadge from "./StatusBadge";

function Field({ field, value, onChange, disabled }) {
  const placeholder = value ? undefined : "Awaiting AI extraction...";

  if (field.type === "select") {
    return (
      <select value={value} disabled={disabled} onChange={(e) => onChange(field.key, e.target.value)}>
        {field.options.map((opt) => (
          <option key={opt} value={opt}>
            {opt || "Awaiting AI classification..."}
          </option>
        ))}
      </select>
    );
  }

  if (field.type === "textarea") {
    return (
      <textarea
        rows={3}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(e) => onChange(field.key, e.target.value)}
      />
    );
  }

  return (
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      disabled={disabled}
      onChange={(e) => onChange(field.key, e.target.value)}
    />
  );
}

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const { id, fields, status, loading } = useSelector((s) => s.complaint);
  const { sending } = useSelector((s) => s.chat);

  const handleChange = (key, value) => dispatch(setField({ key, value }));
  const handleCommit = () => dispatch(commitComplaint(id));

  // Once committed, the record represents a closed QMS entry - lock
  // every field so it can't be silently edited after the fact. (There's
  // currently no "re-open" or "save edits" endpoint post-commit anyway,
  // so this also avoids edits that would have nowhere to actually save.)
  const isCommitted = status === "committed";

  // Starts a genuinely fresh complaint: a new DB row (so old AI Insights,
  // risk assessment, and form fields don't carry over) plus a fresh chat
  // thread. Without this, pasting a new complaint's text just re-extracts
  // into the SAME row, which is why old bonus-feature notes used to stick
  // around - the backend always returns the complete current row.
  const handleNewComplaint = () => {
    dispatch(startNewComplaint());
    dispatch(resetChat());
  };

  return (
    <div className="panel form-panel">
      <div className="form-header">
        <div>
          <h1>Log Customer Complaint</h1>
          <p className="subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <StatusBadge status={status} />
      </div>

      <button
        className="new-complaint-btn"
        onClick={handleNewComplaint}
        disabled={sending}
      >
        + New Complaint
      </button>

      {loading && <p>Starting new complaint...</p>}

      {isCommitted && (
        <p className="readonly-banner">
          🔒 This complaint has been committed to the QMS Ledger and is now read-only.
        </p>
      )}

      {FORM_SECTIONS.map((section) => (
        <div className="form-section" key={section.title}>
          <h3>{section.title}</h3>
          <div className="field-grid">
            {section.fields.map((field) => (
              <div className="field" key={field.key}>
                <label>{field.label}</label>
                <Field
                  field={field}
                  value={fields[field.key] || ""}
                  onChange={handleChange}
                  disabled={isCommitted}
                />
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* AI Copilot Risk Assessment - only meaningful once the AI has run */}
      {(fields.severity || fields.suggested_next_action || fields.initial_risk_assessment) && (
        <div className="risk-box">
          <h3>🛡️ AI Copilot Risk Assessment</h3>
          <div className="field-grid">
            <div className="field">
              <label>Severity (Suggested)</label>
              <input
                type="text"
                value={fields.severity || ""}
                disabled={isCommitted}
                onChange={(e) => handleChange("severity", e.target.value)}
              />
            </div>
            <div className="field">
              <label>Suggested Next Action</label>
              <input
                type="text"
                value={fields.suggested_next_action || ""}
                disabled={isCommitted}
                onChange={(e) => handleChange("suggested_next_action", e.target.value)}
              />
            </div>
          </div>
          <div className="field">
            <label>Initial Risk Assessment</label>
            <textarea
              rows={2}
              value={fields.initial_risk_assessment || ""}
              disabled={isCommitted}
              onChange={(e) => handleChange("initial_risk_assessment", e.target.value)}
            />
          </div>
        </div>
      )}

      {/* AI Insights - the 5 optional bonus features, one field each.
          Only shown once at least one has actually produced output,
          so a fresh form isn't cluttered with empty boxes. */}
      {BONUS_TOOLS.some((tool) => fields[tool.field]) && (
        <div className="insights-box">
          <h3>✨ AI Insights (Bonus Features)</h3>
          {BONUS_TOOLS.map((tool) =>
            fields[tool.field] ? (
              <div className="field" key={tool.key}>
                <label>{tool.label.replace(/^\S+\s/, "")}</label>
                <textarea
                  rows={2}
                  value={fields[tool.field] || ""}
                  disabled={isCommitted}
                  onChange={(e) => handleChange(tool.field, e.target.value)}
                />
              </div>
            ) : null
          )}
        </div>
      )}

      <button
        className="commit-btn"
        disabled={status !== "ready_to_commit"}
        onClick={handleCommit}
      >
        {status === "committed" ? "✓ Committed to QMS Ledger" : "Commit to QMS Ledger"}
      </button>
    </div>
  );
}
