import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

# Official 7 Target Categories and Keywords
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Network": [
        "vpn",
        "wifi",
        "wi-fi",
        "network",
        "internet",
        "connection",
        "connectivity",
        "router",
        "dns",
        "firewall",
        "ethernet"
    ],
    "Hardware": [
        "laptop",
        "desktop",
        "monitor",
        "keyboard",
        "mouse",
        "battery",
        "screen",
        "hard drive",
        "computer",
        "docking station"
    ],
    "Software": [
        "excel",
        "word",
        "powerpoint",
        "application",
        "software",
        "crash",
        "crashes",
        "installation",
        "install",
        "update",
        "application error"
    ],
    "Email": [
        "email",
        "outlook",
        "mailbox",
        "mail",
        "inbox",
        "outbox",
        "attachment",
        "spam",
        "email server"
    ],
    "Printer": [
        "printer",
        "printing",
        "print",
        "paper jam",
        "print queue",
        "cartridge",
        "toner",
        "scanner"
    ],
    "Security": [
        "phishing",
        "unauthorized",
        "security",
        "suspicious",
        "malware",
        "antivirus",
        "threat",
        "breach",
        "compromised"
    ],
    "Access/Account": [
        "password",
        "login",
        "log in",
        "account",
        "permission",
        "access denied",
        "credentials",
        "locked account",
        "locked",
        "authentication",
        "sign in"
    ]
}

# Category priority weights for tie-breaking high-risk/specific categories
CATEGORY_WEIGHTS: Dict[str, float] = {
    "Security": 1.2,        # High-priority security keywords take precedence
    "Printer": 1.1,         # Very specific domain
    "Network": 1.0,
    "Hardware": 1.0,
    "Software": 1.0,
    "Email": 1.0,
    "Access/Account": 1.0
}

# Global Lazy-Loaded Classifier Pipeline
_CLASSIFIER_PIPELINE = None
_MODEL_LOADED = False


def _get_classifier():
    """Lazy-load the trained TF-IDF + LogisticRegression pipeline."""
    global _CLASSIFIER_PIPELINE, _MODEL_LOADED
    if not _MODEL_LOADED:
        _MODEL_LOADED = True
        model_file = Path(__file__).resolve().parent / "ticket_classifier.pkl"
        if model_file.exists():
            try:
                import joblib
                _CLASSIFIER_PIPELINE = joblib.load(model_file)
            except Exception as e:
                print(f"[categorization] Warning: could not load model ({e}), using keyword fallback.")
                _CLASSIFIER_PIPELINE = None
    return _CLASSIFIER_PIPELINE


