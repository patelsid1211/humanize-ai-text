import re
import textstat
from src.utils import (
    split_sentences,
    split_words,
    sentence_length_variance,
    vocabulary_diversity,
    count_sentences,
    count_words
)

# Words humans naturally use but AI almost never does
HUMAN_FILLER_WORDS = [
    "honestly", "actually", "basically", "literally", "seriously",
    "look", "listen", "okay", "yeah", "nope", "pretty much",
    "kind of", "sort of", "you know", "i mean", "thing is",
    "to be fair", "at the end of the day", "anyway", "so yeah"
]

# Phrases that are strong AI signals
AI_PHRASES = [
    "it is important to note", "it is worth noting",
    "in conclusion", "in summary", "to summarize",
    "furthermore", "moreover", "additionally",
    "it is essential", "one must consider",
    "plays a crucial role", "it is imperative",
    "in today's world", "in today's society",
    "delve into", "underscore", "utilize",
    "it is clear that", "needless to say"
]


def score_sentence_variance(text: str) -> float:
    """Score based on sentence length variance.
    
    Low variance = AI (score close to 1.0)
    High variance = Human (score close to 0.0)
    """
    variance = sentence_length_variance(text)
    if variance >= 30:
        return 0.0   # very human
    elif variance >= 15:
        return 0.25
    elif variance >= 8:
        return 0.50
    elif variance >= 3:
        return 0.75
    else:
        return 1.0   # very AI


def score_vocabulary(text: str) -> float:
    """Score based on vocabulary diversity.

    Low diversity = AI (score close to 1.0)
    High diversity = Human (score close to 0.0)
    """
    diversity = vocabulary_diversity(text)
    if diversity >= 0.80:
        return 0.0
    elif diversity >= 0.65:
        return 0.25
    elif diversity >= 0.50:
        return 0.50
    elif diversity >= 0.35:
        return 0.75
    else:
        return 1.0


def score_readability(text: str) -> float:
    """Score based on Flesch reading ease.

    AI tends to write at a very consistent, formal reading level.
    Humans vary more and often write more casually.
    """
    score = textstat.flesch_reading_ease(text)
    if score >= 70:
        return 0.0   # easy/casual = human
    elif score >= 50:
        return 0.25
    elif score >= 30:
        return 0.60
    else:
        return 1.0   # very formal = AI


def score_ai_phrases(text: str) -> float:
    """Score based on presence of known AI phrases.

    Counts how many classic AI phrases appear in the text.
    """
    text_lower = text.lower()
    found = sum(1 for phrase in AI_PHRASES if phrase in text_lower)
    if found == 0:
        return 0.0
    elif found == 1:
        return 0.40
    elif found == 2:
        return 0.70
    else:
        return 1.0


def score_human_fillers(text: str) -> float:
    """Score based on absence of human filler words.

    If no human filler words found, more likely AI.
    """
    text_lower = text.lower()
    found = sum(1 for word in HUMAN_FILLER_WORDS if word in text_lower)
    if found >= 3:
        return 0.0   # very human
    elif found == 2:
        return 0.25
    elif found == 1:
        return 0.50
    else:
        return 0.90  # no fillers = likely AI


def get_ai_score(text: str) -> dict:
    """Calculate overall AI likelihood score for the given text.

    Combines 5 signals with weights into a final score 0-100.
    Returns score, label, and breakdown of each signal.
    """
    if count_words(text) < 20:
        return {
            "score": -1,
            "label": "too_short",
            "message": "Text is too short for reliable scoring. Please provide at least 20 words.",
            "breakdown": {}
        }

    # Weighted signals
    signals = {
        "sentence_variance" : (score_sentence_variance(text),  0.30),
        "vocabulary"        : (score_vocabulary(text),         0.25),
        "readability"       : (score_readability(text),        0.20),
        "ai_phrases"        : (score_ai_phrases(text),         0.15),
        "human_fillers"     : (score_human_fillers(text),      0.10),
    }

    # Weighted average → scale to 0-100
    raw_score = sum(score * weight for score, weight in signals.values())
    final_score = round(raw_score * 100)

    # Label
    if final_score <= 20:
        label = "human"
    elif final_score <= 50:
        label = "mixed"
    elif final_score <= 80:
        label = "likely_ai"
    else:
        label = "ai"

    return {
        "score"    : final_score,
        "label"    : label,
        "message"  : f"This text is {final_score}% likely to be AI-generated.",
        "breakdown": {
            k: round(v[0] * 100) for k, v in signals.items()
        }
    }