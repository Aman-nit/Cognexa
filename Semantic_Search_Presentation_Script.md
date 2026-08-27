# Cognexa — Semantic Search: 5-Minute Presentation Script

**Your role:** Semantic Search (business rules retrieval)
**Total time:** ~5 minutes
**Tone:** Simple, confident, no jargon dumping — explain like you're teaching a smart friend who's never seen the code.

---

## 0:00 – 0:30 | Opening (Set the stage)

> "Hi, I'm [Your Name], and I built the **semantic search** part of Cognexa — our AI insurance claims assistant.
>
> Here's the problem we solved: an insurance company doesn't just store *data* — like claim amounts and policy numbers — it also has *rules*. Things like 'a claim over ₹50,000 must be manually investigated,' or 'if fraud was reported within 30 days, escalate it.'
>
> These rules live in documents, not in a database. So if someone asks 'What claims need manual investigation?' — a normal database query can't answer that. That's exactly what my part of the system solves."

---

## 0:30 – 1:30 | What is Semantic Search? (The core idea)

> "Semantic search means: instead of matching *exact words*, we match *meaning*.
>
> Think of it like this — if you search 'high value claim rule' and the document says 'claims above a certain threshold require review,' a normal keyword search would miss that, because the words don't match. But semantic search understands they *mean* the same thing.
>
> We do this using something called **embeddings**. An embedding turns a sentence into a list of numbers — a kind of mathematical fingerprint of its meaning. Two sentences that mean similar things get numbers that are close together, even if the words are completely different."

*(Optional hand gesture: two dots close together on an imaginary graph)*

---

## 1:30 – 3:00 | How I Built It (Walk through the pipeline)

> "Here's exactly what happens, step by step:
>
> **Step 1 — The Knowledge Base.**
> All our business rules — things like BR006, investigation categories, claim thresholds — are stored in a YAML file. Think of YAML as a clean, structured text file, like a well-organized notebook of rules.
>
> **Step 2 — Turning Rules into Passages.**
> I convert every rule, every question pattern, and every investigation category into a readable paragraph — a 'passage.' So instead of raw structured data, we get natural sentences the AI can actually understand.
>
> **Step 3 — Creating Embeddings.**
> I use a small, fast embedding model called `all-MiniLM-L6-v2`. It reads every passage *once*, ahead of time, and converts it into that numeric fingerprint I mentioned. This happens once when the app starts — so it's fast at query time.
>
> **Step 4 — The Actual Search.**
> When a user asks a question, I convert their *question* into the same kind of fingerprint, then compare it against every rule's fingerprint using something called **cosine similarity** — basically a way to measure 'how close are these two meanings.'
>
> **Step 5 — Filtering for Quality.**
> I only keep results that pass a similarity threshold — 0.30 in our case — so we don't return irrelevant rules just to fill space. Then I return the top 5 best matches."

---

## 3:00 – 3:45 | Why This Matters (The judge-impressing part)

> "Here's the key insight that separates us from a basic chatbot: **we never let the AI invent business rules.**
>
> The AI's job isn't to *guess* what a rule says — it's to *retrieve the actual rule text* and hand it to the final answer model as evidence. This means:
> - No hallucinated policies
> - Every answer is traceable back to a real rule
> - If nothing matches well, we simply say 'no relevant business rule found' instead of making something up"

*(This is a strong differentiator — say it slowly and clearly.)*

---

## 3:45 – 4:20 | How It Fits Into the Bigger System

> "My semantic search doesn't work alone — it's one of three paths in Cognexa:
> - **SQL path** — for factual database questions like 'show claims above ₹50,000'
> - **Semantic path** — mine — for policy and rule questions like 'what is the high-value claim rule'
> - **Hybrid path** — when a question needs *both*, like 'should claim 5 be investigated according to the business rules?'
>
> In hybrid mode, my semantic search runs *alongside* the SQL search. Both results get combined and sent to a final AI model, which writes one clear, grounded answer — using real data *and* real rules, never guessing."

---

## 4:20 – 4:50 | The Important Nuance (Shows depth of understanding)

> "One subtle but important design decision: our dataset has a column called `fraud_reported`. It's tempting to think that's the same as 'this claim needs investigation' — but it's not.
>
> `fraud_reported = 'Y'` is just a historical label from the original dataset. It is *not* a live fraud decision made by Cognexa. Whether a claim needs investigation comes from our **business rules**, which my semantic search retrieves separately. Keeping these two concepts separate is exactly why we need a dedicated rules-retrieval system instead of just querying a database column."

---

## 4:50 – 5:00 | Closing Line

> "So in short — my part of Cognexa turns unstructured policy documents into something the AI can actually *understand and retrieve accurately*, so every answer about business rules is grounded in real, traceable evidence, not guesswork."

---

# Presentation Tips

1. **Practice the pause after "meaning, not words."** That's your hook line — let it land before moving on.
2. **Don't read the script word-for-word.** Memorize the *structure* (5 steps), not the sentences — sounding natural beats sounding rehearsed.
3. **Use your hands for the embeddings idea.** A simple gesture ("close together" vs "far apart") makes an abstract concept feel intuitive fast.
4. **Anticipate the obvious judge question:** *"Why not just use keyword search?"* Answer ready: "Because insurance rules use varied wording — 'manual investigation,' 'escalation,' 'review required' — keyword search would miss half of them."
5. **Anticipate a second question:** *"What if no rule matches the question?"* Answer ready: "We return nothing rather than a wrong rule — the 0.30 similarity threshold acts as a safety filter."
6. **Keep eye contact during the fraud_reported nuance slide** — that's your "we thought about this carefully" moment; judges remember teams who show they questioned their own data.
7. **If time runs short, cut from the middle, not the ends.** Keep your opening hook and your closing line intact — those are what judges remember.
8. **Speak slightly slower than feels natural.** Under pressure, most people speed up without noticing — slowing down makes you sound more confident, not less.
