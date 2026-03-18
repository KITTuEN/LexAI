import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Source (Local)
LOCAL_URI = "mongodb://localhost:27017/"
LOCAL_DB_NAME = "lexai"

# Destination (Atlas)
ATLAS_URI = "mongodb+srv://harikothapalli61_db_user:cSF5pxh81C5VUTVt@cluster0.zbhsdva.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ATLAS_DB_NAME = "lexai"

def migrate_database():
    print("--- LexAI Database Migration Tool ---")
    
    try:
        # 1. Connect to Local Source
        print(f"Connecting to Source: {LOCAL_URI}")
        client_local = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
        client_local.admin.command('ping')
        db_local = client_local[LOCAL_DB_NAME]
        print("✅ Source connected successfully.")
    except Exception as e:
        print(f"❌ Failed to connect to local source. Is MongoDB running locally? Error: {e}")
        sys.exit(1)

    try:
        # 2. Connect to Atlas Destination
        print(f"\nConnecting to Destination: {ATLAS_URI}")
        client_atlas = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000) # Give Atlas a bit more time
        client_atlas.admin.command('ping')
        db_atlas = client_atlas[ATLAS_DB_NAME]
        print("✅ Destination connected successfully.")
    except Exception as e:
        print(f"❌ Failed to connect to Atlas cluster. Ensure your IP has Network Access. Error: {e}")
        sys.exit(1)

    # 3. Migrate Collections
    collections = db_local.list_collection_names()
    if not collections:
        print("\n⚠️ No collections found in the local 'lexai' database system.")
        sys.exit(0)
        
    print(f"\nFound {len(collections)} collections to migrate: {collections}")
    
    for coll_name in collections:
        source_coll = db_local[coll_name]
        dest_coll = db_atlas[coll_name]
        
        # We don't want to copy internal system collections
        if coll_name.startswith("system."):
            continue
            
        doc_count = source_coll.count_documents({})
        if doc_count == 0:
            print(f"⏩ Skipping '{coll_name}' - No documents found.")
            continue
            
        print(f"🔄 Migrating '{coll_name}' ({doc_count} documents)...")
        
        # Read all documents from source
        documents = list(source_coll.find({}))
        
        try:
            # Drop the destination collection if it exists to ensure a clean slate
            dest_coll.drop()
            # Bulk insert into destination
            dest_coll.insert_many(documents)
            print(f"  └─ ✅ Successfully inserted {doc_count} documents into Atlas '{coll_name}'.")
        except Exception as e:
            print(f"  └─ ❌ Failed to migrate collection '{coll_name}'. Error: {e}")
            
    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
