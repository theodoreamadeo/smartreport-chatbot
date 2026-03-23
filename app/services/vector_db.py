import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.config import Settings
from typing import List, Dict
from app.core.config import setting
import pandas as pd
import os
import httpx

class VectorDBService:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        # Initialize OpenAI Embedding Function
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key = setting.openai_api_key,
            model_name = "text-embedding-3-small"
        )

        # Get or create Chroma collection for PDF knowledge base
        self.pdf_collection = self.client.get_or_create_collection(
            name="knowledge_pdf",
            embedding_function=self.embedding_function, #type: ignore
            metadata={"hnsw:space":"cosine"}
        )

        # Get or create Chroma collection for Excel issue reports
        self.excel_collection = self.client.get_or_create_collection(
            name="knowledge_excel",
            embedding_function=self.embedding_function, #type: ignore
            metadata={"hnsw:space":"cosine"}
        )
    
    def add_pdf_documents(self, texts: List[str], metadatas: List[Dict[str, str]]):
        """Add multiple documents to the vector database."""
        ids = [metadata["chunk_id"] for metadata in metadatas]
        self.pdf_collection.add(
            documents=texts,
            metadatas=metadatas,  # type: ignore
            ids=ids
        )

    # Query the vector database for PDF knowledge base
    def query_pdf_knowledge_base(self, query: str, n_results: int = 3) -> List[dict]:
        """Query the knowledge base for relevant information."""
        results = self.pdf_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results["documents"] or not results["documents"][0]:
            return []
        
        return [
            {
                "text": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0] if results["metadatas"] else [],
                results["distances"][0] if results["distances"] else []
            )
        ]

    # Load all data inside Excel into Chroma
    def load_excel_to_vectordb(self, excel_file: str = "logs/ALuL Issue Tracking.xlsx"):
        """Load all Excel data into vector database"""
        try:
            if not os.path.exists(excel_file):
                print(f"Excel file not found: {excel_file}")
                return
            
            df = pd.read_excel(excel_file)
            if df.empty:
                return 0
            
            # Clear existing data
            existing = self.excel_collection.get()
            existing_ids = existing.get("ids", [])
            if existing_ids:
                self.excel_collection.delete(ids=existing_ids)
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                doc_text = (
                    f"Date: {row.get('date_reported', 'N/A')}\n"
                    f"Reporter: {row.get('reporter', 'N/A')}\n"
                    f"Type: {row.get('issue_type', 'N/A')}\n"
                    f"Equipment: {row.get('equipment_id', 'N/A')}\n"
                    f"Issue: {row.get('issue_summary', 'N/A')}\n"
                    f"Severity: {row.get('severity', 'N/A')}"
                )
                documents.append(doc_text)
                metadatas.append({
                    "source": "excel",
                    "log_id": str(row.get("log_id", idx)),
                    "date": str(row.get("date_reported", "")),
                    "equipment": str(row.get("equipment_id", "")),
                    "severity": str(row.get("severity", "")),
                })
                ids.append(f"excel_row_{idx}")
            
            # Add to vector database 
            if documents:
                self.excel_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                # Verify by checking collection count
                count = self.excel_collection.count()
                print(f"Total documents in collection: {count}")

            return len(documents)
        
        except Exception as e:
            print(f"Error loading Excel to VectorDB: {e}")
            import traceback
            traceback.print_exc()

    def query_excel_knowledge_base(self, query: str, n_results: int = 5) -> List[dict]:
        count = self.excel_collection.count()
        if count == 0:
            print("Excel knowledge base is empty. Please load data first.")
            return []
        capped = min(n_results, count)
        results = self.excel_collection.query(query_texts=[query], n_results=capped)
        if not results["documents"] or not results["documents"][0]:
            return []
        return [
            {"text": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0] if results["metadatas"] else [],
                results["distances"][0] if results["distances"] else []
            )
        ]

# Global instance
vector_db = VectorDBService()