def find_matched_keywords(text: str) -> Dict[str, List[str]]:
    """
    Find matching keywords across categories using case-insensitive phrase/word boundary matching.
    """
    if not text or not isinstance(text, str):
        return {}

    text_lower = text.lower()
    matches: Dict[str, List[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        matched_kws = []
        for kw in keywords:
            pattern = r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)"
            if re.search(pattern, text_lower):
                matched_kws.append(kw)
        if matched_kws:
            matches[category] = matched_kws

    return matches


def categorize(text: str) -> str:
    """
    Classify ticket text into one of the 7 categories.
    Uses ML LogisticRegression classifier when available; falls back to weighted keyword matching.
    """
    clf = _get_classifier()
    if clf is not None and text and text.strip():
        try:
            pred = clf.predict([text])[0]
            # Security safety check: If text contains explicit security red flags, ensure security priority
            matches = find_matched_keywords(text)
            if "Security" in matches and pred != "Security":
                sec_kws = ["phishing", "malware", "breach", "unauthorized", "compromised"]
                if any(k in text.lower() for k in sec_kws):
                    return "Security"
            return str(pred)
        except Exception:
            pass

    # Keyword fallback
    matches = find_matched_keywords(text)
    if not matches:
        return "General"

    def compute_category_score(cat: str) -> float:
        kws = matches[cat]
        base_score = sum(1.5 if " " in kw else 1.0 for kw in kws)
        return base_score * CATEGORY_WEIGHTS.get(cat, 1.0)

    return max(matches.keys(), key=compute_category_score)


def predict_category_with_explanation(text: str) -> Dict[str, Any]:
    """
    Produce rich Explainable AI output for categorization:
    - Predicted category
    - Confidence percentage
    - Class probability distribution
    - Top contributing feature tokens (TF-IDF * coefficient)
    - Matched keywords
    - Plain-text reasoning
    """
    matches = find_matched_keywords(text)
    matched_kws = []
    clf = _get_classifier()
    
    pred_category = "General"
    confidence = 0.5
    probabilities = {}
    contributing_tokens = []
    is_ml = False

    if clf is not None and text and text.strip():
        try:
            tfidf = clf.named_steps["tfidf"]
            lr = clf.named_steps["classifier"]
            classes = lr.classes_
            
            probs = clf.predict_proba([text])[0]
            pred_idx = probs.argmax()
            pred_category = classes[pred_idx]
            confidence = float(probs[pred_idx])
            probabilities = {str(c): round(float(p) * 100, 1) for c, p in zip(classes, probs)}
            is_ml = True

            # Extract token contributions for the predicted class
            vector = tfidf.transform([text])
            feature_names = tfidf.get_feature_names_out()
            feature_indices = vector.nonzero()[1]
            coefs = lr.coef_[pred_idx]
            
            tokens_with_weights = []
            for fi in feature_indices:
                score = vector[0, fi] * coefs[fi]
                if score > 0:
                    tokens_with_weights.append((feature_names[fi], round(float(score), 3)))
            
            tokens_with_weights.sort(key=lambda x: x[1], reverse=True)
            contributing_tokens = tokens_with_weights[:6]

            # Security override guard
            if "Security" in matches and pred_category != "Security":
                sec_kws = ["phishing", "malware", "breach", "unauthorized", "compromised"]
                if any(k in text.lower() for k in sec_kws):
                    pred_category = "Security"
                    confidence = 0.95
                    why = "Security override: high-risk security indicators detected in complaint text."
            
            matched_kws = matches.get(pred_category, [])
        except Exception as ex:
            is_ml = False

    if not is_ml:
        pred_category = categorize(text)
        matched_kws = matches.get(pred_category, [])
        confidence = 0.88 if matched_kws else 0.50
        probabilities = {pred_category: round(confidence * 100, 1)}

    kws_formatted = [format_keyword_name(k) for k in matched_kws]
    
    if is_ml:
        token_str = ", ".join([f"'{t[0]}' (+{t[1]})" for t in contributing_tokens[:3]])
        why = f"Classified as {pred_category} with {confidence*100:.1f}% ML model confidence."
        if token_str:
            why += f" Key influential terms: {token_str}."
    elif matched_kws:
        why = f"Classified as {pred_category} based on matched domain keywords: {', '.join(kws_formatted)}."
    else:
        why = "No specific category keywords detected. Assigned to General triage."

    return {
        "category": pred_category,
        "confidence": confidence,
        "confidence_pct": f"{confidence * 100:.1f}%",
        "probabilities": probabilities,
        "matched_keywords": kws_formatted,
        "contributing_tokens": contributing_tokens,
        "is_ml": is_ml,
        "why": why
    }


def format_keyword_name(kw: str) -> str:
    """Format keywords for display (e.g., VPN, Wi-Fi, Outlook)."""
    special_caps = {
        "vpn": "VPN",
        "wifi": "WiFi",
        "wi-fi": "Wi-Fi",
        "dns": "DNS",
        "outlook": "Outlook",
        "excel": "Excel",
        "word": "Word",
        "powerpoint": "PowerPoint"
    }
    return special_caps.get(kw.lower(), kw)


def explain_category(text: str) -> str:
    """
    Return human-readable explanation with matched category, ML confidence, and keywords.
    """
    exp = predict_category_with_explanation(text)
    cat = exp["category"]
    conf = exp["confidence_pct"]
    kws = exp["matched_keywords"]
    
    if exp.get("is_ml"):
        tokens = exp.get("contributing_tokens", [])
        tok_str = f" | Influential tokens: {', '.join([t[0] for t in tokens[:3]])}" if tokens else ""
        return f"Category: {cat} (ML Confidence: {conf}{tok_str})"
    elif kws:
        return f"Category: {cat} (Matched keywords: {', '.join(kws)})"
    else:
        return f"Category: {cat} (Keyword fallback: no specific terms detected)"
