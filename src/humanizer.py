import os
import re
import logging
from dotenv import load_dotenv
from src.utils import clean_text, count_words
from src.scorer import get_ai_score

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Rule-based replacement maps ---

AI_TO_HUMAN_PHRASES = {
    "it is important to note"   : "worth mentioning",
    "it is worth noting"        : "something to keep in mind",
    "it is essential"           : "you really need",
    "it is imperative"          : "it is critical",
    "it is clear that"          : "clearly",
    "needless to say"           : "obviously",
    "in today's world"          : "these days",
    "in today's society"        : "nowadays",
    "plays a crucial role"      : "matters a lot",
    "delve into"                : "dig into",
    "underscore"                : "highlight",
    "utilize"                   : "use",
    "furthermore"               : "also",
    "moreover"                  : "on top of that",
    "additionally"              : "and",
    "in conclusion"             : "to wrap up",
    "in summary"                : "so basically",
    "to summarize"              : "in short",
    "one must consider"         : "you should think about",
    "it is worth considering"   : "think about",
}

CONTRACTIONS = {
    "it is"     : "it's",
    "that is"   : "that's",
    "there is"  : "there's",
    "they are"  : "they're",
    "we are"    : "we're",
    "you are"   : "you're",
    "i am"      : "i'm",
    "do not"    : "don't",
    "does not"  : "doesn't",
    "did not"   : "didn't",
    "will not"  : "won't",
    "would not" : "wouldn't",
    "could not" : "couldn't",
    "should not": "shouldn't",
    "is not"    : "isn't",
    "are not"   : "aren't",
    "was not"   : "wasn't",
    "were not"  : "weren't",
    "have not"  : "haven't",
    "has not"   : "hasn't",
    "had not"   : "hadn't",
    "cannot"    : "can't",
}


def apply_rule_based_fixes(text: str) -> str:
    """Layer 1: Apply deterministic rule-based humanization.
    
    This runs even without an API key and handles the most
    obvious AI tells — formal phrases and missing contractions.
    """
    result = text

    # Replace AI phrases
    for ai_phrase, human_phrase in AI_TO_HUMAN_PHRASES.items():
        pattern = re.compile(re.escape(ai_phrase), re.IGNORECASE)
        result = pattern.sub(human_phrase, result)

    # Apply contractions (lowercase match, preserve sentence start capitals)
    for formal, contraction in CONTRACTIONS.items():
        pattern = re.compile(r'\b' + re.escape(formal) + r'\b', re.IGNORECASE)
        result = pattern.sub(contraction, result)

    return clean_text(result)


def build_humanize_prompt(text: str) -> str:
    """Build the LLM prompt for humanization.
    
    The prompt is the most important part of this project.
    It instructs the LLM to rewrite in a specific human style
    while preserving the original meaning completely.
    """
    return f"""You are a writing expert who specializes in making AI-generated text sound completely human.

Rewrite the following text so it sounds like a real person wrote it. Follow these rules strictly:

1. VARY sentence lengths dramatically — mix short punchy sentences with longer ones
2. Use contractions naturally (it's, don't, you're, that's)
3. Add subtle imperfections — a casual phrase, a mild opinion, a natural aside
4. Replace formal transitions (furthermore, moreover, additionally) with casual ones (also, plus, and, but)
5. Remove all classic AI phrases like "it is important to note", "delve into", "plays a crucial role"
6. Keep the exact same meaning and all factual information
7. Do NOT add information that wasn't in the original
8. Write in first or second person where natural
9. Aim for a conversational but intelligent tone
10. Output ONLY the rewritten text — no explanations, no preamble

Original text:
{text}

Rewritten human version:"""


def humanize_with_llm(text: str) -> str:
    """Layer 2: Use Groq LLM to rewrite text in human voice."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": build_humanize_prompt(text)}],
            temperature=0.85,   # higher = more creative and varied
            max_tokens=2048
        )
        result = response.choices[0].message.content.strip()
        logger.info("LLM humanization complete")
        return result

    except Exception as e:
        logger.warning(f"LLM humanization failed: {e}. Falling back to rule-based.")
        return None


def humanize_text(text: str) -> dict:
    """Main humanization function called by the MCP server.

    1. Score original text
    2. Apply rule-based fixes
    3. Apply LLM rewrite if API key available
    4. Score final text
    5. Return full report
    """
    if count_words(text) < 20:
        return {
            "error": "Text is too short. Please provide at least 20 words."
        }

    logger.info(f"Humanizing text ({count_words(text)} words)")

    # Score original
    original_score = get_ai_score(text)

    # Layer 1: rule-based
    fixed_text = apply_rule_based_fixes(text)

    # Layer 2: LLM rewrite (if API key present)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        llm_result = humanize_with_llm(fixed_text)
        final_text = llm_result if llm_result else fixed_text
        method = "llm + rules"
    else:
        final_text = fixed_text
        method = "rules only (no GROQ_API_KEY found)"
        logger.warning("No GROQ_API_KEY found. Using rule-based humanization only.")

    # Score final
    final_score = get_ai_score(final_text)

    improvement = original_score["score"] - final_score["score"]

    return {
        "original_text"   : text,
        "humanized_text"  : final_text,
        "original_score"  : original_score["score"],
        "final_score"     : final_score["score"],
        "improvement"     : improvement,
        "method"          : method,
        "original_label"  : original_score["label"],
        "final_label"     : final_score["label"],
        "message"         : f"Reduced AI score from {original_score['score']}% to {final_score['score']}% (improved by {improvement} points)"
    }