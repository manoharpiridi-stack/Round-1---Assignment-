import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api";
import { BONUS_TOOLS } from "../../formConfig";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Ready to process new complaints. You can paste the raw email from the customer, " +
    "or upload a PDF of the complaint report. I will extract the data and run the initial risk assessment.",
};

// Three ways a message can reach the Copilot - paste text, upload a
// file, or send a correction. All three return the same shape from
// the backend: { reply, fields, status, changed_fields }.

export const sendText = createAsyncThunk(
  "chat/sendText",
  async ({ complaintId, text }) => {
    return api.extractText(complaintId, text);
  }
);

export const sendFile = createAsyncThunk(
  "chat/sendFile",
  async ({ complaintId, file }) => {
    return api.extractFile(complaintId, file);
  }
);

export const sendCorrection = createAsyncThunk(
  "chat/sendCorrection",
  async ({ complaintId, message }) => {
    return api.correct(complaintId, message);
  }
);

// One thunk covers all five bonus features - `tool` is the key from
// BONUS_TOOLS in formConfig.js, which is also how we look up the
// button label and which api.js function to call.
export const runBonusTool = createAsyncThunk(
  "chat/runBonusTool",
  async ({ complaintId, tool }) => {
    const toolDef = BONUS_TOOLS.find((t) => t.key === tool);
    return api[toolDef.apiMethod](complaintId);
  }
);

function addUserMessage(state, content) {
  state.messages.push({ role: "user", content });
}
function addAssistantMessage(state, content) {
  state.messages.push({ role: "assistant", content });
}

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [WELCOME_MESSAGE],
    sending: false,
  },
  reducers: {
    resetChat(state) {
      state.messages = [WELCOME_MESSAGE];
    },
  },
  extraReducers: (builder) => {
    builder
      // --- paste text ---
      .addCase(sendText.pending, (state, action) => {
        state.sending = true;
        addUserMessage(state, action.meta.arg.text);
      })
      .addCase(sendText.fulfilled, (state, action) => {
        state.sending = false;
        addAssistantMessage(state, action.payload.reply);
      })
      .addCase(sendText.rejected, (state) => {
        state.sending = false;
        addAssistantMessage(state, "Something went wrong extracting that. Please try again.");
      })
      // --- upload file ---
      .addCase(sendFile.pending, (state, action) => {
        state.sending = true;
        addUserMessage(state, `[Uploaded file: ${action.meta.arg.file.name}]`);
      })
      .addCase(sendFile.fulfilled, (state, action) => {
        state.sending = false;
        addAssistantMessage(state, action.payload.reply);
      })
      .addCase(sendFile.rejected, (state) => {
        state.sending = false;
        addAssistantMessage(state, "Something went wrong reading that file. Please try again.");
      })
      // --- correction ---
      .addCase(sendCorrection.pending, (state, action) => {
        state.sending = true;
        addUserMessage(state, action.meta.arg.message);
      })
      .addCase(sendCorrection.fulfilled, (state, action) => {
        state.sending = false;
        addAssistantMessage(state, action.payload.reply);
      })
      .addCase(sendCorrection.rejected, (state) => {
        state.sending = false;
        addAssistantMessage(state, "Something went wrong applying that correction. Please try again.");
      })
      // --- bonus AI tools (completeness, root cause, CAPA, summary, duplicates) ---
      .addCase(runBonusTool.pending, (state, action) => {
        state.sending = true;
        const toolDef = BONUS_TOOLS.find((t) => t.key === action.meta.arg.tool);
        addUserMessage(state, toolDef.label);
      })
      .addCase(runBonusTool.fulfilled, (state, action) => {
        state.sending = false;
        addAssistantMessage(state, action.payload.reply);
      })
      .addCase(runBonusTool.rejected, (state) => {
        state.sending = false;
        addAssistantMessage(state, "Something went wrong running that tool. Please try again.");
      });
  },
});

export const { resetChat } = chatSlice.actions;
export default chatSlice.reducer;
