import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { startNewComplaint } from "./features/complaint/complaintSlice";
import ComplaintForm from "./components/ComplaintForm";
import CopilotPanel from "./components/CopilotPanel";
import LedgerView from "./components/LedgerView";

export default function App() {
  const dispatch = useDispatch();
  const [showLedger, setShowLedger] = useState(false);

  // On load, create a fresh draft complaint row in the DB - its id is
  // what every Copilot call attaches its results to.
  useEffect(() => {
    dispatch(startNewComplaint());
  }, [dispatch]);

  return (
    <div className="app-root">
      <div className="top-bar">
        <span className="top-bar-title">AIVOA</span>
        <button className="ledger-toggle-btn" onClick={() => setShowLedger(true)}>
          📋 View QMS Ledger
        </button>
      </div>

      <div className="app-shell">
        <ComplaintForm />
        <CopilotPanel />
      </div>

      {showLedger && <LedgerView onClose={() => setShowLedger(false)} />}
    </div>
  );
}

