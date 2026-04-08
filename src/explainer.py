import re
import logging
from src.utils import (
    split_sentences,
    count_words,
    sentence_length_variance,
    vocabulary_diversity
)
from src.scorer import AI_PHRASES, HUMAN_FILLER_WORDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Reasons why each type of change improves human score
CHANGE_REASONS = {
    "ai_phrase"        : "Classic AI phrase removed — these are strong signals for AI detectors",
    "contraction"      : "Contraction added — humans naturally shorten words in conversation",
    "sentence_split"   : "Long sentence broken up — humans write shorter, punchier sentences",
    "transition"       : "Formal transition replaced — words like 'furthermore' are almost never used in human writing",
    "vocabulary"       : "Word simplified — AI tends to use overly formal vocabulary",
    "filler_added"     : "Human filler word added — gives text a natural conversational tone",
}


def find_removed_ai_phrases(original: str, humanized: str) -> list[dict]:
    """Detect which AI phrases were removed during humanization."""
    changes = []
    original_lower = original.lower()
    humanized_lower = humanized.lower()

    for phrase in AI_PHRASES:
        if phrase in original_lower and phrase not in humanized_lower:
            changes.append({
                "type"   : "ai_phrase",
                "removed": phrase,
                "reason" : CHANGE_REASONS["ai_phrase"]
            })
    return changes


def find_added_contractions(original: str, humanized: str) -> list[dict]:
    """Detect contractions that were added during humanization."""
    contractions = [
        "it's", "that's", "there's", "they're", "we're",
        "you're", "i'm", "don't", "doesn't", "didn't",
        "won't", "wouldn't", "couldn't", "shouldn't",
        "isn't", "aren't", "wasn't", "weren't",
        "haven't", "hasn't", "hadn't", "can't"
    ]
    changes = []
    original_lower = original.lower()
    humanized_lower = humanized.lower()

    for contraction in contractions:
        if contraction not in original_lower and contraction in humanized_lower:
            changes.append({
                "type"   : "contraction",
                "added"  : contraction,
                "reason" : CHANGE_REASONS["contraction"]
            })
    return changes


def find_added_fillers(original: str, humanized: str) -> list[dict]:
    """Detect human filler words that were added."""
    changes = []
    original_lower = original.lower()
    humanized_lower = humanized.lower()

    for filler in HUMAN_FILLER_WORDS:
        if filler not in original_lower and filler in humanized_lower:
            changes.append({
                "type"   : "filler_added",
                "added"  : filler,
                "reason" : CHANGE_REASONS["filler_added"]
            })
    return changes


def compare_sentence_variance(original: str, humanized: str) -> dict | None:
    """Compare sentence length variance before and after."""
    orig_var  = sentence_length_variance(original)
    human_var = sentence_length_variance(humanized)

    if human_var > orig_var + 2:
        return {
            "type"    : "sentence_variance",
            "before"  : orig_var,
            "after"   : human_var,
            "reason"  : "Sentence length variation increased — more natural rhythm"
        }
    return None


def compare_vocabulary(original: str, humanized: str) -> dict | None:
    """Compare vocabulary diversity before and after."""
    orig_div  = vocabulary_diversity(original)
    human_div = vocabulary_diversity(humanized)

    if human_div > orig_div + 0.05:
        return {
            "type"   : "vocabulary",
            "before" : orig_div,
            "after"  : human_div,
            "reason" : CHANGE_REASONS["vocabulary"]
        }
    return None


def generate_summary(original_score: int, final_score: int, changes: list) -> str:
    """Generate a plain English summary of the humanization."""
    improvement = original_score - final_score
    n_changes   = len(changes)

    if improvement <= 0:
        return (f"The text was already scoring low on AI detection ({original_score}%). "
                f"Minor adjustments were made but significant improvement wasn't needed.")

    if final_score <= 20:
        quality = "excellent — the text now reads as fully human"
    elif final_score <= 40:
        quality = "good — the text reads as mostly human with minimal AI signals"
    elif final_score <= 60:
        quality = "moderate — some AI patterns remain, consider revising further"
    else:
        quality = "limited — the text still has significant AI patterns"

    return (f"Made {n_changes} changes that reduced the AI score from {original_score}% "
            f"to {final_score}% (improvement of {improvement} points). "
            f"Overall result: {quality}.")


def explain_changes(original: str, humanized: str,
                    original_score: int, final_score: int) -> dict:
    """Full explanation of all changes made during humanization.

    Called by the MCP server after humanization is complete.
    Returns a structured report with every change and its reason.
    """
    logger.info("Generating change explanation")

    # Collect all changes
    changes = []
    changes.extend(find_removed_ai_phrases(original, humanized))
    changes.extend(find_added_contractions(original, humanized))
    changes.extend(find_added_fillers(original, humanized))

    variance_change = compare_sentence_variance(original, humanized)
    if variance_change:
        changes.append(variance_change)

    vocab_change = compare_vocabulary(original, humanized)
    if vocab_change:
        changes.append(vocab_change)

    summary = generate_summary(original_score, final_score, changes)

    return {
        "summary"        : summary,
        "total_changes"  : len(changes),
        "changes"        : changes,
        "original_score" : original_score,
        "final_score"    : final_score,
        "improvement"    : original_score - final_score,
        "tip"            : "To further reduce AI score: vary your sentence lengths, use contractions, and add personal opinions or anecdotes."
    }