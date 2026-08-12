import { configureStore } from "@reduxjs/toolkit";
import complaintReducer from "./features/complaint/complaintSlice";
import chatReducer from "./features/chat/chatSlice";

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    chat: chatReducer,
  },
});
