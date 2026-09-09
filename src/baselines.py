"""
Baseline Systems for Comparative Evaluation.
Mandatory assignment requirement: At least two baselines (a trivial one and a simple one).

1. Trivial Baseline:
   - Naive regex keyword intent matching
   - Static keyword escalation rule (if 'refund', 'broken', 'scam', 'lawyer')
   - Static canned response per intent

2. Simple Baseline:
   - Retrieval-only (BM25 nearest neighbor reply copied verbatim)
   - BM25 nearest neighbor intent adoption
   - Similarity threshold escalation (escalate if top BM25 score < 1.5)
"""

from src.retriever import HybridSupportRetriever
from src.data_loader import clean_tweet_text
from src.config import INTENTS

class TrivialBaselineAgent:
    """
    Trivial baseline: Keyword regex intent + static escalation keywords + canned responses.
    """
    def __init__(self):
        self.canned_responses = {
            "SOFTWARE_OS_TROUBLESHOOTING": "Thanks for reaching out! Please restart your device and visit https://support.apple.com for more help.",
            "HARDWARE_BATTERY_REPAIR": "We're sorry to hear about your hardware issue. Please visit an Apple Store Genius Bar for assistance.",
            "ACCOUNT_APPLE_ID_SECURITY": "For Apple ID and password issues, please visit https://iforgot.apple.com.",
            "BILLING_SUBSCRIPTIONS_REFUNDS": "For billing issues or refunds, please sign in to https://reportaproblem.apple.com.",
            "DEVICE_SETUP_COMPATIBILITY": "To transfer data to a new device, please use Quick Start or iCloud backup.",
            "OUT_OF_SCOPE_FEEDBACK_RANT": "Thank you for your feedback regarding Apple products. Have a nice day!"
        }

    def process(self, customer_tweet: str) -> dict:
        text_lower = clean_tweet_text(customer_tweet).lower()

        # Trivial regex intent heuristic
        if any(w in text_lower for w in ["apple id", "password", "locked", "2fa", "security"]):
            intent = "ACCOUNT_APPLE_ID_SECURITY"
        elif any(w in text_lower for w in ["refund", "charge", "bill", "subscription", "money"]):
            intent = "BILLING_SUBSCRIPTIONS_REFUNDS"
        elif any(w in text_lower for w in ["battery", "screen", "cracked", "broken", "hardware", "dropped"]):
            intent = "HARDWARE_BATTERY_REPAIR"
        elif any(w in text_lower for w in ["new phone", "transfer", "pair", "watch", "setup"]):
            intent = "DEVICE_SETUP_COMPATIBILITY"
        elif any(w in text_lower for w in ["freeze", "wifi", "bluetooth", "update", "crash", "bug"]):
            intent = "SOFTWARE_OS_TROUBLESHOOTING"
        else:
            intent = "OUT_OF_SCOPE_FEEDBACK_RANT"

        # Trivial escalation heuristic (keyword search)
        escalate_keywords = ["human", "agent", "refund", "lawyer", "police", "scam", "stolen", "broken", "shattered", "supervisor"]
        should_escalate = any(k in text_lower for k in escalate_keywords)

        return {
            "predicted_intent": intent,
            "should_escalate": should_escalate,
            "escalation_reason": "Trivial keyword match detected." if should_escalate else "No escalation keywords found.",
            "drafted_reply": self.canned_responses.get(intent, self.canned_responses["SOFTWARE_OS_TROUBLESHOOTING"])
        }

class SimpleBaselineAgent:
    """
    Simple baseline: Pure BM25 nearest-neighbor retrieval.
    - Adopts top historical match's intent
    - Copies top historical reply verbatim without synthesis
    - Escalates if similarity score is below cutoff threshold
    """
    def __init__(self, confidence_cutoff=1.5):
        self.retriever = HybridSupportRetriever()
        self.confidence_cutoff = confidence_cutoff

    def process(self, customer_tweet: str) -> dict:
        cleaned = clean_tweet_text(customer_tweet)
        grounding = self.retriever.retrieve_grounding_context(cleaned, top_k=1)

        if grounding["top_historical_pairs"]:
            top_match = grounding["top_historical_pairs"][0]
            intent = top_match.get("intent", "SOFTWARE_OS_TROUBLESHOOTING")
            drafted_reply = top_match.get("reply", "Please visit https://support.apple.com for help.")
            score = top_match.get("score", 0.0)
            
            # Escalate if retrieval confidence is weak
            should_escalate = (score < self.confidence_cutoff)
            reason = f"BM25 retrieval similarity score ({score:.2f}) fell below confidence cutoff ({self.confidence_cutoff})." if should_escalate else "Sufficient historical match found."
        else:
            intent = "SOFTWARE_OS_TROUBLESHOOTING"
            drafted_reply = "Please visit https://support.apple.com for help."
            should_escalate = True
            reason = "No historical match found in knowledge base."

        return {
            "predicted_intent": intent,
            "should_escalate": should_escalate,
            "escalation_reason": reason,
            "drafted_reply": drafted_reply
        }
