"""
Core AI Support Agent for AppleSupport on Twitter.
Orchestrates Intent Classification -> Grounding Retrieval -> Escalation Policy -> Grounded Reply Drafting.
"""

from src.intent_classifier import RuleAndCentroidIntentClassifier
from src.retriever import HybridSupportRetriever
from src.escalation_engine import EscalationDecisionEngine
from src.data_loader import clean_tweet_text

class AppleSupportAgent:
    """
    Production-grade AI Support Agent for @AppleSupport.
    Handles incoming customer tweets with domain grounding, policy escalation, and brand tone.
    """
    def __init__(self):
        self.retriever = HybridSupportRetriever()
        self.classifier = RuleAndCentroidIntentClassifier()
        self.escalator = EscalationDecisionEngine()

    def process(self, customer_tweet: str) -> dict:
        """
        Executes end-to-end support triage and response generation:
        1. Classify intent
        2. Retrieve grounding historical resolutions & KB article
        3. Determine escalation policy & formulate stated reason
        4. Draft grounded response
        """
        cleaned_text = clean_tweet_text(customer_tweet)

        # Step 1: Historical Grounding Retrieval (also provides prior for intent)
        grounding = self.retriever.retrieve_grounding_context(cleaned_text, top_k=2)
        top_prior_intent = None
        if grounding["top_historical_pairs"]:
            top_prior_intent = grounding["top_historical_pairs"][0]["intent"]

        # Step 2: Intent Classification
        classification = self.classifier.classify(cleaned_text, retrieval_prior_intent=top_prior_intent)
        intent = classification["predicted_intent"]
        confidence = classification["confidence"]

        # Step 3: Escalation Decision & Stated Reasoning
        escalation = self.escalator.evaluate(cleaned_text, intent, confidence)
        should_escalate = escalation["should_escalate"]
        escalation_category = escalation["escalation_category"]
        escalation_reason = escalation["escalation_reason"]

        # Step 4: Grounded Response Drafting
        drafted_reply = self._draft_reply(
            cleaned_text=cleaned_text,
            intent=intent,
            should_escalate=should_escalate,
            escalation_category=escalation_category,
            grounding=grounding
        )

        return {
            "customer_query": customer_tweet,
            "cleaned_query": cleaned_text,
            "predicted_intent": intent,
            "intent_confidence": confidence,
            "key_signals": classification["key_signals"],
            "should_escalate": should_escalate,
            "escalation_category": escalation_category,
            "escalation_reason": escalation_reason,
            "risk_level": escalation["risk_level"],
            "drafted_reply": drafted_reply,
            "grounding_context": grounding
        }

    def _draft_reply(self, cleaned_text: str, intent: str, should_escalate: bool, escalation_category: str, grounding: dict) -> str:
        """
        Synthesizes a policy-compliant, grounded response in AppleSupport brand persona.
        """
        top_hist = grounding["top_historical_pairs"][0] if grounding["top_historical_pairs"] else None
        top_kb = grounding["top_kb_article"]

        # A. ESCALATED RESPONSES (Human intervention or secure channel needed)
        if should_escalate:
            if escalation_category == "ACCOUNT_SECURITY_PII":
                return "Your account security is our top priority. For your privacy and safety, never share credentials publicly. Please send us a DM so an Account Security advisor can assist you in private: https://iforgot.apple.com"
            
            elif escalation_category == "HARDWARE_DAMAGE_REPAIR":
                if "swollen" in cleaned_text.lower() or "bulging" in cleaned_text.lower():
                    return "For your safety, please power off the device immediately, disconnect any chargers, and do not use it. Please visit an Apple Store or authorized service provider right away for urgent inspection."
                elif "water" in cleaned_text.lower() or "liquid" in cleaned_text.lower() or "pool" in cleaned_text.lower():
                    return "To prevent further damage, keep the device powered off and do not plug in a charger while wet. We recommend having it inspected by a certified technician at an Apple Store: https://support.apple.com/repair"
                else:
                    return "We're sorry to hear about the damage. Physical hardware issues require in-person diagnostic evaluation. You can check repair pricing and reserve a Genius Bar appointment here: https://support.apple.com/repair"

            elif escalation_category == "BILLING_REFUND_DISPUTE":
                return "We understand your frustration regarding these charges and want to review this carefully. You can check your purchase history at https://reportaproblem.apple.com, or send us a DM with your Order ID so our billing team can assist you."

            elif escalation_category == "REPEATED_FAILED_TROUBLESHOOTING":
                return "We appreciate you taking the time to try those troubleshooting steps. Since the issue persists after a full restore, let's connect you with a senior technical advisor. Please DM us so we can review your diagnostics."

            elif escalation_category == "AMBIGUOUS_COMPLAINT":
                return "We take concerns of this nature extremely seriously. Please send us a DM with your contact details, store location, or case number so executive customer relations can investigate and follow up with you directly."

        # B. AUTO-HANDLED RESPONSES (Grounded in Historical Solutions & Knowledge Base)
        if top_hist and top_hist["score"] > 2.0:
            # High-relevance historical match
            reply = top_hist["reply"]
            # Ensure official URL is included if available
            if top_kb and top_kb["url"] not in reply:
                reply = f"{reply} {top_kb['url']}"
            return reply

        elif top_kb:
            # Grounded in official Knowledge Base article
            summary = top_kb["summary"]
            url = top_kb["url"]
            diag = top_kb.get("diagnostic_question", "")
            return f"We'd like to help with this! {summary} {diag} For more steps: {url}"

        else:
            # Fallback empathetic AppleSupport intake
            return "Thanks for reaching out! We'd love to help get this resolved. Which Apple device model and software version are you currently using? Let us know more details so we can assist."
