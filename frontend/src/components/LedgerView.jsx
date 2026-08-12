import React, { useEffect, useState } from "react";
import { api } from "../api";
import StatusBadge from "./StatusBadge";

/**
 * A simple read-only overlay listing every complaint in the database,
 * newest first (the backend already orders it that way). This is the
 * "QMS Ledger" the Commit button refers to - previously nothing in the
 * UI actually showed it, even though GET /api/complaints existed.
 *
 * Deliberately read-only and non-interactive (no row click / load-into-
 * form) to keep this simple - it's a record viewer, not an editor.
 */
export default function LedgerView({ onClose }) {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .listComplaints()
      .then(setComplaints)
      .catch(() => setError("Could not load the ledger. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="ledger-overlay" onClick={onClose}>
      <div className="ledger-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ledger-header">
          <h2>📋 QMS Ledger</h2>
          <button className="ledger-close-btn" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        {loading && <p className="ledger-status-msg">Loading…</p>}
        {error && <p className="ledger-status-msg ledger-error">{error}</p>}

        {!loading && !error && complaints.length === 0 && (
          <p className="ledger-status-msg">No complaints logged yet.</p>
        )}

        {!loading && !error && complaints.length > 0 && (
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Product</th>
                <th>Batch / Lot</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Logged</th>
              </tr>
            </thead>
            <tbody>
              {complaints.map((c) => (
                <tr key={c.id}>
                  <td>{c.fields.customer_name || "—"}</td>
                  <td>{c.fields.product_name || "—"}</td>
                  <td>{c.fields.batch_lot_number || "—"}</td>
                  <td>{c.fields.severity || "—"}</td>
                  <td>
                    <StatusBadge status={c.status} />
                  </td>
                  <td>{c.created_at ? new Date(c.created_at).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
