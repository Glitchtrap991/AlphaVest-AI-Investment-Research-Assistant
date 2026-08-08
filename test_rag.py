"""Quick test to diagnose where the RAG pipeline hangs."""
import time, sys

print("1. Importing chromadb...", flush=True)
t0 = time.time()
import chromadb
print(f"   Done in {time.time()-t0:.1f}s", flush=True)

print("2. Creating PersistentClient...", flush=True)
t0 = time.time()
client = chromadb.PersistentClient(path="data/chroma_db")
print(f"   Done in {time.time()-t0:.1f}s", flush=True)

print("3. get_or_create_collection (triggers default embedding model download)...", flush=True)
t0 = time.time()
collection = client.get_or_create_collection(name="test_collection")
print(f"   Done in {time.time()-t0:.1f}s", flush=True)

print("4. Adding a single test document (triggers embedding)...", flush=True)
t0 = time.time()
collection.add(
    ids=["test_0"],
    documents=["This is a test document about Azure cloud computing."],
    metadatas=[{"source": "test.pdf", "page": 0}],
)
print(f"   Done in {time.time()-t0:.1f}s", flush=True)

print("5. Adding 5 docs in batch...", flush=True)
t0 = time.time()
collection.add(
    ids=[f"batch_{i}" for i in range(5)],
    documents=[f"Test document number {i} about cloud services." for i in range(5)],
    metadatas=[{"source": "test.pdf", "page": i} for i in range(5)],
)
print(f"   Done in {time.time()-t0:.1f}s", flush=True)

print("6. Querying...", flush=True)
t0 = time.time()
results = collection.query(query_texts=["azure"], n_results=2)
print(f"   Done in {time.time()-t0:.1f}s", flush=True)
print(f"   Results: {results['documents']}", flush=True)

# Cleanup
client.delete_collection("test_collection")
print("\nAll steps completed successfully!", flush=True)
