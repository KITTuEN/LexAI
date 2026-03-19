import os
from services.pinecone_service import pinecone_service
from services.gemini_service import gemini_service
import PyPDF2
import io

class RecursiveSplitter:
    """A lightweight replacement for langchain's RecursiveCharacterTextSplitter."""
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", " ", ""]

    def split_text(self, text):
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Find the best separator in the lookback area
            found_sep = False
            for sep in self.separators:
                if not sep: continue
                idx = text.rfind(sep, start, end)
                if idx != -1 and idx > start:
                    chunks.append(text[start:idx+len(sep)].strip())
                    start = idx + len(sep) - self.chunk_overlap
                    found_sep = True
                    break
            
            if not found_sep:
                # No separator found, hard cut
                chunks.append(text[start:end])
                start = end - self.chunk_overlap
        
        return [c for c in chunks if c.strip()]

class DocumentService:
    def __init__(self):
        self.text_splitter = RecursiveSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def extract_text_from_pdf(self, pdf_file):
        """Extracts text from a PDF file object."""
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def process_and_ingest(self, file_content, file_name, doc_id):
        """
        Processes a file (PDF or text) and ingests it into Pinecone.
        """
        if file_name.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(io.BytesIO(file_content))
        else:
            try:
                text = file_content.decode('utf-8')
            except:
                text = str(file_content)

        chunks = self.text_splitter.split_text(text)
        
        upsert_count = pinecone_service.upsert_chunks(
            case_id=str(doc_id),
            chunks=chunks,
            source_name=file_name
        )
        
        return {
            "doc_id": doc_id,
            "source": file_name,
            "chunks_processed": upsert_count,
            "total_text_length": len(text)
        }

document_service = DocumentService()
