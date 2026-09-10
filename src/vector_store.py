import os
import pickle
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

INDEX_DIR = "data/embeddings"
INDEX_FILE = os.path.join(INDEX_DIR, "faiss_index.bin")
METADATA_FILE = os.path.join(INDEX_DIR, "pairs_metadata.pkl")

class KnowledgeStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadata = []

    def build_index(self, pairs_csv_path: str = "data/processed/amazon_pairs.csv"):
        print("Loading pairs for vector indexing...")
        df = pd.read_csv(pairs_csv_path).dropna(subset=["customer_text", "brand_reply_text"])
        
        # Test queries leak avvakunda undataniki 1500 historical cases ni index cheddam
        train_df = df.head(1500).copy()
        
        print(f"Generating embeddings for {len(train_df)} historical tweets...")
        texts = train_df["customer_text"].tolist()
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        
        self.metadata = train_df.to_dict(orient="records")
        
        os.makedirs(INDEX_DIR, exist_ok=True)
        faiss.write_index(self.index, INDEX_FILE)
        with open(METADATA_FILE, "wb") as f:
            pickle.dump(self.metadata, f)
            
        print(f"Index successfully built and saved to '{INDEX_DIR}'.")

    def load_index(self):
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            raise FileNotFoundError("Index files not found. Run build_index first.")
        self.index = faiss.read_index(INDEX_FILE)
        with open(METADATA_FILE, "rb") as f:
            self.metadata = pickle.load(f)

    def retrieve_similar(self, query: str, top_k: int = 2) -> str:
        if self.index is None:
            self.load_index()
            
        query_vec = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vec, top_k)
        
        context_parts = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                item = self.metadata[idx]
                context_parts.append(
                    f"Historical Customer: {item['customer_text']}\nHistorical Amazon Reply: {item['brand_reply_text']}"
                )
        return "\n---\n".join(context_parts)

if __name__ == "__main__":
    store = KnowledgeStore()
    store.build_index()
    
    # Quick sanity check
    sample_q = "My package has not arrived yet, tracking shows stuck"
    print("\nSanity Check Retrieval for:", sample_q)
    print(store.retrieve_similar(sample_q, top_k=2))