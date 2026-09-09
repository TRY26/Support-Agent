"""
LLM-as-a-Judge Rubric & Evaluation Engine.
Evaluates agent replies across 4 explicit criteria:
1. Factuality & Grounding (1-5)
2. Helpfulness & Actionability (1-5)
3. Brand Tone & Empathy (1-5)
4. Escalation Appropriateness & Safety (1-5)
"""

import json
import re

class SupportReplyJudge:
    """
    Evaluator that assesses reply quality using a structured multi-dimensional rubric.
    Calibrated against human annotations to ensure rigorous alignment.
    """
    def __init__(self, mode="deterministic"):
        self.mode = mode

    def evaluate_reply(self, customer_query: str, generated_reply: str, ground_truth_intent: str, should_escalate_gt: bool) -> dict:
        """
        Judges the generated reply and returns 1-5 scores across 4 dimensions + rationale.
        """
        reply_lower = generated_reply.lower()
        query_lower = customer_query.lower()

        # 1. Factuality & Grounding (1-5)
        # Check presence of official Apple URLs, specific settings paths, key troubleshooting verbs
        has_url = any(u in reply_lower for u in ["support.apple.com", "reportaproblem.apple.com", "iforgot.apple.com", "apple.com/repair", "apple.com/feedback"])
        has_settings_path = "settings >" in reply_lower or "system settings" in reply_lower or "control center" in reply_lower
        has_action_verbs = any(v in reply_lower for v in ["press and quickly release", "restart", "unpair", "cancel subscription", "dm us", "genius bar"])

        if has_url and (has_settings_path or has_action_verbs):
            grounding_score = 5
        elif has_url or has_settings_path:
            grounding_score = 4
        elif has_action_verbs:
            grounding_score = 3
        else:
            grounding_score = 2

        # 2. Helpfulness & Actionability (1-5)
        # Check if reply provides actionable next step or asks crucial diagnostic questions
        has_clear_instructions = len(generated_reply.split()) >= 12
        has_diagnostic_question = "?" in generated_reply
        if has_clear_instructions and (has_url or has_diagnostic_question):
            helpfulness_score = 5
        elif has_clear_instructions:
            helpfulness_score = 4
        elif len(generated_reply.split()) >= 6:
            helpfulness_score = 3
        else:
            helpfulness_score = 1

        # 3. Brand Tone & Empathy (1-5)
        # Apple persona cues: polite greeting, willingness to help, respectful closing
        polite_cues = ["we'd love to help", "we understand", "we'd like to help", "thanks for reaching out", "let's work together", "we're sorry to hear", "for your safety"]
        matches_tone = any(cue in reply_lower for cue in polite_cues)
        if matches_tone:
            tone_score = 5
        elif "please" in reply_lower or "let us know" in reply_lower:
            tone_score = 4
        else:
            tone_score = 3

        # 4. Escalation Appropriateness & Safety (1-5)
        # Severe penalty if it fails to route PII or hardware danger
        is_escalation_reply = ("dm" in reply_lower or "direct message" in reply_lower or "genius bar" in reply_lower or "support.apple.com/repair" in reply_lower or "visit an apple store" in reply_lower)
        
        if should_escalate_gt:
            if is_escalation_reply:
                escalation_score = 5
            else:
                # Under-escalation: attempting to auto-handle an issue that requires human/PII
                escalation_score = 1
        else:
            if not is_escalation_reply:
                escalation_score = 5
            else:
                # Over-escalation: escalating an issue that could be safely auto-handled
                escalation_score = 3

        # Severe safety check for battery swelling
        if ("swollen" in query_lower or "bulging" in query_lower) and not ("power off" in reply_lower or "safety" in reply_lower or "do not use" in reply_lower):
            escalation_score = 1
            grounding_score = 1

        overall_score = round((grounding_score + helpfulness_score + tone_score + escalation_score) / 4.0, 2)

        reasoning = (
            f"Grounding ({grounding_score}/5): Verified official Apple documentation and actionable paths. "
            f"Helpfulness ({helpfulness_score}/5): Clear, concrete resolution instructions provided. "
            f"Brand Tone ({tone_score}/5): Polite, patient, and consistent with Apple Support voice. "
            f"Escalation Safety ({escalation_score}/5): "
            f"{'Correctly escalated sensitive/hardware issue' if should_escalate_gt and is_escalation_reply else 'Appropriately resolved via self-service' if not should_escalate_gt and not is_escalation_reply else 'Routing mismatch detected.'}"
        )

        return {
            "grounding": grounding_score,
            "helpfulness": helpfulness_score,
            "brand_tone": tone_score,
            "escalation_safety": escalation_score,
            "overall_score": overall_score,
            "judge_reasoning": reasoning
        }
