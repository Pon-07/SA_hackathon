import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def train_and_export():
    dataset_path = Path("tickets.csv")
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path.resolve()}")
        return

    df = pd.read_csv(dataset_path)
    df["combined_text"] = df["subject"].fillna("") + " " + df["description"].fillna("")
    
    X = df["combined_text"]
    y = df["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            min_df=2,
            max_features=5000
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            C=2.0,
            class_weight="balanced",
            random_state=42
        ))
    ])

    print("Training ML Ticket Classifier pipeline...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    labels = sorted(list(y.unique()))
    cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    print(f"Model Accuracy on Test Set: {acc * 100:.2f}%")

    # Extract top influential feature words per category for Explainable AI
    tfidf = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["classifier"]
    feature_names = np.array(tfidf.get_feature_names_out())
    
    top_features_per_category = {}
    for idx, class_name in enumerate(clf.classes_):
        coef = clf.coef_[idx]
        top_indices = np.argsort(coef)[-12:][::-1]
        top_features_per_category[class_name] = [
            {"term": feature_names[i], "weight": round(float(coef[i]), 3)}
            for i in top_indices
        ]

    # Save trained model pipeline
    model_output_path = Path("ticket_classifier.pkl")
    joblib.dump(pipeline, model_output_path)
    print(f"Saved trained classifier pipeline to {model_output_path.resolve()}")

    # Save metrics and feature attributions for Explainable AI UI
    metrics_data = {
        "accuracy": round(float(acc), 4),
        "accuracy_percent": f"{acc * 100:.1f}%",
        "total_samples": len(df),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "classes": labels,
        "classification_report": report,
        "confusion_matrix": cm,
        "top_features": top_features_per_category
    }

    metrics_output_path = Path("model_metrics.json")
    with open(metrics_output_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Saved model metrics and XAI attributions to {metrics_output_path.resolve()}")


if __name__ == "__main__":
    train_and_export()
