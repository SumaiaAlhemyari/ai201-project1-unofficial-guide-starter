import os
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import load_all_documents

# ── Settings ──────────────────────────────────────────────────────────────────
CHROMA_FOLDER  = "chroma_db"        # where ChromaDB saves its data locally
COLLECTION     = "professor_reviews"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── Step 1: Load embedding model ──────────────────────────────────────────────
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("✅ Model loaded\n")

# ── Step 2: Load all chunks from ingest.py ────────────────────────────────────
print("Loading and chunking documents...")
chunks = load_all_documents()
print(f"✅ {len(chunks)} chunks ready\n")

# ── Step 3: Set up ChromaDB ───────────────────────────────────────────────────
print("Setting up ChromaDB...")
client     = chromadb.PersistentClient(path=CHROMA_FOLDER)

# Delete old collection if it exists so we start fresh
try:
    client.delete_collection(COLLECTION)
    print("  (old collection cleared)")
except:
    pass

collection = client.create_collection(COLLECTION)
print("✅ ChromaDB ready\n")

# ── Step 4: Embed and store all chunks ────────────────────────────────────────
print("Embedding chunks and storing in ChromaDB...")
print("This may take 1-2 minutes...\n")

texts      = [c["text"]      for c in chunks]
professors = [c["professor"] for c in chunks]
ids        = [f"chunk_{i}"   for i in range(len(chunks))]

# Embed all chunks at once
embeddings = model.encode(texts, show_progress_bar=True).tolist()

# Store in ChromaDB with metadata
collection.add(
    ids        = ids,
    embeddings = embeddings,
    documents  = texts,
    metadatas  = [{"professor": p} for p in professors],
)

print(f"\n✅ {len(chunks)} chunks stored in ChromaDB\n")

# ── Step 5: Test retrieval with 3 sample queries ──────────────────────────────
print("=" * 60)
print("TESTING RETRIEVAL — 3 SAMPLE QUERIES")
print("=" * 60)

test_queries = [
    "What do students say about Yang Tang's availability outside of class?",
    "Is Joanna Klukowska a tough grader?",
    "What is Hilbert Locklear's grading policy on exams?",
]

def retrieve(query, k=5):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = k,
    )
    chunks_out = []
    for i in range(len(results["documents"][0])):
        chunks_out.append({
            "text":      results["documents"][0][i],
            "professor": results["metadatas"][0][i]["professor"],
            "distance":  round(results["distances"][0][i], 4),
        })
    return chunks_out

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 50)
    results = retrieve(query, k=3)
    for r in results:
        print(f"  Professor : {r['professor']}")
        print(f"  Distance  : {r['distance']}  (lower = more relevant)")
        print(f"  Text      : {r['text'][:200]}")
        print()
