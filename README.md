# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system is an unofficial student review guide for computer science professors at New York University. It answers questions about how individual professors actually teach — their availability, grading style, workload, and exam policies — based on real student reviews collected from RateMyProfessors.

This knowledge is valuable because official NYU course listings only show course descriptions, prerequisites, and credentials. They reveal nothing about teaching style, how hard the exams are, how heavy the workload is, or whether students would take the professor again. That information lives scattered across individual reviews written by students, and this guide consolidates it so a student can ask one honest question and get a grounded answer drawn from many reviews at once.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors — Alon Hillel-Tuch (AppSec, Networking, AI Governance) | PDF | documents/Alon Hillel-Tuch.pdf |
| 2 | RateMyProfessors — Cory Plock (Programming Languages) | PDF | documents/Cory Plock.pdf |
| 3 | RateMyProfessors — Douglas Moody (CSO, CS201) | PDF | documents/Douglas Moody.pdf |
| 4 | RateMyProfessors — Gizem Kayar (CS101, CS201) | PDF | documents/Gizem Kayar.pdf |
| 5 | RateMyProfessors — Hilbert Locklear (CS101 Intro Java) | PDF | documents/Hilbert Locklear.pdf |
| 6 | RateMyProfessors — Joanna Klukowska (Data Structures CS102) | PDF | documents/Joanna Klukowska.pdf |
| 7 | RateMyProfessors — Joe Versoza (Full Stack, Databases) | PDF | documents/Joe Versoza.pdf |
| 8 | RateMyProfessors — Joshua Clayton (Intro Programming, Web) | PDF | documents/Joshua Clayton.pdf |
| 9 | RateMyProfessors — Parijat Dube (DSUA301, ML courses) | PDF | documents/Parijat Dube.pdf |
| 10 | RateMyProfessors — Yang Tang (Operating Systems CS202) | PDF | documents/Yang Tang.pdf |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Why these choices fit your documents:**
The documents are short student reviews, typically 2–5 sentences each. A 400-character chunk captures roughly one complete review without merging multiple unrelated opinions into a single vector. The 50-character overlap prevents a key sentence from being cut across a chunk boundary and losing its meaning. Chunks much smaller than this (under ~100 characters) would strip away surrounding context and chunks much larger (over ~800 characters) would blend several distinct reviews together and dilute retrieval accuracy.

Before chunking, each PDF is run through 'pdfplumber' to extract text, then cleaned in 'clean_text()' ([ingest.py](ingest.py)): blank lines are dropped, very short lines (under 15 characters) are removed, and any line matching a noise pattern is discarded. The noise list targets RateMyProfessors boilerplate and ads — e.g. 'advertisement', 'rate compare', 'help site guidelines', 'load more ratings', 'would take again', 'level of difficulty', 'overall quality', 'select a department', and sign-in/copyright lines. Cleaned lines are joined into one string and split with a fixed 400/50 sliding window, chunks of 50 characters or fewer are dropped.

**Final chunk count:** 328 chunks across all 10 documents (Alon Hillel-Tuch 41, Cory Plock 26, Douglas Moody 27, Gizem Kayar 41, Hilbert Locklear 36, Joanna Klukowska 32, Joe Versoza 34, Joshua Clayton 33, Parijat Dube 34, Yang Tang 24).

---

## Embedding Model

**Model used:** 'all-MiniLM-L6-v2', run locally via 'sentence-transformers'. It requires no API key, is fast on CPU, and its 384-dimensional embeddings are well suited to short, single-topic review chunks. Embeddings are stored in a persistent local ChromaDB collection ('professor_reviews') with each chunk tagged with its professor name as metadata. [embed.py](embed.py).

**Production tradeoff reflection:**
If I were deploying this for real users and cost were not a constraint, I would evaluate a hosted model such as OpenAI's 'text-embedding-3-large', which generally has higher accuracy on domain-specific academic text and a much larger context window. The tradeoffs are that it costs per token, requires an API key and network calls, and adds latency on every query — none of which matter for a small local demo but all of which matter at scale. 'all-MiniLM-L6-v2' has a 256-token context limit, which is fine here because each chunk is only ~400 characters, but would be limiting for longer documents. If the guide expanded beyond English-language reviews, I would switch to a multilingual model (e.g. 'paraphrase-multilingual-MiniLM-L12-v2') since the current model is English-only. Latency is negligible for this local setup but would become a real consideration with a hosted model serving many concurrent users.

