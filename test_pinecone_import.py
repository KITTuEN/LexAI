import pinecone
print(f"Pinecone file: {pinecone.__file__}")
try:
    from pinecone import Pinecone
    print("Successfully imported Pinecone")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
