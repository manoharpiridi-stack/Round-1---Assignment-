import React from "react";

const LABELS = {
  pending_triage: "Pending Triage",
  ready_to_commit: "Ready to Commit",
  committed: "Committed",
};

export default function StatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{LABELS[status] || status}</span>;
}