---

## Grounded Generation

**System prompt grounding instruction:**
Generation uses Groq's 'llama-3.3-70b-versatile' at 'temperature=0.2' ('generate_answer()' in [app.py](app.py)). The retrieved chunks are formatted into a numbered context block — each labeled '[Source N — Professor: <name>]' — and passed to the model with the following system prompt:

> You are a helpful assistant that answers questions about NYU CS professors.
>
> STRICT RULES:
> 1. Answer ONLY using the information in the provided sources below.
> 2. Do NOT use any outside knowledge or make anything up.
> 3. If the sources do not contain enough information to answer the question, say exactly: "I don't have enough information in my documents to answer that question."
> 4. Always end your answer with a "Sources:" line listing which professor(s) your answer came from.
> 5. Keep your answer clear and concise.

Several structural choices reinforce the grounding beyond the prompt text: the low temperature (0.2) discourages the model from improvising, the context is the *only* knowledge the model is given about the question, with the professor name embedded in each source so attribution is traceable, and an explicit fixed refusal string is mandated for out-of-scope questions, which the model does in fact emit (in the evaluation report below, where both an off-topic question and an under-supported in-scope question return the refusal rather than a hallucinated answer).

**How source attribution is surfaced in the response:**
Two ways. First, the model is instructed to end every answer with a 'Sources:' line naming the professor(s) the answer drew from, so attribution appears inline in the answer text. Second, the Gradio UI shows a separate **"Retrieved From"** panel listing the de-duplicated professor names of all top-5 retrieved chunks, built independently in the 'ask()' function — so the user can see which documents the system actually pulled, regardless of what the model wrote.

---

## Evaluation Report

The five planned questions (plus an out-of-scope control) were run through the live system. Responses below are summarized from the model's actual output.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Yang Tang's availability outside of class? | Responds on Discord within minutes, sometimes past midnight / on Friday nights | Very accessible and caring, replies on Discord within minutes, answers as late as 1–3 am, stays up late during office hours | Relevant | Accurate |
| 2 | Is Joanna Klukowska a tough grader? | Yes — heavy/hard quizzes, low averages, curve applied at the end | Yes — described as a "tough grader" across multiple sources | Relevant | Accurate (correct but thinner than expected — see below) |
| 3 | What courses does Alon Hillel-Tuch teach? | Application Security, Computer Networking, AI Governance | Networking and AppSec (Application Security) | Relevant | Partially accurate — missed AI Governance |
| 4 | What is Hilbert Locklear's grading policy on exams? | Binary grading — 50% or 100%, no partial credit | Binary 50/100 grading, a 50 can take a mitigation exam for 82.5, strict curve (0/50/100), test-heavy with pop quizzes | Relevant | Accurate (more detailed than expected) |
| 5 | Do students recommend Joe Versoza for Full Stack? | Mixed — students love him and learn a lot, but lectures are fast and homework is heavy | "I don't have enough information in my documents to answer that question." | Off-target | Inaccurate (failure case — see below) |
| — | (control) What is the capital of France? | Out of scope | "I don't have enough information in my documents to answer that question." | Off-target (as expected) | Correct refusal |

**Retrieval quality:** Relevant for Q1–Q4, off-target for Q5. The control question retrieved only high-distance (≈1.68+) chunks and was correctly refused.
**Response accuracy:** Accurate for Q1, Q2, Q4, partially accurate for Q3, inaccurate for Q5. The grounding mechanism held — no hallucinations were observed, and out-of-scope input produced the mandated refusal.

---

## Failure Case Analysis

**Question that failed:** "Do students recommend Joe Versoza for Full Stack?"

**What the system returned:** "I don't have enough information in my documents to answer that question." — even though there are 34 Joe Versoza chunks in the store and the planned expected answer (a mixed recommendation: students like him and learn a lot, but lectures are fast and homework is heavy) is the kind of sentiment those reviews contain.

