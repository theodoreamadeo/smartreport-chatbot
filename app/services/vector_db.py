import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.config import Settings
from typing import List, Dict
from app.core.config import setting
import pandas as pd
import os

class VectorDBService:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory = "./chroma_db",
            anonymized_telemetry = False
        ))

        # Initialize OpenAI Embedding Function
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key = setting.openai_api_key,
            model_name = "text-embedding-3-small"
        )

        # Get or create Chroma collection
        self.collection = self.client.get_or_create_collection(
            name="issue_tracker",
            embedding_function=self.embedding_function, #type: ignore
            metadata={"hnsw:space":"cosine"}
        )
    
    # Load all data inside Excel into Chroma
    def load_excel_to_vectordb(self, excel_file: str = "logs/ALuL Issue Tracking.xlsx"):
        """Load all Excel data into vector database"""
        try:
            print(f"📂 Loading from: {excel_file}")
            
            if not os.path.exists(excel_file):
                print(f"❌ Excel file not found: {excel_file}")
                return
            
            df = pd.read_excel(excel_file)
            print(f"📊 Loaded {len(df)} rows from Excel")
            
            # Print last 3 rows to verify latest data
            print("Last 3 entries:")
            print(df.tail(3))
            
            # Clear existing data
            try:
                self.client.delete_collection("issue_reports")
                self.collection = self.client.create_collection(
                    name="issue_reports",
                    embedding_function=self.embedding_function, #type: ignore
                    metadata={"hnsw:space": "cosine"}
                )
            except:
                pass
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Create a text representation of each row
                doc_text = (
                    f"Date: {row['Date']}\n"
                    f"Reporter: {row['Reporter']}\n"
                    f"Type: {row['Type']}\n"
                    f"Equipment: {row['Equipment']}\n"
                    f"Issue: {row['Issue Summary']}"
                )
                
                documents.append(doc_text)
                metadatas.append({
                    "date": str(row['Date']),
                    "reporter": str(row['Reporter']),
                    "type": str(row['Type']),
                    "equipment": str(row['Equipment'])
                })
                ids.append(f"report_{idx}")
            
            # Add to vector database 
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Added {len(documents)} reports to vector database")
                
                # Verify by checking collection count
                count = self.collection.count()
                print(f"📈 Total documents in collection: {count}")
        
        except Exception as e:
            print(f"❌ Error loading Excel to VectorDB: {e}")
            import traceback
            traceback.print_exc()

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar reports"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching VectorDB: {e}")
            return []

# Global instance
vector_db = VectorDBService()