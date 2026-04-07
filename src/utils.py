import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data on first run
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)


def split_sentences(text: str) -> list[str]:
    """Split text into a list of sentences using NLTK."""
    return sent_tokenize(text.strip())


def split_words(text: str) -> list[str]:
    """Split text into individual words, excluding punctuation."""
    tokens = word_tokenize(text.lower())
    return [t for t in tokens if t.isalpha()]


def count_sentences(text: str) -> int:
    """Return number of sentences in text."""
    return len(split_sentences(text))


def count_words(text: str) -> int:
    """Return number of words in text."""
    return len(split_words(text))


def avg_sentence_length(text: str) -> float:
    """Return average number of words per sentence.
    
    AI text tends to have very consistent sentence lengths.
    High variance = more human. Low variance = more AI.
    """
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    lengths = [len(split_words(s)) for s in sentences]
    return sum(lengths) / len(lengths)


def sentence_length_variance(text: str) -> float:
    """Return variance in sentence lengths.

    This is one of the strongest signals for AI detection.
    Humans naturally write short punchy sentences followed by
    longer more detailed ones. AI tends to keep lengths uniform.
    """
    sentences = split_sentences(text)
    if len(sentences) < 2:
        return 0.0
    lengths = [len(split_words(s)) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return round(variance, 2)


def vocabulary_diversity(text: str) -> float:
    """Return ratio of unique words to total words (Type-Token Ratio).

    Higher TTR = more diverse vocabulary = more human.
    AI text often repeats the same words and phrases.
    Score range: 0.0 to 1.0
    """
    words = split_words(text)
    if not words:
        return 0.0
    return round(len(set(words)) / len(words), 4)


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize line breaks."""
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()


def word_count_display(text: str) -> str:
    """Return a human readable word and sentence count summary."""
    w = count_words(text)
    s = count_sentences(text)
    return f"{w} words, {s} sentences"