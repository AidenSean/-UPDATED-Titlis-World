import chromadb
from sentence_transformers import SentenceTransformer

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Example FAQs
faq_data = [
    {"question": "What is machine learning?", "answer": "Machine learning is a field of AI..."},
    {"question": "How does a neural network work?", "answer": "A neural network is composed of layers..."},
    {"question": "What is overfitting in ML?", "answer": "Overfitting occurs when a model learns noise..."},
]

# Create a ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="faq_collection")

# Store FAQ embeddings in ChromaDB
for faq in faq_data:
    embedding = model.encode(faq["question"]).tolist()
    collection.add(ids=[faq["question"]], embeddings=[embedding], metadatas=[faq])

print("FAQ dataset prepared and stored in ChromaDB.")
