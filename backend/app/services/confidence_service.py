def calculate_final_confidence(base_confidence: float, source_count: int, retrieval_quality: float, metadata_match_avg: float) -> float:
    # Input Sanitization
    base_confidence = float(base_confidence or 0.0)
    source_count = int(source_count or 0)
    retrieval_quality = float(retrieval_quality or 0.0)
    metadata_match_avg = float(metadata_match_avg or 0.0)

    # Clamp Values
    base_confidence = max(0.0, min(base_confidence, 1.0))
    retrieval_quality = max(0.0, min(retrieval_quality, 1.0))
    metadata_match_avg = max(0.0, min(metadata_match_avg, 1.0))

    chunk_factor = min(1.0, source_count / 10)
    source_factor = min(1.0, source_count / 5)
    risk_penalty = max(0.0, min(1.0, 1.0 - ((retrieval_quality + metadata_match_avg) / 2.0)))

    final_confidence = min(
        1.0,
        (0.4 * chunk_factor) + (0.3 * source_factor) + (0.3 * (1 - risk_penalty)),
    )

    if source_count >= 2 and retrieval_quality >= 0.35:
        final_confidence = min(1.0, final_confidence + 0.03)

    return round(final_confidence, 4)

def determine_status(confidence: float) -> str:
    if confidence < 0.4:
        return "low_confidence"
    elif confidence < 0.7:
        return "moderate"
    else:
        return "high"
