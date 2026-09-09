"""
Data loader and text preprocessing routines for Twitter Customer Support.
"""

import json
import re
import os
from src.config import (
    KNOWLEDGE_BASE_PATH,
    HISTORICAL_CONVERSATIONS_PATH,
    GOLDEN_EVAL_PATH,
    HUMAN_CALIBRATION_PATH
)

def clean_tweet_text(text: str) -> str:
    """
    Cleans raw customer tweet text while preserving crucial technical tokens (iOS versions, error codes).
    - Removes Twitter @mentions (e.g. @AppleSupport, @115858)
    - Normalizes extra whitespace
    - Preserves URLs or replaces them cleanly
    """
    if not text:
        return ""
    
    # Remove @mentions
    cleaned = re.sub(r'@[A-Za-z0-9_]+', '', text)
    # Remove redundant whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def load_knowledge_base():
    """Loads curated official Apple Support articles."""
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        raise FileNotFoundError(f"Knowledge base not found at {KNOWLEDGE_BASE_PATH}")
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_historical_conversations():
    """Loads historical AppleSupport conversation pairs for grounding."""
    if not os.path.exists(HISTORICAL_CONVERSATIONS_PATH):
        raise FileNotFoundError(f"Historical conversations not found at {HISTORICAL_CONVERSATIONS_PATH}")
    with open(HISTORICAL_CONVERSATIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_golden_eval_set():
    """Loads the 200 hand-labelled golden test set."""
    if not os.path.exists(GOLDEN_EVAL_PATH):
        raise FileNotFoundError(f"Golden evaluation set not found at {GOLDEN_EVAL_PATH}")
    with open(GOLDEN_EVAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_human_calibration():
    """Loads the 50 human-rated query-reply calibration items."""
    if not os.path.exists(HUMAN_CALIBRATION_PATH):
        raise FileNotFoundError(f"Human calibration data not found at {HUMAN_CALIBRATION_PATH}")
    with open(HUMAN_CALIBRATION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
