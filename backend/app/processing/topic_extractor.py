from transformers import pipeline

# Load HuggingFace LLM
generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    max_length=20
)


def extract_topic(text):

    prompt = f"""
Extract one clear topic (maximum 3 words) from the following educational text.
Return only the topic.

Text: {text}
"""

    result = generator(prompt)

    topic = result[0]["generated_text"].strip()

    return topic


def add_topics_to_documents(documents):

    for doc in documents:
        topic = extract_topic(doc["text"])
        doc["metadata"]["topic"] = topic

    return documents


documents = [
{
 "text": "Gradient descent is an optimization algorithm used to minimize loss in neural networks.",
 "metadata": {
     "source": "pdf",
     "file_name": "ml_notes.pdf",
     "page": 5
 }
},
{
 "text": "Convolutional neural networks detect patterns in images using filters.",
 "metadata": {
     "source": "youtube",
     "video_url": "https://youtube.com/example",
     "timestamp": "02:10"
 }
},
{
 "text": "Backpropagation computes gradients during neural network training.",
 "metadata": {
     "source": "pdf",
     "file_name": "deep_learning.pdf",
     "page": 12
 }
}
]

updated_documents = add_topics_to_documents(documents)

print(updated_documents)