from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import nltk
from nltk.tokenize import word_tokenize
from nltk import pos_tag


nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# -------------------------
# Load embedding model
# -------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# Similarity threshold (recommended)
SIMILARITY_THRESHOLD = 0.2


# -------------------------
# POS-based keyword extractor
# -------------------------
def extract_keywords(query):
    """
    Keep only important words:
    - Nouns (NN, NNS)
    - Adjectives (JJ)
    """
    tokens = word_tokenize(query)
    tagged = pos_tag(tokens)

    keywords = [
        word.lower() for word, pos in tagged
        if pos.startswith('NN') or pos.startswith('JJ')
    ]

    return " ".join(keywords)


# -------------------------
# Retrieval Function
# -------------------------
def retrieve_documents(query, index, embedded_docs, k=3):
    """
    Retrieve top-k similar documents using FAISS.
    Uses POS-filtered query for better retrieval.
    """

    # -------------------------
    # Step 1: Extract keywords
    # -------------------------
    keyword_query = extract_keywords(query)

    # Fallback: if POS removes everything
    if not keyword_query.strip():
        keyword_query = query

    # -------------------------
    # Step 2: Encode query
    # -------------------------
    query_embedding = model.encode([keyword_query])
    query_vector = np.array(query_embedding).astype("float32")

    # Normalize for cosine similarity
    faiss.normalize_L2(query_vector)

    # -------------------------
    # Step 3: Search
    # -------------------------
    distances, indices = index.search(query_vector, k)

    # -------------------------
    # Step 4: Filter by threshold
    # -------------------------
    results = []

    for score, i in zip(distances[0], indices[0]):
        if i == -1 or i >= len(embedded_docs):
            continue

        if score >= SIMILARITY_THRESHOLD:
            results.append(embedded_docs[i])

    return results