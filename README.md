# LearnMate — AI-Powered Learning Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-frontend-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)
![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> Turn any collection of YouTube videos and PDFs into an interactive study session — ask questions, get cited answers, and quiz yourself on demand.

---

## What is LearnMate?

LearnMate is a Retrieval-Augmented Generation (RAG) learning platform that lets you ingest multiple YouTube videos and PDF documents, then interact with all that content through a single interface.

Instead of scrubbing through hours of video or skimming dense PDFs, you ask a question in plain English. LearnMate finds the most relevant passages across all your sources, generates a grounded answer, and tells you exactly where it came from — down to the timestamp or page number. You can also generate a custom quiz at any time to test your retention.

---

## Features

### Multi-Source Ingestion

- Add any number of YouTube video URLs — transcripts are fetched automatically
- Upload multiple PDFs — text is extracted and chunked for retrieval
- All sources are indexed together into a single unified knowledge base

### Question Answering with Citations

- Ask questions in natural language
- Answers are grounded in your uploaded content, not internet-wide knowledge
- Every answer includes precise source references:
  - ⏱ YouTube: timestamp (e.g. `02:30`)
  - 📄 PDF: page number (e.g. `Page 14`)

### Adaptive Quiz Generation

Configure quizzes by:

- Number of questions
- Difficulty (easy / medium / hard)
- Specific topic or concept
- Source filter (quiz from one video or one PDF, or all sources)

Results include instant scoring with per-question feedback.

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                        User                             │
│          (uploads PDFs / pastes YouTube URLs)           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Content Extraction                     │
│   YouTube Transcript API  │  PyMuPDF (PDF text)         │
└──────────────────────┬──────────────────────────────────┘
                       │  chunks + metadata (source, ts/page)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Embedding & Indexing                       │
│          all-MiniLM-L6-v2  →  FAISS vector store        │
└──────────────────────┬──────────────────────────────────┘
                       │  top-K relevant chunks (TOP_K=3)
                       ▼
┌─────────────────────────────────────────────────────────┐
│               Answer / Quiz Generation                  │
│           Gemini 2.5 Flash (via Google AI API)          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│             Streamlit Frontend                          │
│      Cited answers  │  Adaptive quiz  │  Score card     │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer               | Technology                                 |
| ------------------- | ------------------------------------------ |
| Frontend            | Streamlit                                  |
| LLM                 | Gemini 2.5 Flash (Google AI)               |
| Embeddings          | `all-MiniLM-L6-v2` (Sentence Transformers) |
| Vector Store        | FAISS                                      |
| PDF Extraction      | PyMuPDF (`fitz`)                           |
| Transcript Fetching | YouTube Transcript API                     |
| Language            | Python 3.10+                               |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/poojabisht10/learnmate.git
cd learnmate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Google AI (Gemini) API key
GOOGLE_API_KEY=your_api_key_here

# Model
GEMINI_MODEL=gemini-2.5-flash

# Retrieval settings
MAX_CONTEXT_LENGTH=2000
TOP_K=3

# App settings
ENV=development
DEBUG=True
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### 4. Run the app

```bash
cd backend/app && streamlit run main.py
```

The app will open at `http://localhost:8501`.

---

## Project Structure

```
learnmate/
├── backend/
│   └── app/
│       ├── main.py              # Streamlit entry point
│       ├── ingestion/           # PDF + YouTube content extraction
│       ├── retrieval/           # FAISS indexing & similarity search
│       ├── generation/          # Gemini prompts for QA and quizzing
│       └── utils/               # Helpers, config loading
├── requirements.txt
├── .env.example
└── README.md
```

---

## Example Outputs

### Cited Answer

```
Q: What is gradient descent?

A: Gradient descent is an optimization algorithm that iteratively adjusts
   model parameters to minimize a loss function by moving in the direction
   of steepest descent.

Sources:
  📺 ML Crash Course (YouTube) — 02:30
  📄 Deep Learning Notes.pdf   — Page 7
```

### Quiz

```
Q1. Which of the following best describes overfitting?

  A. The model performs well on training and test data
  B. The model memorizes training data but fails to generalize  ✓
  C. The model underfits the training distribution
  D. The loss function diverges during training

Score: 4 / 5 (80%)
```

---

## Roadmap

- [ ] Hybrid search (keyword + semantic) for improved retrieval accuracy
- [ ] Support for audio files and lecture recordings (Whisper transcription)
- [ ] Personalized quiz generation based on past performance
- [ ] Flashcard export (Anki-compatible)
- [ ] Multi-user sessions with saved learning history
- [ ] Support for `.pptx`, `.epub`, and web article URLs

---

## Author

**Pooja Bisht** — [github.com/poojabisht10](https://github.com/poojabisht10)

---
# LearnMate
