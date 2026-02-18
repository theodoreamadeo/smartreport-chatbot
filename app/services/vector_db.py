import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.config import Settings
from typing import List, Dict
from app.core.config import setting
import pandas as pd
import os

class VectorDBService:
    def __init__(self):
        # Use PersistentClient instead of Client
        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        # Initialize OpenAI Embedding Function
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key = setting.openai_api_key,
            model_name = "text-embedding-3-small"
        )

        # Get or create Chroma collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_function, #type: ignore
            metadata={"hnsw:space":"cosine"}
        )
    
    # Load all data inside Excel into Chroma
    # def load_excel_to_vectordb(self, excel_file: str = "logs/ALuL Issue Tracking.xlsx"):
    #     """Load all Excel data into vector database"""
    #     try:
    #         print(f"📂 Loading from: {excel_file}")
            
    #         if not os.path.exists(excel_file):
    #             print(f"❌ Excel file not found: {excel_file}")
    #             return
            
    #         df = pd.read_excel(excel_file)
    #         print(f"📊 Loaded {len(df)} rows from Excel")
            
    #         # Print last 3 rows to verify latest data
    #         print("Last 3 entries:")
    #         print(df.tail(3))
            
    #         # Clear existing data
    #         try:
    #             self.client.delete_collection("issue_reports")
    #             self.collection = self.client.create_collection(
    #                 name="issue_reports",
    #                 embedding_function=self.embedding_function, #type: ignore
    #                 metadata={"hnsw:space": "cosine"}
    #             )
    #         except:
    #             pass
            
    #         documents = []
    #         metadatas = []
    #         ids = []
            
    #         for idx, row in df.iterrows():
    #             # Create a text representation of each row
    #             doc_text = (
    #                 f"Date: {row['Date']}\n"
    #                 f"Reporter: {row['Reporter']}\n"
    #                 f"Type: {row['Type']}\n"
    #                 f"Equipment: {row['Equipment']}\n"
    #                 f"Issue: {row['Issue Summary']}"
    #             )
                
    #             documents.append(doc_text)
    #             metadatas.append({
    #                 "date": str(row['Date']),
    #                 "reporter": str(row['Reporter']),
    #                 "type": str(row['Type']),
    #                 "equipment": str(row['Equipment'])
    #             })
    #             ids.append(f"report_{idx}")
            
    #         # Add to vector database 
    #         if documents:
    #             self.collection.add(
    #                 documents=documents,
    #                 metadatas=metadatas,
    #                 ids=ids
    #             )
    #             print(f"✅ Added {len(documents)} reports to vector database")
                
    #             # Verify by checking collection count
    #             count = self.collection.count()
    #             print(f"📈 Total documents in collection: {count}")
        
    #     except Exception as e:
    #         print(f"❌ Error loading Excel to VectorDB: {e}")
    #         import traceback
    #         traceback.print_exc()

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, str]]):
        """Add multiple documents to the vector database."""
        ids = [metadata["chunk_id"] for metadata in metadatas]
        self.collection.add(
            documents=texts,
            metadatas=metadatas,  # type: ignore
            ids=ids
        )

    def query_knowledge_base(self, query: str, n_results: int = 3) -> List[dict]:
        """Query the knowledge base for relevant information."""
        results = self.collection.query(
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
    
    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            
            # Get a sample of documents
            sample = self.collection.get(limit=5)
            
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "sample_ids": sample["ids"] if sample else [],
                "sample_metadatas": sample["metadatas"] if sample else [],
                "sample_documents": [doc[:200] + "..." if len(doc) > 200 else doc 
                                    for doc in (sample["documents"] or [])]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def is_empty(self) -> bool:
        """Check if the collection is empty."""
        return self.collection.count() == 0

# Global instance
vector_db = VectorDBService()