from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(documents, chunk_size=1400):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200
    )

    chunks = []

    for doc in documents:

        text = doc["text"]
        metadata = doc["metadata"]

        # If text is small, keep it as one chunk
        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "metadata": metadata
            })
            continue

        # Otherwise split the text
        splits = splitter.split_text(text)

        for split in splits:
            chunks.append({
                "text": split,
                "metadata": metadata
            })

    return chunks


# ---------------- EXAMPLE ---------------- #

documents = [
    {
        "text": "Neural networks are inspired by biological neurons. "
                "Each neuron receives inputs, processes them, and produces an output. "
                "These neurons are organized into layers including input, hidden, "
                "and output layers. Training a neural network involves adjusting "
                "weights using algorithms such as backpropagation.",
        "metadata": {
            "source": "youtube",
            "timestamp": "02:10",
            "url": "https://youtube.com/watch?v=example"
        }
    },
    {
        "text": "Machine learning is a field of artificial intelligence that focuses "
                "on enabling computers to learn from data without explicit programming. "
                "There are several types of machine learning including supervised learning, "
                "unsupervised learning, and reinforcement learning. These methods are used "
                "in many real world applications such as recommendation systems, fraud "
                "detection, natural language processing, and computer vision. "
                * 20,   # repeating to simulate a long PDF page
        "metadata": {
            "source": "pdf",
            "page": 5,
            "file": "ml_book.pdf"
        }
    }
]


chunked_docs = chunk_documents(documents)

print("Total chunks created:", len(chunked_docs))
print()

for chunk in chunked_docs[:3]:
    print(chunk)
    print()