**Root cause (tied to a specific pipeline stage):** This is a retrieval failure, not a generation failure. The top-5 chunks returned for this query had notably high distances (0.90–1.08), the worst of any in-scope question in the evaluation. The query is phrased as a yes/no recommendation question ("Do students recommend… for Full Stack?"), but the underlying reviews don't phrase their opinions that way — they describe pace, workload, and how much you learn without using recommendation language. Because 'all-MiniLM-L6-v2' matches on surface semantic similarity, the embedding of the recommendation-framed query landed far from the embeddings of the actual review chunks. The retrieved context was weak enough that the model correctly judged it insufficient and emitted the grounded refusal rather than guessing. So the grounding prompt did its job — the breakdown happened upstream, where retrieval failed to surface the relevant sentiment chunks.

**What you would change to fix it:** (1) Increase 'top_k' (e.g. from 5 to 8–10) so more borderline-relevant Joe Versoza chunks reach the model. (2) Add a query-rewriting/expansion step that reframes recommendation questions into descriptive ones ("Joe Versoza Full Stack workload, pace, what students think") before embedding, so the query vector lands closer to the review vectors. (3) Pre-filter by the professor-name metadata already stored on each chunk when a professor is named in the question, so retrieval is scoped to that professor's reviews instead of competing against all 328 chunks.

---

## Spec Reflection

**One way the spec helped you during implementation:**
Writing the Chunking Strategy and Anticipated Challenges sections in planning.md before any code meant the ingestion pipeline was built with cleaning in mind from the start. I had already identified RateMyProfessors boilerplate (ads, "Rate Compare" banners, "Load More Ratings", site guidelines) as a concrete risk, so 'clean_text()' shipped with an explicit noise-pattern list rather than being bolted on after I noticed garbage in the chunks. Similarly, the spec's decision to tag each chunk with the professor's full name as metadata was made up front, which is exactly what made the per-professor source attribution and the proposed metadata-filtering fix in the failure analysis straightforward.

**One way your implementation diverged from the spec, and why:**
The plan listed the pipeline as "unzip .pdf files, read .txt files" and described stripping a small fixed set of patterns. In implementation I dropped the unzip/.txt path entirely — the documents arrived as plain PDFs, so 'ingest.py' reads them directly with 'pdfplumber' and there is no archive step. I also expanded the noise list well beyond the four patterns named in the plan (adding sign-in, copyright, "would take again", "level of difficulty", etc.) and added two heuristics the spec didn't mention: dropping lines under 15 characters and discarding chunks of 50 characters or fewer, because early test output still contained short navigation fragments that the keyword list alone didn't catch.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Documents and Chunking Strategy sections of planning.md, plus the instruction to write 'ingest.py' that reads each PDF, strips ad/navigation boilerplate, and splits the cleaned text into 400-character chunks with 50-character overlap, tagging each chunk with the professor's name.
- *What it produced:* A pipeline using 'pdfplumber' for extraction, a 'clean_text()' function filtering a list of noise patterns, and a fixed sliding-window 'chunk_text()' that returns dicts of '{text, professor, source}'.
- *What I changed or overrode:* I expanded the noise-pattern list beyond the handful I'd named in the plan (added sign-in/copyright/"would take again"/"level of difficulty"/etc.), and added two filters the generated draft didn't have — dropping lines shorter than 15 characters and skipping chunks of 50 characters or fewer — after seeing short nav fragments survive into early sample output.

**Instance 2**

- *What I gave the AI:* My grounding requirement (answers must come only from retrieved context and must cite the professor as the source) and the pipeline diagram, asking it to write 'app.py' that retrieves the top-5 chunks and passes them to Groq 'llama-3.3-70b-versatile' behind a strict grounding system prompt, with a Gradio interface.
- *What it produced:* A 'retrieve()' / 'generate_answer()' / 'ask()' structure, a numbered '[Source N — Professor: …]' context format, a strict system prompt with a fixed refusal string, and a Gradio Blocks UI with an answer box, a separate "Retrieved From" panel, and example questions.
- *What I changed or overrode:* I set 'temperature=0.2' (rather than a higher default) to further discourage improvisation, and I kept the UI's "Retrieved From" panel computed independently from the de-duplicated retrieved metadata rather than relying solely on the model's self-reported 'Sources:' line — so attribution is shown even if the model's text were to omit it. I verified grounding by running an out-of-scope control question ("What is the capital of France?") and confirming the system emitted the refusal string instead of hallucinating.
