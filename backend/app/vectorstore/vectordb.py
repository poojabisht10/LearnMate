import faiss
import numpy as np
import os
import json


INDEX_SAVE_DIR = os.path.join(os.path.dirname(__file__), "indexes")
INDEX_FILE = os.path.join(INDEX_SAVE_DIR, "faiss_index.bin")
METADATA_FILE = os.path.join(INDEX_SAVE_DIR, "metadata.json")


def _ensure_index_dir():
    os.makedirs(INDEX_SAVE_DIR, exist_ok=True)


def create_faiss_index(embedded_docs):
    """
    Create FAISS index from embedded documents
    """

    if not embedded_docs:
        raise ValueError("No documents provided for indexing")

    embeddings = [doc["embedding"] for doc in embedded_docs]
    vectors = np.array(embeddings).astype("float32")

    if len(vectors.shape) != 2:
        raise ValueError("Invalid embedding shape")

    dimension = vectors.shape[1]

    # Normalize for cosine similarity
    faiss.normalize_L2(vectors)

    # ✅ Better: Inner Product = cosine similarity
    index = faiss.IndexFlatIP(dimension)

    index.add(vectors)

    return index


def save_index(index, embedded_docs):
    _ensure_index_dir()

    faiss.write_index(index, INDEX_FILE)

    metadata = [
        {k: v for k, v in doc.items() if k != "embedding"}
        for doc in embedded_docs
    ]

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f)


def load_index():
    if not os.path.exists(INDEX_FILE):
        return None, None

    index = faiss.read_index(INDEX_FILE)

    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
    else:
        metadata = None

    return index, metadata


def index_exists():
    return os.path.exists(INDEX_FILE)


def documents_changed(embedded_docs):
    if not index_exists():
        return True

    _, metadata = load_index()

    if metadata is None or len(metadata) != len(embedded_docs):
        return True

    for i, doc in enumerate(embedded_docs):
        saved = metadata[i]

        if saved.get("text") != doc.get("text"):
            return True

        if saved.get("metadata") != doc.get("metadata"):
            return True

    return False


def rebuild_index(embedded_docs):
    clear_index()

    index = create_faiss_index(embedded_docs)

    save_index(index, embedded_docs)

    return index


def clear_index():
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)

    if os.path.exists(METADATA_FILE):
        os.remove(METADATA_FILE)