import re


def clean_text(text: str) -> str:
    """
    Remove symbols and punctuation while keeping English words.
    """

    if not text:
        return ""

    # Remove punctuation and symbols
    text = re.sub(r"[^\w\s]", "", text)

    # Replace newlines with space
    text = text.replace("\n", " ")

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_documents(documents: list) -> list:
    """
    Clean the 'text' field of all documents.
    """

    cleaned_docs = []

    for doc in documents:

        cleaned_doc = {
            "text": clean_text(doc.get("text", "")),
            "metadata": doc.get("metadata", {})
        }

        cleaned_docs.append(cleaned_doc)

    return cleaned_docs


# -------- MAIN FUNCTION --------

if __name__ == "__main__":

    # Example documents
    documents = [
        {
            "text": "♪ We've known each other\nfor so long!!! Your heart's been aching...",
            "metadata": {
                "source": "youtube",
                "timestamp": "01:00"
            }
        },
        {
            "text": "Machine learning, is a field of AI!!! It uses data.",
            "metadata": {
                "source": "pdf",
                "page": 3
            }
        }
    ]

    cleaned = clean_documents(documents)

    print("\nCleaned Documents:\n")

    for doc in cleaned:
        print(doc)