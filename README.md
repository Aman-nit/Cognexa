# 🛡️ ClaimShield AI
### Insurance Claim Investigation using Hybrid Semantic Search &amp; RAG

> Cognizant NPN Hackathon — Use Case 8

---

## 📌 Use Case

Insurance companies process thousands of claims every day across health, life, motor, and property products. Before a claim can be approved, rejected, or escalated, investigators have to manually piece together:

- **Claim details** — amount, type, incident facts
- **Policy & customer history** — coverage, tenure, prior claims
- **Business rules** — fraud indicators, underwriting conditions, escalation SOPs

Today this is slow, inconsistent, and locked behind SQL — a business user can't just *ask a question* and get an answer.

### Challenges

| # | Challenge |
|---|---|
| 1 | Data scattered across claims, policy, and insurer systems |
| 2 | Business rules spread across fraud, underwriting, and escalation guidelines |
| 3 | Manual investigation is slow and effort-heavy |
| 4 | Inconsistent conclusions on similar claims |
| 5 | SQL skills needed, limiting business-user self-service |

### Objective

Given a query — a Claim ID, Policy Number, Customer Name, fraud investigation request, or compliance question — retrieve the relevant claim/policy records and business rules **contextually and semantically**, not just by exact keyword match, and return:

- Relevant claim and policy details
- Applicable fraud and compliance rules
- Investigation findings and risk indicators
- Recommended action (Approve / Review / Investigate)
- A natural-language explanation grounded in that evidence

---

## 💡 Proposed Solution — ClaimShield AI

ClaimShield AI is an investigator-facing system that turns a plain-language question into an **evidence-grounded answer**, not a guess.

It works by fusing four retrieval paths — structured data, keyword search, semantic search, and codified business rules — and only lets the LLM speak once every claim it makes can be traced back to a real fact or rule ID. Nothing enters the answer that wasn't retrieved.

**Design principles:**
- 🔎 **Hybrid over single-mode** — SQL alone misses nuance, embeddings alone miss exact IDs. Fuse both.
- 📜 **Rules stay human-editable** — YAML, not hardcoded into prompts, so logic stays auditable.
- 🛡️ **Grounded, not generative** — every sentence the LLM outputs must cite a fact or rule that was actually retrieved.
- 🧑‍⚖️ **Human stays in charge** — the system recommends; it never auto-decides.
- 🔌 **Offline-first** — runs without external services, so nothing breaks on a flaky connection.

---

## 🧩 Tech Stack

<table>
<tr>
<th align="left">Layer</th>
<th align="left">Pick</th>
<th align="left">Why this one</th>
</tr>
<tr>
<td>🗄️ <b>Structured data</b></td>
<td><code>DuckDB</code></td>
<td>Zero-infra, joins claims × customers × policies in one SQL statement</td>
</tr>
<tr>
<td>📜 <b>Rules</b></td>
<td><code>YAML</code> + Python evaluator</td>
<td>Human-readable, editable live to prove logic isn't hardcoded</td>
</tr>
<tr>
<td>🔎 <b>Keyword search</b></td>
<td><code>BM25</code></td>
<td>Catches exact claim IDs and rule codes embeddings can blur</td>
</tr>
<tr>
<td>🧠 <b>Vector store</b></td>
<td><code>FAISS</code> (in-process)</td>
<td>No external service — loads from disk, works fully offline</td>
</tr>
<tr>
<td>🔡 <b>Embeddings</b></td>
<td><code>sentence-transformers</code> (MiniLM / BGE-small)</td>
<td>CPU-only, fast enough to embed the whole corpus in seconds</td>
</tr>
<tr>
<td>🤖 <b>LLM</b></td>
<td><code>Phi-3-mini</code> local + hosted fallback</td>
<td>No single point of failure if local inference or wifi drops</td>
</tr>
<tr>
<td>🔀 <b>Fusion</b></td>
<td>Reciprocal Rank Fusion</td>
<td>Merges SQL / keyword / semantic / rules into one ranked context</td>
</tr>
<tr>
<td>🛡️ <b>Guardrail</b></td>
<td>Citation-validation pass</td>
<td>Strips any claim not backed by retrieved evidence</td>
</tr>
<tr>
<td>⚙️ <b>Backend</b></td>
<td><code>FastAPI</code></td>
<td>Clean, testable routes — independent of the UI</td>
</tr>
<tr>
<td>🖥️ <b>Frontend</b></td>
<td><code>Streamlit</code></td>
<td>Fast to build an investigator-facing evidence &amp; trace view</td>
</tr>
</table>

---

## 🔄 Workflow

```
Investigator Query
        │
        ▼
 Hybrid Retrieval  (DuckDB + BM25 + FAISS + YAML rules)
        │
        ▼
 Reciprocal Rank Fusion → single evidence set
        │
        ▼
 Phi-3 reasoning → grounded, cited draft answer
        │
        ▼
 Guardrail → verifies every citation is real
        │
        ▼
 Streamlit → answer + evidence + recommendation
```

---

## 📁 Project Structure

```
claimshield-ai/
│
├── data/
│   ├── insurance_fraud_detection.xlsx     # raw dataset as given
│   └── claimshield.duckdb                  # built from the xlsx
│
├── rules/
│   └── fraud_rules.yaml                    # rules + semantics in one file for MVP
│
├── index/
│   ├── faiss_index.bin                      # vector index
│   └── bm25_index.pkl                        # keyword index
│
├── backend/
│   ├── main.py                                # FastAPI app + all routes
│   ├── retrieval.py                            # SQL + BM25 + FAISS + rules, one file
│   ├── fusion.py                                # Reciprocal Rank Fusion
│   ├── llm.py                                    # Phi-3 local/fallback + guardrail
│   └── build_index.py                             # one-time setup: xlsx→duckdb, build indexes
│
├── frontend/
│   └── app.py                                       # Streamlit UI
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🎯 Output

For every query, ClaimShield AI returns:

- ✅ Relevant claim & policy facts (from DuckDB)
- ✅ Matched rule IDs with plain-language explanation (from YAML)
- ✅ Risk indicators and financial exposure
- ✅ A recommendation — **Approve / Review / Investigate**
- ✅ Full evidence trace, so every sentence can be clicked back to its source