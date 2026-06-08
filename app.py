import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ── Settings ──────────────────────────────────────────────────────────────────
CHROMA_FOLDER   = "chroma_db"
COLLECTION      = "professor_reviews"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL      = "llama-3.3-70b-versatile"
TOP_K           = 5

# ── Load embedding model and ChromaDB ─────────────────────────────────────────
print("Loading embedding model...")
embedder   = SentenceTransformer(EMBEDDING_MODEL)

print("Connecting to ChromaDB...")
client     = chromadb.PersistentClient(path=CHROMA_FOLDER)
collection = client.get_collection(COLLECTION)

print("Connecting to Groq...")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("✅ All systems ready\n")


# ── Retrieval function ────────────────────────────────────────────────────────
def retrieve(query, k=TOP_K):
    """
    Embed the query and return the top-k most relevant chunks from ChromaDB.
    """
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text":      results["documents"][0][i],
            "professor": results["metadatas"][0][i]["professor"],
            "distance":  round(results["distances"][0][i], 4),
        })
    return chunks


# ── Generation function ───────────────────────────────────────────────────────
def generate_answer(query, chunks):
    """
    Send retrieved chunks to Groq and get a grounded answer.
    The system prompt strictly instructs the model to answer
    only from the provided context — no general knowledge.
    """

    # Build context block from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} — Professor: {chunk['professor']}]\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    # Strict grounding system prompt
    system_prompt = """You are a helpful assistant that answers questions about NYU CS professors.

STRICT RULES:
1. Answer ONLY using the information in the provided sources below.
2. Do NOT use any outside knowledge or make anything up.
3. If the sources do not contain enough information to answer the question, say exactly: "I don't have enough information in my documents to answer that question."
4. Always end your answer with a "Sources:" line listing which professor(s) your answer came from.
5. Keep your answer clear and concise."""

    user_message = f"""Sources:
{context}

Question: {query}

Answer based only on the sources above:"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_message},
        ],
        temperature=0.2,
        max_tokens=500,
    )

    return response.choices[0].message.content


# ── Main ask function ─────────────────────────────────────────────────────────
def ask(query):
    """
    Full pipeline: retrieve chunks → generate grounded answer.
    Returns answer text and a list of source professor names.
    """
    if not query.strip():
        return "Please enter a question.", ""

    # Retrieve
    chunks = retrieve(query, k=TOP_K)

    # Generate
    answer = generate_answer(query, chunks)

    # Build sources list for display
    seen    = set()
    sources = []
    for chunk in chunks:
        if chunk["professor"] not in seen:
            seen.add(chunk["professor"])
            sources.append(f"• {chunk['professor']}")

    sources_text = "\n".join(sources)
    return answer, sources_text


# ── Gradio Interface ──────────────────────────────────────────────────────────
import gradio as gr

with gr.Blocks(title="NYU CS Professor Guide") as demo:

    gr.Markdown("# 🎓 NYU CS Unofficial Professor Guide")
    gr.Markdown("Ask any question about NYU CS professors based on real student reviews.")

    with gr.Row():
        with gr.Column():
            question = gr.Textbox(
                label="Your Question",
                placeholder="e.g. Is Yang Tang accessible outside of class?",
                lines=2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label="Answer",
                lines=10,
                interactive=False,
            )
        with gr.Column(scale=1):
            sources_box = gr.Textbox(
                label="Retrieved From",
                lines=10,
                interactive=False,
            )

    # Example questions
    gr.Examples(
        examples=[
            ["What do students say about Yang Tang's availability outside of class?"],
            ["Is Joanna Klukowska a tough grader?"],
            ["What courses does Alon Hillel-Tuch teach?"],
            ["What is Hilbert Locklear's grading policy on exams?"],
            ["Do students recommend Joe Versoza for Full Stack?"],
        ],
        inputs=question,
    )

    # Wire up button and enter key
    ask_btn.click(fn=ask, inputs=question, outputs=[answer_box, sources_box])
    question.submit(fn=ask, inputs=question, outputs=[answer_box, sources_box])

if __name__ == "__main__":
    demo.launch()
