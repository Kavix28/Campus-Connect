# Knowledge Base Security & RAG Fix Summary

## 🛠️ Issues Resolved
1.  **Internal Policy Leakage**: The chatbot was incorrectly retrieving internal employee policies (e.g., Expense Reimbursement) when asked about customer returns.
2.  **Source Leakage**: File names like `Oudience.pdf` were being exposed in conversation responses.
3.  **Lack of Domain Constraints**: General similarity search was too broad, failing to distinguish between employee and customer domains.

## 🚀 Implemented Fixes

### 1. Strict Intent Binding (`intent_handler.py`)
- Created a dedicated `return_policy` intent to catch queries like "what is your return policy" or "how to return".
- Implemented `handle_return_policy`, which returns a verified, customer-facing response detailing the 30-day window, refund timeline, and exchange rules.
- This ensures the return policy is **always** answered correctly without relying on ambiguous semantic search.

### 2. Policy Domain Filtering (`app.py`)
- Implemented a **filtering layer** for the RAG system. Before any similarity search, all internal/employee-only chunks (identified by keywords like *probation*, *reimbursement*, *offboarding*, etc.) are strictly excluded.
- The system now only "sees" customer-facing content for general queries.

### 3. Internal Query Safeguards (`app.py`)
- Added a proactive blocking list for internal topics. If a user asks about *reimbursements*, *stipends*, or *internal IT support*, the bot now politely directs them to the internal HR portal instead of attempting to answer.

### 4. Source Leak Prevention (`app.py`)
- Removed all logic that appended `(Source: filename.pdf)` to responses.
- The chatbot now speaks exclusively as the official company assistant without exposing the underlying document structure.

### 5. KB Result Validation (`app.py`)
- Added a validation step for RAG results. Any retrieved context is checked for internal keywords and customer-relevance before being used. If the result is deemed internal, a safe fallback is used instead of leaking data.

## ✅ Verification
- **Test Query**: "what is your return policy" → **Result**: Correct 30-day policy explained. No source leak.
- **Test Query**: "can employees claim reimbursements?" → **Result**: Politeness block ("I only have info on customer policies").
- **Test Query**: "tell me about Oudience.pdf" → **Result**: General assistance provided without confirming file existence.
