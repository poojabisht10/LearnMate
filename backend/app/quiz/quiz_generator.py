import os
import random
from google import genai

# vector retrieval (reuse same pipeline idea)
from vectorstore.retrieval import retrieve_documents

from vectorstore.vectordb import (
    load_index,
    index_exists,
    documents_changed,
    rebuild_index
)

class QuizGenerator:

    def __init__(self):

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")

        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # -------------------------
    # Difficulty Mapping
    # -------------------------
    def get_difficulty(self, level):

        if level == "easy":
            return "only easy, simple factual questions"
        elif level == "medium":
            return "only medium, conceptual understanding questions"
        elif level == "hard":
            return "only hard, analytical and tricky questions"
        elif level in ("mix", "dynamic"):
            return "a balanced mix of easy, medium, and hard questions"
        return "general questions"

    # -------------------------
    # Filter Sources
    # -------------------------
    def filter_docs(self, docs, sources):

        if not sources:
            return docs

        # Filter by specific source (filename for PDFs, video_url for YouTube)
        filtered = []
        for d in docs:
            metadata = d["metadata"]
            source_type = metadata.get("source")
            
            # Check if this document's source is in the selected sources
            if source_type == "pdf":
                if metadata.get("filename") in sources:
                    filtered.append(d)
            elif source_type == "youtube":
                if metadata.get("video_url") in sources:
                    filtered.append(d)
        
        return filtered

    # -------------------------
    # Generate Quiz
    # -------------------------
    def generate_quiz(self, query, embedded_docs, num_questions=5, difficulty="medium", sources=None):

        # Step 1: Filter docs
        docs = self.filter_docs(embedded_docs, sources)

        if not docs:
            return "No documents available"

        # -------------------------
        # Step 2: Load / Build Index (SAME AS QA)
        # -------------------------

        if index_exists() and not documents_changed(docs):
            index, _ = load_index()
        else:
            index = rebuild_index(docs)

        # -------------------------
        # Step 3: Retrieve
        # -------------------------

        retrieved = retrieve_documents(
            query,
            index,
            docs,
            k=num_questions * 2
        )

        # -------------------------
        # Step 4: Context
        # -------------------------

        context = "\n".join([d["text"][:200] for d in retrieved])

        # -------------------------
        # Step 5: Prompt
        # -------------------------

        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts",
            "quiz_prompt.txt"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        prompt = template.format(
            num_questions=num_questions,
            difficulty_instruction=self.get_difficulty(difficulty),
            context=context
        )

        # -------------------------
        # Step 6: Gemini
        # -------------------------

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.3,   # less randomness
                }
            )

            return response.text.strip()

        except Exception as e:
            return f"Error: {str(e)}"