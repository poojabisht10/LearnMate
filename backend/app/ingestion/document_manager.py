import os
from typing import List, Dict


from ingestion.pdf_loader import PDFLoader
from ingestion.youtube_loader import load_youtube_transcript


class DocumentManager:
    """
    Handles ingestion from multiple sources (PDFs + YouTube)
    and returns a unified document structure for the RAG pipeline.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.pdf_loader = PDFLoader(chunk_size, overlap)

    # -----------------------------
    # PDF INGESTION
    # -----------------------------
    def load_pdfs(self, pdf_paths: List[str]) -> List[Dict]:

        all_docs = []

        for path in pdf_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"PDF not found: {path}")

            docs = self.pdf_loader.load_pdf(path)
            all_docs.extend(docs)

        return all_docs

    # -----------------------------
    # YOUTUBE INGESTION
    # -----------------------------
    def load_youtube(self, youtube_urls: List[str]) -> List[Dict]:

        documents = []

        for url in youtube_urls:

            transcript_chunks = load_youtube_transcript(url)

            for chunk in transcript_chunks:
                # Get the title, with fallback to video ID
                video_title = chunk.get("video_title")
                if not video_title or video_title.strip() == "":
                    # Fallback: extract video ID for display
                    video_id = chunk.get("video_id", "")
                    video_title = f"Video ({video_id[:8]})" if video_id else "YouTube Video"

                documents.append({
                    "text": chunk["text"],
                    "metadata": {
                        "source": "youtube",
                        "video_url": chunk["source"],
                        "link": chunk["source"],
                        "title": video_title,
                        "video_id": chunk.get("video_id"),
                        "timestamp": chunk["timestamp"],
                        "timestamp_seconds": chunk["timestamp_seconds"],
                        "chunk_end_timestamp": chunk["chunk_end_timestamp"]
                    }
                })

        return documents

    # -----------------------------
    # LOAD EVERYTHING
    # -----------------------------
    def load_all_sources(
        self,
        pdf_paths: List[str] = None,
        youtube_urls: List[str] = None
    ) -> List[Dict]:

        documents = []

        if pdf_paths:
            documents.extend(self.load_pdfs(pdf_paths))

        if youtube_urls:
            documents.extend(self.load_youtube(youtube_urls))

        return documents

    # -----------------------------
    # DATASET SUMMARY
    # -----------------------------
    def summarize(self, docs: List[Dict]):

        summary = {
            "total_chunks": len(docs),
            "pdf_chunks": 0,
            "youtube_chunks": 0,
            "sources": set(),
            "source_titles": {}  # Map source URL/filename to display title
        }

        for d in docs:

            source = d["metadata"]["source"]

            if source == "pdf":
                summary["pdf_chunks"] += 1
                filename = d["metadata"]["filename"]
                summary["sources"].add(filename)
                summary["source_titles"][filename] = filename

            if source == "youtube":
                summary["youtube_chunks"] += 1
                video_url = d["metadata"]["video_url"]
                title = d["metadata"].get("title", "YouTube Video")
                summary["sources"].add(video_url)
                summary["source_titles"][video_url] = title

        summary["sources"] = list(summary["sources"])

        return summary


# -----------------------------
# TEST SCRIPT
# -----------------------------
if __name__ == "__main__":

    manager = DocumentManager()

    pdfs = [
        "backend/data/pdfs/sample_tables.pdf"
    ]

    videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ]

    docs = manager.load_all_sources(
        pdf_paths=pdfs,
        youtube_urls=videos
    )

    print("Total chunks:", len(docs))

    summary = manager.summarize(docs)

    print("\nSummary:")
    print(summary)

    print("\nSample document:")
    print(docs[3])