from sentence_transformers import SentenceTransformer
from typing import List, Dict


class EmbeddingModel:
    """
    Handles embedding generation for documents and queries
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        """
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        """
        embeddings = self.model.encode(texts, batch_size=32)
        return [emb.tolist() for emb in embeddings]

    def embed_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for documents.

        Expected document format:
        {
            "text": "...",
            "metadata": {...}
        }
        """

        texts = [doc["text"] for doc in documents]

        embeddings = self.embed_batch(texts)

        embedded_docs = []

        for doc, emb in zip(documents, embeddings):
            embedded_docs.append({
                "text": doc["text"],
                "embedding": emb,
                "metadata": doc["metadata"]
            })

        return embedded_docs

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query
        """
        return self.embed_text(query)


# -------------------------
# TEST SCRIPT
# -------------------------

if __name__ == "__main__":

    documents = [
        {
            "text": "Gradient descent is an optimization algorithm used in neural networks.",
            "metadata": {
                "source": "pdf",
                "file_name": "ml_notes.pdf",
                "page": 5,
                "topic": "Gradient Descent"
            }
        },
        {
            "text": "Convolutional neural networks detect image features using filters.",
            "metadata": {
                "source": "youtube",
                "video_url": "https://youtube.com/example",
                "timestamp": "02:10",
                "topic": "CNN"
            }
        }
    ]

    model = EmbeddingModel()

    embedded_docs = model.embed_documents(documents)

    print("Embedded Documents:\n")

    for doc in embedded_docs:
        print("Text:", doc["text"])
        print("Embedding length:", len(doc["embedding"]))
        print("Metadata:", doc["metadata"])
        print("-" * 50)