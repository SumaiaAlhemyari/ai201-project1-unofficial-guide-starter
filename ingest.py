import os
import pdfplumber

# ── Settings ──────────────────────────────────────────────────────────────────
DOCUMENTS_FOLDER = "documents"
CHUNK_SIZE       = 400
CHUNK_OVERLAP    = 50

# Lines containing these words will be removed (ads, nav, boilerplate)
NOISE_PATTERNS = [
    "advertisement",
    "rate compare",
    "help site guidelines",
    "load more ratings",
    "sign in",
    "sign up",
    "log in",
    "copyright",
    "all rights reserved",
    "ratemyprofessors",
    "add a professor",
    "compare professors",
    "select a department",
    "overall quality",
    "level of difficulty",
    "would take again",
    "check out similar",
]

# ── Step 1: Extract text from a real PDF ──────────────────────────────────────
def extract_text_from_pdf(pdf_path):
    """
    Use pdfplumber to extract text from each page of a real PDF.
    """
    text_parts = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
    except Exception as e:
        print(f"  ❌  Error reading {os.path.basename(pdf_path)}: {e}")
        return ""

    return "\n\n".join(text_parts)


# ── Step 2: Clean the text ────────────────────────────────────────────────────
def clean_text(text):
    """
    Remove boilerplate lines, ads, and navigation text.
    Keep only real review content.
    """
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        line_stripped = line.strip()

        if not line_stripped:
            continue

        line_lower = line_stripped.lower()
        if any(pattern in line_lower for pattern in NOISE_PATTERNS):
            continue

        if len(line_stripped) < 15:
            continue

        cleaned.append(line_stripped)

    return " ".join(cleaned)


# ── Step 3: Split text into chunks ───────────────────────────────────────────
def chunk_text(text, professor_name):
    """
    Split cleaned text into chunks of CHUNK_SIZE characters
    with CHUNK_OVERLAP characters of overlap.
    """
    chunks = []
    start  = 0

    while start < len(text):
        end   = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if len(chunk) > 50:
            chunks.append({
                "text":      chunk,
                "professor": professor_name,
                "source":    professor_name,
            })

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ── Step 4: Process all PDFs ─────────────────────────────────────────────────
def load_all_documents():
    """
    Loop through every PDF in the documents folder,
    extract text, clean it, and chunk it.
    Returns a list of all chunks across all professors.
    """
    all_chunks = []

    pdf_files = [f for f in os.listdir(DOCUMENTS_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("❌ No PDF files found in the documents folder.")
        return []

    print(f"Found {len(pdf_files)} PDF files\n")

    for filename in sorted(pdf_files):
        professor_name = filename.replace(".pdf", "")
        pdf_path       = os.path.join(DOCUMENTS_FOLDER, filename)

        print(f"Processing: {professor_name}")

        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text:
            print(f"  ⚠️  Skipping — no text extracted\n")
            continue

        clean = clean_text(raw_text)
        if not clean:
            print(f"  ⚠️  Skipping — nothing left after cleaning\n")
            continue

        chunks = chunk_text(clean, professor_name)
        all_chunks.extend(chunks)

        print(f"  ✅  {len(chunks)} chunks created\n")

    return all_chunks


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chunks = load_all_documents()

    print("=" * 60)
    print(f"TOTAL CHUNKS: {len(chunks)}")
    print("=" * 60)

    print("\n--- 5 SAMPLE CHUNKS ---\n")
    for i, chunk in enumerate(chunks[:5]):
        print(f"Chunk {i+1} | Professor: {chunk['professor']}")
        print(chunk["text"])
        print()
