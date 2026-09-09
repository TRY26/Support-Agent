"""
Policy-driven Escalation Decision Engine for Customer Support.
Evaluates incoming queries against safety, PII, financial, and frustration policies
to decide: AUTO_HANDLE vs ESCALATE_HUMAN with a concrete stated reason.
"""

import re
from src.config import ESCALATION_CATEGORIES
from src.data_loader import clean_tweet_text

class EscalationDecisionEngine:
    """
    Evaluates customer tweet, predicted intent, and risk signals
    to determine if the query should be auto-handled or escalated to a human.
    """
    def __init__(self):
        # Trigger rules for each escalation category
        self.security_pii_triggers = [
            "hacked", "compromised", "stolen", "unauthorized login", "russian domain",
            "gift card", "disabled for security", "service unavailable", "former employer",
            "activation lock", "previous owner", "lost my phone", "can't access your phone"
        ]

        self.hardware_damage_triggers = [
            "shattered", "cracked", "ink bleeding", "swollen", "bulging", "liquid",
            "fell into", "pool", "water", "crackling speaker", "green line", "sensor cracked",
            "won't turn on at all", "completely dead", "trackpad up", "displaced display"
        ]

        self.billing_dispute_triggers = [
            "dispute", "charged 6 times", "denied my refund", "denied my appeal", "appeal",
            "speak to a supervisor", "unauthorized charge", "fix this now", "charged twice",
            "cancelled during the free trial", "cancelled during the trial", "refund bot denied"
        ]

        self.frustration_repetition_triggers = [
            "already done", "already tried", "tried 3 times", "tried 4 times", "4 force restarts",
            "error 4013", "error 9", "kernel panic", "panic-full", "bootloop", "restarted 15 times",
            "wiped my iphone"
        ]

        self.legal_brand_risk_triggers = [
            "lawyer", "lawsuit", "police", "shoplifting", "consumer protection", "press",
            "insulted me", "refused to honor"
        ]

    def evaluate(self, customer_text: str, predicted_intent: str, confidence: float) -> dict:
        """
        Evaluates the message and returns:
            should_escalate: bool
            escalation_category: str
            escalation_reason: str
            risk_level: str ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        """
        text_lower = clean_tweet_text(customer_text).lower()

        # 1. Critical Account Security & PII Triggers
        for trigger in self.security_pii_triggers:
            if trigger in text_lower:
                return {
                    "should_escalate": True,
                    "escalation_category": "ACCOUNT_SECURITY_PII",
                    "escalation_reason": f"Customer reported sensitive credential or account risk ('{trigger}'). PII and account recovery must be handled via secure private DM or human specialist.",
                    "risk_level": "CRITICAL"
                }

        # 2. Urgent Hardware Damage & Battery Safety Triggers
        for trigger in self.hardware_damage_triggers:
            if trigger in text_lower:
                category = "HARDWARE_DAMAGE_REPAIR"
                if "swollen" in trigger or "bulging" in trigger:
                    reason = "Potential swollen battery represents an acute safety hazard requiring immediate discontinuation of charging and urgent in-person hardware evaluation."
                    risk = "CRITICAL"
                else:
                    reason = f"Physical damage or hardware failure detected ('{trigger}'). Automated troubleshooting cannot repair physical components; requires Genius Bar or mail-in service."
                    risk = "MEDIUM"
                return {
                    "should_escalate": True,
                    "escalation_category": category,
                    "escalation_reason": reason,
                    "risk_level": risk
                }

        # 3. Financial Escalation & Disputed Refunds
        for trigger in self.billing_dispute_triggers:
            if trigger in text_lower:
                return {
                    "should_escalate": True,
                    "escalation_category": "BILLING_REFUND_DISPUTE",
                    "escalation_reason": f"Customer expresses billing dispute or unauthorized repeated charges ('{trigger}'). Financial adjustments and appeal reviews require human billing authorization.",
                    "risk_level": "HIGH"
                }

        # 4. Repeated Failed Troubleshooting / Diagnostic Exhaustion
        for trigger in self.frustration_repetition_triggers:
            if trigger in text_lower:
                return {
                    "should_escalate": True,
                    "escalation_category": "REPEATED_FAILED_TROUBLESHOOTING",
                    "escalation_reason": f"Customer has already exhausted self-service troubleshooting ('{trigger}'). Repeating automated steps would cause acute customer dissatisfaction; transferring to senior technical advisor.",
                    "risk_level": "HIGH"
                }

        # 5. Legal Threats & High-Risk Brand Complaints
        for trigger in self.legal_brand_risk_triggers:
            if trigger in text_lower:
                return {
                    "should_escalate": True,
                    "escalation_category": "AMBIGUOUS_COMPLAINT",
                    "escalation_reason": f"Customer raises legal, ethical, or high-severity brand compliance concerns ('{trigger}'). Requires immediate escalation to executive relations.",
                    "risk_level": "CRITICAL"
                }

        # 6. Intent-specific policy defaults
        if predicted_intent == "ACCOUNT_APPLE_ID_SECURITY" and ("locked" in text_lower or "disabled" in text_lower):
            return {
                "should_escalate": True,
                "escalation_category": "ACCOUNT_SECURITY_PII",
                "escalation_reason": "Locked Apple ID account requires identity verification in secure private channels.",
                "risk_level": "MEDIUM"
            }

        # 7. Safe to Auto-Handle (Default)
        return {
            "should_escalate": False,
            "escalation_category": "NONE_SAFE_TO_AUTOHANDLE",
            "escalation_reason": "Standard self-service query covered by official Apple Support diagnostic workflows. Safe to auto-handle without PII or human intervention.",
            "risk_level": "LOW"
        }
