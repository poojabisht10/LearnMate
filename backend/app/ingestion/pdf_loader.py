import os
import fitz  # PyMuPDF
from typing import List, Dict


class PDFLoader:
    """
    Loads PDF files and extracts text with metadata.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def load_pdf(self, file_path: str) -> List[Dict]:
        """
        Extract text from a single PDF file and return chunks with metadata.
        """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = fitz.open(file_path)
        filename = os.path.basename(file_path)

        documents = []

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()

            if not text.strip():
                continue

            chunks = self.chunk_text(text)

            for chunk in chunks:
                documents.append({
                    "text": chunk,
                    "metadata": {
                        "source": "pdf",
                        "filename": filename,
                        "page": page_num
                    }
                })

        return documents

    def load_multiple_pdfs(self, folder_path: str) -> List[Dict]:
        """
        Load all PDFs from a folder.
        """

        all_documents = []

        for file in os.listdir(folder_path):
            if file.endswith(".pdf"):
                file_path = os.path.join(folder_path, file)
                docs = self.load_pdf(file_path)
                all_documents.extend(docs)

        return all_documents

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        """

        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk = words[start:end]
            chunks.append(" ".join(chunk))

            start += self.chunk_size - self.overlap

        return chunks


if __name__ == "__main__":
    loader = PDFLoader()

    docs = loader.load_pdf("backend/data/pdfs/sample_multicolumn.pdf")

    print(f"Total chunks created: {len(docs)}\n")

    for d in docs[:20]:  
        print(d["metadata"])
        print(d["text"][:200])
        print("-" * 50)