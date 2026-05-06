import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# load env
from dotenv import load_dotenv
load_dotenv()

# vector store
from vectorstore.vectordb import (
    load_index,
    index_exists,
    documents_changed,
    rebuild_index
)
from vectorstore.retrieval import retrieve_documents

# ✅ NEW Gemini SDK
from google import genai


# -------------------------
# Configure Gemini
# -------------------------

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# -------------------------
# QA PIPELINE
# -------------------------

def qa_pipeline(query, embedded_docs):

    # -------------------------
    # Step 1: Load / Build Index
    # -------------------------

    if index_exists() and not documents_changed(embedded_docs):
        index, metadata = load_index()
    else:
        index = rebuild_index(embedded_docs)

    # -------------------------
    # Step 2: Retrieval
    # -------------------------

    k = int(os.getenv("TOP_K", 3))
    retrieved_docs = retrieve_documents(query, index, embedded_docs, k=k)


    # bail early if nothing passed the similarity threshold
    if not retrieved_docs:
        return "I don't have enough information in the provided sources to answer this question.", []

    # -------------------------
    # Step 3: Context
    # -------------------------

    max_len = int(os.getenv("MAX_CONTEXT_LENGTH", 2000))

    context = "\n".join([
        doc["text"][:max_len] for doc in retrieved_docs
    ])

        # -------------------------
    # Step 4: Load Prompt
    # -------------------------

    PROMPT_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts",
        "qa_prompt.txt"
    )

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        context=context,
        query=query
    )

    # -------------------------
    # Step 5: Gemini Call
    # -------------------------

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        answer = response.text.strip()

    except Exception as e:
        answer = f"Error: {str(e)}"

    return answer, retrieved_docs


# -------------------------
# SIMPLE API TEST
# -------------------------

if __name__ == "__main__":

    print("\n🔍 Testing Gemini API...\n")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="Say hi"
        )

        print("✅ API Working!\n")
        print("Response:\n", response.text)

    except Exception as e:
        print("❌ API Error:")
        print(e)