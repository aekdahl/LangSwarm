def ensure_contains_keywords(text: str, keywords: list):
    missing = [kw for kw in keywords if kw.lower() not in text.lower()]
    if missing:
        raise ValueError(f"Missing required keywords: {', '.join(missing)}")
    return f"✅ Validation passed: contains {', '.join(keywords)}"
