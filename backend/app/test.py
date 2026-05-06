import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ingestion
from ingestion.document_manager import DocumentManager

# processing
from processing.transcript_cleaner import clean_documents
from processing.chunking import chunk_documents

# embeddings
from embeddings.embedding_model import EmbeddingModel

# rag pipeline
from rag.qa_pipeline import qa_pipeline

# citation handler
from rag.citation_handler import format_citations, print_citations

# from quiz.quiz_generator import QuizGenerator

# quiz_gen = QuizGenerator()

# quiz_text = quiz_gen.generate_quiz(
#     embedded_docs,
#     num_questions=3,
#     difficulty="hard",
#     sources=["pdf"]   # user choice
# )

# print("\n📝 QUIZ:\n")
# print(quiz_text)

def main():

    # -------------------------
    # INPUTS
    # -------------------------

    pdf_files = [
        "backend/data/pdfs/sample_tables.pdf",
        "backend/data/pdfs/sample_ml_notes.pdf"
    ]

    youtube_urls = [
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "https://www.youtube.com/watch?v=YRhxdVk_sIs",
        "https://www.youtube.com/watch?v=gmvvaobm7eQ"
    ]

    # -------------------------
    # Step 1: Load using DocumentManager
    # -------------------------

    print("\n🚀 Loading all sources...\n")

    manager = DocumentManager()

    documents = manager.load_all_sources(
        pdf_paths=pdf_files,
        youtube_urls=youtube_urls
    )

    if not documents:
        print("❌ No data loaded")
        return

    summary = manager.summarize(documents)

    print("\n📊 Dataset Summary:")
    print(summary)

    # -------------------------
    # Step 2: Clean
    # -------------------------

    print("\n🧹 Cleaning documents...")
    clean_docs = clean_documents(documents)

    # -------------------------
    # Step 3: Chunk
    # -------------------------

    print("\n✂️ Chunking...")
    chunks = chunk_documents(clean_docs)
    print(f"✅ Total chunks: {len(chunks)}")

    # -------------------------
    # Step 4: Embeddings
    # -------------------------

    print("\n🧠 Generating embeddings...")
    embedding_model = EmbeddingModel()
    embedded_docs = embedding_model.embed_documents(chunks)

    # -------------------------
    # Step 5: QA Loop
    # -------------------------

    
    # query = input("\n💬 Ask a question (or type 'exit'): ")
    query="What is Machine learning?"

    answer, sources = qa_pipeline(query, embedded_docs)

    citations = format_citations(sources)

    print("\n📢 ANSWER:\n", answer.strip())
    print_citations(citations)


if __name__ == "__main__":
    main()