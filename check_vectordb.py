import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.vector_db import vector_db

print("=" * 60)
print("VECTOR DATABASE STATUS")
print("=" * 60)

# Check count
count = vector_db.collection.count()
print(f"📊 Total Documents: {count}")

if count == 0:
    print("❌ Vector database is EMPTY!")
    print("\n💡 You need to run the knowledge base update process.")
else:
    print(f"✅ Vector database has {count} documents")
    
    # Get sample data
    info = vector_db.get_collection_info()
    print(f"\n📝 Collection Name: {info['collection_name']}")
    print(f"\n🔑 Sample IDs (first 5):")
    for id in info['sample_ids'][:5]:
        print(f"   - {id}")
    
    print(f"\n📄 Sample Documents (first 2):")
    for i, doc in enumerate(info['sample_documents'][:2], 1):
        print(f"\n   {i}. {doc}")
        if i < len(info['sample_metadatas']):
            print(f"      Metadata: {info['sample_metadatas'][i-1]}")

print("\n" + "=" * 60)