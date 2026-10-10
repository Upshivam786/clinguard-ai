from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


DEFAULT_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IP_ADDRESS",
]


def redact_pii(text: str) -> str:
    """
    Detect and redact common PII before text is processed
    by the clinical RAG pipeline.
    """

    if not text:
        return text

    results = analyzer.analyze(
        text=text,
        entities=DEFAULT_ENTITIES,
        language="en",
    )

    if not results:
        return text

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={
            "DEFAULT": OperatorConfig(
                "replace",
                {
                    "new_value": "<REDACTED>",
                },
            )
        },
    )

    return anonymized.text
