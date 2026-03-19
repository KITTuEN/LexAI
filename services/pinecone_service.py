import os
from pinecone import Pinecone, ServerlessSpec
from services.gemini_service import gemini_service
from dotenv import load_dotenv

load_dotenv()

class PineconeService:
    def __init__(self):
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'nyayavevasth')
        
        if not self.api_key:
            print("WARNING: PINECONE_API_KEY not found in environment.")
            self.pc = None
            self.index = None
            return

        self.pc = Pinecone(api_key=self.api_key)
        
        # Ensure index exists
        if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
            print(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=3072, # Dimension for gemini-embedding-001
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1' # Default region for serverless
                )
            )
        
        self.index = self.pc.Index(self.index_name)

    def upsert_chunks(self, case_id, chunks, source_name):
        """
        Embeds and upserts chunks into Pinecone in batches.
        """
        if not self.index:
            raise Exception("Pinecone index not initialized.")

        # Batch embed all chunks at once (much faster)
        # Gemini handles up to 100 per call, let's play it safe and batch the embeddings too if needed
        # but for most docs < 50 chunks, one call is enough.
        
        embeddings = []
        for i in range(0, len(chunks), 100):
            batch_chunks = chunks[i:i+100]
            batch_embeddings = gemini_service.embed_content(batch_chunks)
            embeddings.extend(batch_embeddings)

        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vectors.append({
                "id": f"{case_id}_{i}",
                "values": embedding,
                "metadata": {
                    "doc_id": case_id,
                    "chunk_index": i,
                    "source": source_name,
                    "text": chunk
                }
            })
        
        # Pinecone upsert in batches of 100
        for i in range(0, len(vectors), 100):
            batch = vectors[i:i+100]
            self.index.upsert(vectors=batch)
        
        return len(vectors)

    def query_context(self, query_text, doc_id=None, top_k=5):
        """
        Searches Pinecone for relevant chunks.
        If doc_id is provided, filters by that document.
        """
        if not self.index:
            raise Exception("Pinecone index not initialized.")

        query_embedding = gemini_service.embed_content(query_text, task_type="RETRIEVAL_QUERY")
        
        filter_dict = {}
        if doc_id:
            filter_dict = {"doc_id": doc_id}

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        return results.matches

    def delete_document(self, doc_id):
        """Deletes all vectors associated with a doc_id."""
        if not self.index:
            return
        
        self.index.delete(filter={"doc_id": doc_id})

pinecone_service = PineconeService()
