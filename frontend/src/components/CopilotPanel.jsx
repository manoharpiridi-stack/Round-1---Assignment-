import React, { useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendText, sendFile, sendCorrection, runBonusTool } from "../features/chat/chatSlice";
import { applyCopilotResult } from "../features/complaint/complaintSlice";
import { BONUS_TOOLS } from "../formConfig";

export default function CopilotPanel() {
  const dispatch = useDispatch();
  const { messages, sending } = useSelector((s) => s.chat);
  const complaintId = useSelector((s) => s.complaint.id);
  const complaintStatus = useSelector((s) => s.complaint.status);
  const [input, setInput] = useState("");
  const fileInputRef = useRef(null);

  // Every one of these handlers does the same two things:
  //   1. fire the chat thunk (adds the chat bubble + calls the API)
  //   2. push the returned fields/status into the form via
  //      applyCopilotResult, so the two panels stay in sync.

  const handleSendText = async () => {
    if (!input.trim() || !complaintId) return;
    const text = input;
    setInput("");
    const result = await dispatch(sendText({ complaintId, text })).unwrap();
    dispatch(applyCopilotResult(result));
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file || !complaintId) return;
    const result = await dispatch(sendFile({ complaintId, file })).unwrap();
    dispatch(applyCopilotResult(result));
    e.target.value = "";
  };

  // A message is treated as a "correction" instead of a fresh
  // extraction once the copilot has already produced a reply -
  // i.e. there's more than just the welcome message in the thread.
  const isFollowUp = messages.length > 1;

  const handleSend = async () => {
    if (!input.trim() || !complaintId) return;
    if (!isFollowUp) return handleSendText();
    const message = input;
    setInput("");
    const result = await dispatch(sendCorrection({ complaintId, message })).unwrap();
    dispatch(applyCopilotResult(result));
  };

  const handleBonusTool = async (toolKey) => {
    if (!complaintId || sending) return;
    const result = await dispatch(runBonusTool({ complaintId, tool: toolKey })).unwrap();
    dispatch(applyCopilotResult(result));
  };

  // The bonus tools act on fields that exist once a complaint has
  // been extracted at least once - no point offering them on a blank
  // form. They're also locked once committed, same reasoning as the
  // read-only form fields: a committed record is a closed QMS entry.
  const isCommitted = complaintStatus === "committed";
  const bonusToolsEnabled = complaintStatus !== "pending_triage" && !isCommitted && !sending;
  const chatLocked = isCommitted || sending;

  return (
    <div className="panel copilot-panel">
      <div className="copilot-header">
        <h2>🧪 AIVOA Copilot</h2>
        <p className="subtitle">Drop complaint files or paste text below.</p>
      </div>

      <div className="chat-thread">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-${m.role}`}>
            {m.content}
          </div>
        ))}
        {sending && <div className="chat-bubble chat-assistant chat-pending">Thinking...</div>}
      </div>

      <div className="bonus-tools-row">
        {BONUS_TOOLS.map((tool) => (
          <button
            key={tool.key}
            className="bonus-tool-btn"
            onClick={() => handleBonusTool(tool.key)}
            disabled={!bonusToolsEnabled}
            title={tool.label}
          >
            {tool.label}
          </button>
        ))}
      </div>

      <div className="chat-input-row">
        <button
          className="attach-btn"
          title="Upload complaint PDF"
          onClick={() => fileInputRef.current.click()}
          disabled={chatLocked}
        >
          📎
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
        <input
          type="text"
          placeholder={isCommitted ? "This complaint is committed and read-only." : "Type a message or paste a complaint..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={chatLocked}
        />
        <button className="send-btn" onClick={handleSend} disabled={chatLocked}>
          ➤
        </button>
      </div>
      <p className="powered-by">POWERED BY LANGGRAPH</p>
    </div>
  );
}
