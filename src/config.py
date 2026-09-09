"""
Configuration, Taxonomy, and Constants for AppleSupport AI Agent.
"""

import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "report")

# Data File Paths
KNOWLEDGE_BASE_PATH = os.path.join(DATA_DIR, "knowledge_base.json")
HISTORICAL_CONVERSATIONS_PATH = os.path.join(DATA_DIR, "historical_conversations.json")
GOLDEN_EVAL_PATH = os.path.join(DATA_DIR, "golden_eval_set.json")
HUMAN_CALIBRATION_PATH = os.path.join(DATA_DIR, "human_calibration_50.json")

# Intent Taxonomy (6 Classes derived from AppleSupport Twitter domain)
INTENTS = [
    "SOFTWARE_OS_TROUBLESHOOTING",
    "HARDWARE_BATTERY_REPAIR",
    "ACCOUNT_APPLE_ID_SECURITY",
    "BILLING_SUBSCRIPTIONS_REFUNDS",
    "DEVICE_SETUP_COMPATIBILITY",
    "OUT_OF_SCOPE_FEEDBACK_RANT"
]

INTENT_DESCRIPTIONS = {
    "SOFTWARE_OS_TROUBLESHOOTING": "iOS/macOS freezes, app crashes, Wi-Fi/Bluetooth issues, battery drain after update, Safari lag.",
    "HARDWARE_BATTERY_REPAIR": "Cracked screens, battery swelling or replacement, water damage, broken camera, speaker distortion, repair appointments.",
    "ACCOUNT_APPLE_ID_SECURITY": "Locked Apple ID, forgotten password, two-factor auth (2FA), Activation Lock, compromised account, phishing alerts.",
    "BILLING_SUBSCRIPTIONS_REFUNDS": "App Store charges, accidental purchases, subscription cancellation, refund requests, billing disputes.",
    "DEVICE_SETUP_COMPATIBILITY": "Quick Start transfer, restoring from backup, Apple Watch pairing, accessory compatibility, charger questions.",
    "OUT_OF_SCOPE_FEEDBACK_RANT": "General brand feedback, non-actionable complaints, jokes, praises, spam, or non-technical queries."
}

# Escalation Categories and Policies
ESCALATION_CATEGORIES = [
    "NONE_SAFE_TO_AUTOHANDLE",
    "ACCOUNT_SECURITY_PII",
    "HARDWARE_DAMAGE_REPAIR",
    "BILLING_REFUND_DISPUTE",
    "REPEATED_FAILED_TROUBLESHOOTING",
    "AMBIGUOUS_COMPLAINT"
]

# Cost weights for Escalation Decision Evaluation
# Sending a high-risk security/billing issue to an auto-bot (False Negative) is 5x more harmful than unnecessary escalation (False Positive)
COST_WEIGHT_FALSE_AUTO_HANDLE = 5.0
COST_WEIGHT_FALSE_ESCALATION = 1.0

# LLM & Generation Configuration
DEFAULT_MODEL = "offline"  # 'offline', 'groq', 'openai', 'gemini'
TWITTER_CHAR_LIMIT = 280
