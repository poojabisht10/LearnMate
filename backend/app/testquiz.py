import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ingestion
from ingestion.document_manager import DocumentManager

# processing
from processing.transcript_cleaner import clean_documents
from processing.chunking import chunk_documents

# embeddings
from embeddings.embedding_model import EmbeddingModel

# quiz
from quiz.quiz_generator import QuizGenerator
from quiz.scoring import QuizScorer


def main():

    pdf_files = [
        "backend/data/pdfs/sample_ml_notes.pdf",
        "backend/data/pdfs/sample_tables.pdf",
        "backend/data/pdfs/sample_multicolumn.pdf"
    ]

    youtube_urls = [
        "https://www.youtube.com/watch?v=gmvvaobm7eQ",
        "https://youtu.be/9gGnTQTYNaE?si=tt83VIFLeL-6kUcL",
        "https://youtu.be/ukzFI9rgwfU?si=tzqOHrYfU8QBzvp9"
    ]

    print("\n🚀 Loading data...")

    manager = DocumentManager()

    documents = manager.load_all_sources(
        pdf_paths=pdf_files,
        youtube_urls=youtube_urls
    )

    print("🧹 Cleaning...")
    docs = clean_documents(documents)

    print("✂️ Chunking...")
    chunks = chunk_documents(docs)

    print("🧠 Embedding...")
    model = EmbeddingModel()
    embedded_docs = model.embed_documents(chunks)

    # -------------------------
    # QUIZ INPUT
    # -------------------------

    query = input("\nEnter topic for quiz: ")
    num_q = int(input("Number of questions: "))
    difficulty = input("Difficulty (easy/medium/hard/mix): ").lower()

    sources = None  # use all available sources

    # -------------------------
    # GENERATE QUIZ
    # -------------------------

    quiz_gen = QuizGenerator()

    print("\n📝 Generating quiz...\n")

    quiz_text = quiz_gen.generate_quiz(
        query=query,
        embedded_docs=embedded_docs,
        num_questions=num_q,
        difficulty=difficulty,
        sources=sources
    )

    from quiz.scoring import hide_answers

    clean_quiz = hide_answers(quiz_text)

    print("\n📝 QUIZ:\n")
    print(clean_quiz)

    # -------------------------
    # USER ANSWERS
    # -------------------------

    user_answers = {}

    for i in range(1, num_q + 1):
        ans = input(f"Answer Q{i}: ").upper()
        user_answers[i] = ans

    # -------------------------
    # SCORING
    # -------------------------

    scorer = QuizScorer()

    result = scorer.evaluate(quiz_text, user_answers)

    print("\n🏆 RESULT")
    print(f"Score: {result['score']} / {result['total']}")
    print(f"Percentage: {result['percentage']:.2f}%")

    print("\n📊 DETAILS")

    for r in result["details"]:
        print(f"Q{r['id']} | Your: {r['user']} | Correct: {r['correct']} | {'✅' if r['is_correct'] else '❌'}")


if __name__ == "__main__":
    main()