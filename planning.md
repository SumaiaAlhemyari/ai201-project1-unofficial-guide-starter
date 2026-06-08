# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This is an unofficial student review guide for computer science professors at New York University. The guide is helpful because it offers honest opinions on each professor's teaching style based on real student experiences, rather than just their credentials or qualifications. Official course listings only show course descriptions and prerequisites — they do not reveal how professors teach, how hard exams are, or whether students would take them again.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Alon Hillel-Tuch | RateMyProfessors reviews — AppSec, Networking, AI Governance | Alon_HillelTuch.pdf |
| 2 | Cory Plock | RateMyProfessors reviews — Programming Languages | Cory_Plock.pdf |
| 3 | Douglas Moody | RateMyProfessors reviews — CSO, CS201 | Douglas_Moody.pdf |
| 4 | Gizem Kayar | RateMyProfessors reviews — CS101, CS201 | Gizem_Kayar.pdf |
| 5 | Hilbert Locklear | RateMyProfessors reviews — CS101 Intro Java | Hilbert_Locklear.pdf |
| 6 | Joanna Klukowska | RateMyProfessors reviews — Data Structures CS102 | Joanna_Klukowska.pdf |
| 7 | Joe Versoza | RateMyProfessors reviews — Full Stack, Databases | Joe_Versoza.pdf |
| 8 | Joshua Clayton | RateMyProfessors reviews — Intro Programming, Web | Joshua_Clayton.pdf |
| 9 | Parijat Dube | RateMyProfessors reviews — DSUA301, ML courses | Parijat_Dube.pdf |
| 10 | Yang Tang | RateMyProfessors reviews — Operating Systems CS202 | Yang_Tang.pdf |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Reasoning:** The documents are short student reviews, typically 2 to 5 sentences each. A 400-character chunk captures roughly one complete review without merging multiple opinions together. Overlap of 50 characters prevents a key sentence from being cut across two chunks and losing its meaning. Chunks that are too small (under 100 characters) would lose context; chunks that are too large (over 800 characters) would mix unrelated reviews and dilute retrieval accuracy.

---

## Retrieval Approach

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers (runs locally, no API key needed)

**Top-k:** 5

**Production tradeoff reflection:** For a production system I would consider text-embedding-3-large from OpenAI for higher accuracy on domain-specific academic text, but it has per-token cost and requires an API key. all-MiniLM-L6-v2 is fast and free but has a 256-token context limit, which is fine for short reviews. A multilingual model would be needed if expanding beyond English reviews. Latency is not a concern for this local setup but would matter at scale.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Yang Tang's availability outside of class? | Students report he responds on Discord within minutes, sometimes past midnight and on Friday nights |
| 2 | Is Joanna Klukowska a tough grader? | Yes — quizzes are heavily weighted and hard, final averages are low, but she applies a curve at the end |
| 3 | What courses does Alon Hillel-Tuch teach? | Application Security, Computer Networking, and AI Governance at NYU |
| 4 | What is Hilbert Locklear's grading policy on exams? | Binary grading — you get either 50% or 100%, no partial credit on midterms or final |
| 5 | Do students recommend Joe Versoza for Full Stack? | Mixed — students love him as a person and say you learn a lot, but warn lectures are very fast and homework is extremely heavy |

---

## Anticipated Challenges

1. Ad text and navigation boilerplate in the source files (footers, "Rate Compare" banners, "Advertisement" lines, site guidelines text) may end up in chunks and confuse retrieval. The ingestion pipeline must strip these patterns out carefully before chunking or the vector store will contain noise that pulls retrieval off-target.

2. Multiple reviews mention professors by first name only (e.g., "Prof Alon") rather than their full name, which could cause the embedding model to miss relevant chunks when a user queries by full name. Each chunk will be tagged with the professor's full name as metadata to help attribution, but retrieval itself may still miss nickname-only mentions.

---

## Architecture

```
[1] Document Ingestion          [2] Chunking               [3] Embedding + Vector Store
    unzip .pdf files,    -->        400 char chunks,   -->     all-MiniLM-L6-v2
    read .txt files,                50 char overlap,           + ChromaDB
    clean ad/nav text               per professor              store with prof name metadata

[4] Retrieval                                [5] Generation
    ChromaDB semantic search,    -->             Groq llama-3.3-70b-versatile
    top-5 chunks returned                        grounded system prompt
    with professor metadata                      answer + source attribution
                                                 Gradio web interface
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I will give Claude this planning.md Documents section and Chunking Strategy section and ask it to write ingest.py that unzips each .pdf file, reads all .txt files inside, strips lines matching ad and nav patterns (Advertisement, Rate Compare, Help Site Guidelines, Load More Ratings), and splits the cleaned text into 400-character chunks with 50-character overlap. I will verify the output by printing 5 random chunks and checking they look like complete review sentences with no boilerplate.

**Milestone 4 — Embedding and retrieval:**
I will give Claude my Retrieval Approach section and the pipeline diagram above and ask it to write embed.py that loads chunks from ingest.py, embeds them with all-MiniLM-L6-v2 via sentence-transformers, stores them in ChromaDB with the professor name as metadata, and exposes a retrieve(query, k=5) function. I will test it manually with 3 of my 5 evaluation questions and confirm the returned chunks are visibly relevant before moving on.

**Milestone 5 — Generation and interface:**
I will give Claude my grounding requirement (answers must come only from retrieved context, must cite professor name as source) and ask it to write app.py using Gradio that takes a user query, calls retrieve(), passes the top-5 chunks to Groq llama-3.3-70b-versatile with a strict grounding system prompt, and returns the answer plus a list of source professor names. I will test with an out-of-scope question to verify the system says it does not have enough information rather than hallucinating an answer.
