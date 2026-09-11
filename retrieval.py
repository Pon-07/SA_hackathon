import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional

class TicketSimilarityEngine:
    """
    TF-IDF and Cosine Similarity retrieval engine over historical ticket repository.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Combine category, subject, and description for contextual retrieval
        self.df["combined_text"] = (
            self.df["category"].fillna("") + " " +
            self.df["subject"].fillna("") + " " +
            self.df["description"].fillna("")
        )
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["combined_text"])

    def find_similar_tickets(
        self,
        subject: str,
        description: str,
        category: Optional[str] = None,
        top_n: int = 3,
        threshold: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Transform query and compute cosine similarity against all historical tickets.
        Returns top_n most similar historical records.
        """
        cat_prefix = f"{category} " if category else ""
        query_text = f"{cat_prefix}{subject} {description}".strip()
        if not query_text:
            return []

        query_vec = self.vectorizer.transform([query_text])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Top N indices
        top_indices = np.argsort(sim_scores)[::-1][:top_n]

        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            score = float(sim_scores[idx])
            row = self.df.iloc[idx]
            
            res_note = row.get("resolution_notes")
            if pd.isna(res_note) or not str(res_note).strip() or str(res_note).lower() == "nan":
                res_note = "Resolution note unavailable."

            results.append({
                "ticket_id": str(row.get("ticket_id", f"TKT{idx+1:04d}")),
                "subject": str(row.get("subject", "")),
                "description": str(row.get("description", "")),
                "category": str(row.get("category", "General")),
                "priority": str(row.get("priority", "Medium")),
                "status": str(row.get("status", "Resolved")),
                "assigned_agent": str(row.get("assigned_agent", "Unassigned")),
                "resolution_notes": str(res_note),
                "similarity_score": score,
                "similarity_percentage": f"{round(score * 100)}%",
                "is_strong_match": score >= threshold
            })

        return results

    def explain_similarity(self, results: List[Dict[str, Any]], threshold: float = 0.15) -> str:
        """
        Generate human-readable similarity retrieval explanation.
        """
        if not results:
            return "No query text provided."
        best = results[0]
        if best["similarity_score"] < threshold:
            return (
                f"No strong historical match found (Highest similarity: "
                f"{best['similarity_percentage']} < {int(threshold*100)}% threshold)."
            )
        return (
            f"Matched against 1000 historical tickets using TF-IDF text similarity. "
            f"Best match: {best['ticket_id']} with {best['similarity_percentage']} text similarity."
        )

# Global engine helper functions
_ENGINE_INSTANCE: Optional[TicketSimilarityEngine] = None

def get_similarity_engine(df: pd.DataFrame) -> TicketSimilarityEngine:
    """Singleton-style or cached helper for the similarity engine."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None or len(_ENGINE_INSTANCE.df) != len(df):
        _ENGINE_INSTANCE = TicketSimilarityEngine(df)
    return _ENGINE_INSTANCE

def find_similar_ticket(
    subject: str,
    description: str,
    df: Optional[pd.DataFrame] = None,
    category: Optional[str] = None,
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """Convenience top-level function matching specification."""
    if df is None:
        df = pd.read_csv("tickets.csv")
    engine = get_similarity_engine(df)
    return engine.find_similar_tickets(subject, description, category=category, top_n=top_n)
