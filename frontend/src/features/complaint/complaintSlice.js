import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api";
import { EMPTY_FIELDS } from "../../formConfig";

// --- Async thunks (one per API call the form cares about) ------------

export const startNewComplaint = createAsyncThunk(
  "complaint/startNew",
  async () => {
    const result = await api.createComplaint();
    return result;
  }
);

export const commitComplaint = createAsyncThunk(
  "complaint/commit",
  async (id) => {
    const result = await api.commitComplaint(id);
    return result;
  }
);

const complaintSlice = createSlice({
  name: "complaint",
  initialState: {
    id: null,
    fields: EMPTY_FIELDS,
    status: "pending_triage", // pending_triage | ready_to_commit | committed
    loading: false,
  },
  reducers: {
    // Called after any Copilot response (extract or correct) to push
    // the new field values + status into the form.
    applyCopilotResult(state, action) {
      state.fields = { ...state.fields, ...action.payload.fields };
      state.status = action.payload.status;
    },
    // Lets the person hand-edit a field directly in the form too -
    // the AI doesn't have to be the only way to change something.
    setField(state, action) {
      const { key, value } = action.payload;
      state.fields[key] = value;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(startNewComplaint.pending, (state) => {
        state.loading = true;
      })
      .addCase(startNewComplaint.fulfilled, (state, action) => {
        state.loading = false;
        state.id = action.payload.id;
        state.fields = { ...EMPTY_FIELDS, ...action.payload.fields };
        state.status = action.payload.status;
      })
      .addCase(commitComplaint.fulfilled, (state, action) => {
        state.status = action.payload.status;
      });
  },
});

export const { applyCopilotResult, setField } = complaintSlice.actions;
export default complaintSlice.reducer;
