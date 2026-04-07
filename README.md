# humanize-ai-text
MCP connector for Claude that humanizes AI-generated text to 0% AI detection
# Humanize AI Text

An MCP server for Claude that rewrites AI-generated text to sound fully human, targeting 0% AI detection score.

---

## What it does

- Rewrites AI-generated text using natural vocabulary, varied sentence structure, and human imperfections
- Scores how AI-like the input text sounds before and after humanization (0-100%)
- Explains exactly what was changed and why, so you can learn and improve your own writing
- Plugs directly into Claude Desktop as an MCP connector — no separate tool needed

---

## How it works

```
User pastes AI text into Claude
      └── Claude calls humanize_text tool
             └── MCP server rewrites it using
                 Groq LLM + linguistic rules
                        └── Returns humanized text
                               + before/after AI score
                               + change explanation
```

---

## Tools

| Tool | Description |
|---|---|
| `humanize_text` | Rewrites AI text to sound natural and human |
| `get_ai_score` | Scores how AI-like the text sounds (0-100%) |
| `explain_changes` | Shows what changed and why |

---

## Stack

| Layer | Tool |
|---|---|
| MCP server | Python, mcp SDK |
| LLM engine | Groq API (llama-3.3-70b) |
| Text analysis | nltk, textstat |
| Integration | Claude Desktop |

---

## Project Structure

```
humanize-ai-text/
├── src/
│   ├── server.py       # MCP server entry point, tool definitions
│   ├── humanizer.py    # Core humanization logic
│   ├── scorer.py       # AI detection scoring
│   ├── explainer.py    # Change explanation engine
│   └── utils.py        # Shared text utilities
├── tests/
│   ├── test_humanizer.py
│   └── test_scorer.py
├── docs/
│   └── technical.md
└── requirements.txt
```

---

## Setup

```bash
git clone https://github.com/patelsid1211/humanize-ai-text.git
cd humanize-ai-text
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your Groq API key to a `.env` file:
```
GROQ_API_KEY=gsk_...
```

---

## Status

In development — MCP server and humanization engine in progress.