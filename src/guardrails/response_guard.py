import re


ADMINISTRATION_PATTERNS = [
    (r"\bwas administered\b", "was documented"),
    (r"\bwere administered\b", "were documented"),
    (r"\badministered\b", "documented"),
    (r"\bwas given\b", "was documented"),
    (r"\bwere given\b", "were documented"),
    (r"\bwas received\b", "was documented"),
    (r"\bwere received\b", "were documented"),
]


COMPLETENESS_SENTENCE_PATTERNS = [
    r"[^.!?\n]*\bno other\b[^.!?\n]*[.!?]?",
    r"[^.!?\n]*\bnone other\b[^.!?\n]*[.!?]?",
    r"[^.!?\n]*\bnothing else\b[^.!?\n]*[.!?]?",
    r"[^.!?\n]*\bno additional\b[^.!?\n]*[.!?]?",
]


def sanitize_clinical_answer(answer: str) -> str:
    if not answer:
        return answer

    sanitized = answer

    # Prevent unsupported claims of medication administration.
    for pattern, replacement in ADMINISTRATION_PATTERNS:
        sanitized = re.sub(
            pattern,
            replacement,
            sanitized,
            flags=re.IGNORECASE,
        )

    # Remove entire unsupported completeness sentences.
    # This is safer than removing only the phrase "no other".
    for pattern in COMPLETENESS_SENTENCE_PATTERNS:
        sanitized = re.sub(
            pattern,
            "",
            sanitized,
            flags=re.IGNORECASE,
        )

    # Clean excessive whitespace while preserving paragraph structure.
    sanitized = re.sub(r"[ \t]+", " ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

    return sanitized.strip()
