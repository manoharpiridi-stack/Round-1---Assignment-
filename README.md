# AIVOA — AI Customer Complaint Management System

A working, deliberately-simple implementation of the AIVOA internship assignment:
paste or upload a pharma complaint -> an AI Copilot (LangGraph + Groq) extracts
structured fields into a QMS-style form -> you review/correct via chat -> commit
to the ledger.

## Stack (matches the assignment)
- **Frontend:** React + Redux Toolkit, plain CSS (no UI framework)
- **Backend:** FastAPI
- **AI Agent:** LangGraph (4-node graph, see `backend/app/agent.py`)
- **LLM:** Groq (`gemma2-9b-it` for extraction, `llama-3.3-70b-versatile` for risk assessment)
- **Database:** Postgres (swap to MySQL with one line — see `.env.example`)

## Project layout
```
backend/
  app/
    main.py          FastAPI app + CORS + table creation
    config.py         <-- all the settings you'd tweak live here
    database.py        SQLAlchemy engine/session
    models.py           the Complaint table
    schemas.py           request/response JSON shapes
    agent.py              *** the LangGraph graph — start here ***
    groq_client.py         thin wrapper around Groq's chat API
    pdf_utils.py             PDF text extraction (no OCR needed)
    routers/
      complaints.py           CRUD: create/list/get/commit
      copilot.py                extract-text / extract-file / correct
  requirements.txt
  .env.example
frontend/
  src/
    formConfig.js      <-- all the form fields live here
    store.js             Redux store
    api.js                 every backend call, in one place
    features/complaint/    form state slice
    features/chat/           chat state slice
    components/
      ComplaintForm.jsx        left panel
      CopilotPanel.jsx          right panel (chat + upload)
      StatusBadge.jsx
    App.jsx
    index.css                    all styling, one file
```

## Running it locally

### 1. Database
Create a Postgres database called `aivoa` (or point `DATABASE_URL` at
whatever you already have — MySQL works too, just change the URL and
add `pymysql`/`mysqlclient` to requirements.txt instead of `psycopg2-binary`).

```bash
createdb aivoa
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste in your GROQ_API_KEY (free at https://console.groq.com)
uvicorn app.main:app --reload
```
Backend now runs at http://localhost:8000. Tables are created automatically
on first run. Try http://localhost:8000/docs for interactive API docs.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173.

### 4. Try it
1. Open the app — a blank complaint form + Copilot chat panel appear.
2. Paste something like: *"Apollo Pharmacy reported discolored capsules in
   Amoxicillin Capsules 500mg. Batch AMX240602. Manufacturing date March 2026.
   Expiry Feb 2028."*
3. Watch the form fill in + the AI risk assessment appear.
4. Type a correction like *"actually the batch number is AMX999"* — only that
   field updates.
5. Or click 📎 and upload a PDF complaint instead of pasting text.
6. Try the bonus AI tool buttons above the chat input (🔍 🧭 🛠️ 📝 🔁) — each
   fills in one box under "AI Insights" on the form.
7. Click **Commit to QMS Ledger**.

## Bonus AI features (all optional per the assignment)

Five extra buttons sit above the chat input. Each one calls its own backend
endpoint, which runs a dedicated LangGraph node, and writes its result into
one field under the form's **"AI Insights"** section:

| Button | Endpoint | Graph node | How it works |
|---|---|---|---|
| 🔍 Check Completeness | `/api/copilot/check-completeness` | `check_completeness` | Rule-based (no LLM) — just checks which `FORM_FIELDS` are still blank. |
| 🧭 Suggest Root Cause | `/api/copilot/root-cause` | `recommend_root_cause` | LLM call — investigative note on likely cause + what evidence would confirm it. |
| 🛠️ Recommend CAPA | `/api/copilot/capa` | `recommend_capa` | LLM call — one corrective + one preventive action. |
| 📝 Summarize | `/api/copilot/summary` | `generate_summary` | LLM call — a short formal QMS-record summary. |
| 🔁 Check Duplicates | `/api/copilot/duplicates` | `detect_duplicates` | Rule-based (no LLM) — flags an exact batch/lot match, or a same-product-and-category match, against every other complaint in the DB. |

All five hang directly off `START` in the graph and skip `assess_risk` —
see the diagram at the top of `agent.py` for the full picture.

## How to extend it
- **Add a form field:** edit `frontend/src/formConfig.js` (UI) +
  `backend/app/models.py`, `schemas.py`, and `FORM_FIELDS` in `agent.py`
  (so the AI knows to extract it).
- **Add another bonus AI feature:** follow the same recipe as the five
  already there — one node function in `agent.py` (rule-based or LLM-based),
  one entry in `_ROUTES`, one `graph.add_edge("your_node", "compose_reply")`,
  one line in `compose_reply()`'s if/elif for the reply text, one endpoint in
  `routers/copilot.py`, one column in `models.py`/`schemas.py`, and one entry
  in `BONUS_TOOLS` in `frontend/src/formConfig.js`. Every layer follows the
  same pattern, so it's mostly copy-adjust-paste.
- **Swap the LLM:** change `EXTRACTION_MODEL` / `RISK_MODEL` in `.env`.
- **Swap Postgres for MySQL:** change `DATABASE_URL` in `.env` and swap
  `psycopg2-binary` for `pymysql` in `requirements.txt`.


