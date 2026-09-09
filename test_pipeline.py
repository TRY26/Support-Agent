#!/usr/bin/env python3
"""
Unit and Integration Test Suite for AppleSupport AI Agent Pipeline.
Usage:
    python3 test_pipeline.py
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import AppleSupportAgent
from src.retriever import HybridSupportRetriever
from src.intent_classifier import RuleAndCentroidIntentClassifier
from src.escalation_engine import EscalationDecisionEngine
from evaluation.metrics import (
    compute_classification_metrics,
    compute_escalation_metrics,
    compute_rouge_l,
    compute_bleu_4
)
from evaluation.agreement import compute_cohen_kappa, compute_spearman_rho

class TestSupportAgentPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AppleSupportAgent()
        cls.classifier = RuleAndCentroidIntentClassifier()
        cls.escalator = EscalationDecisionEngine()
        cls.retriever = HybridSupportRetriever()

    def test_intent_classification(self):
        res1 = self.classifier.classify("@AppleSupport My iPhone screen is completely frozen in Safari.")
        self.assertEqual(res1["predicted_intent"], "SOFTWARE_OS_TROUBLESHOOTING")

        res2 = self.classifier.classify("@AppleSupport Someone changed my Apple ID password and enabled two-factor.")
        self.assertEqual(res2["predicted_intent"], "ACCOUNT_APPLE_ID_SECURITY")

        res3 = self.classifier.classify("@AppleSupport I need a refund for an accidental in-app purchase of $29.")
        self.assertEqual(res3["predicted_intent"], "BILLING_SUBSCRIPTIONS_REFUNDS")

        res4 = self.classifier.classify("@AppleSupport How do I use Quick Start to move data to my new iPhone 15?")
        self.assertEqual(res4["predicted_intent"], "DEVICE_SETUP_COMPATIBILITY")

    def test_escalation_safety_policy(self):
        # Swollen battery must escalate as CRITICAL
        res_battery = self.escalator.evaluate("MacBook battery has swollen and bulging trackpad", "HARDWARE_BATTERY_REPAIR", 0.95)
        self.assertTrue(res_battery["should_escalate"])
        self.assertEqual(res_battery["escalation_category"], "HARDWARE_DAMAGE_REPAIR")
        self.assertEqual(res_battery["risk_level"], "CRITICAL")

        # Account takeover must escalate
        res_hacked = self.escalator.evaluate("Someone hacked my account and bought gift cards", "ACCOUNT_APPLE_ID_SECURITY", 0.95)
        self.assertTrue(res_hacked["should_escalate"])
        self.assertEqual(res_hacked["escalation_category"], "ACCOUNT_SECURITY_PII")

        # Disputed refund appeal must escalate
        res_refund = self.escalator.evaluate("Refund bot denied my appeal for double charge", "BILLING_SUBSCRIPTIONS_REFUNDS", 0.95)
        self.assertTrue(res_refund["should_escalate"])
        self.assertEqual(res_refund["escalation_category"], "BILLING_REFUND_DISPUTE")

        # Standard Wi-Fi FAQ must auto-handle
        res_wifi = self.escalator.evaluate("How do I reset network settings for Wi-Fi?", "SOFTWARE_OS_TROUBLESHOOTING", 0.95)
        self.assertFalse(res_wifi["should_escalate"])
        self.assertEqual(res_wifi["escalation_category"], "NONE_SAFE_TO_AUTOHANDLE")

    def test_bm25_retriever(self):
        grounding = self.retriever.retrieve_grounding_context("iPhone screen unresponsive force restart", top_k=1)
        self.assertGreater(len(grounding["top_historical_pairs"]), 0)
        self.assertIsNotNone(grounding["top_kb_article"])
        self.assertEqual(grounding["top_kb_article"]["article_id"], "HT201412")

    def test_metrics_calculation(self):
        y_true = ["A", "B", "A", "B"]
        y_pred = ["A", "B", "B", "B"]
        metrics = compute_classification_metrics(y_true, y_pred, ["A", "B"])
        self.assertEqual(metrics["accuracy"], 0.75)

        y_true_bool = [True, True, False, False]
        y_pred_bool = [True, False, False, False]
        esc_metrics = compute_escalation_metrics(y_true_bool, y_pred_bool)
        self.assertEqual(esc_metrics["accuracy"], 0.75)
        self.assertEqual(esc_metrics["recall"], 0.5)

    def test_agreement_metrics(self):
        h = ["HIGH", "HIGH", "MODERATE", "LOW"]
        j = ["HIGH", "HIGH", "MODERATE", "LOW"]
        kappa = compute_cohen_kappa(h, j, ["HIGH", "MODERATE", "LOW"])
        self.assertEqual(kappa, 1.0)

        rho = compute_spearman_rho([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        self.assertEqual(rho, 1.0)

    def test_end_to_end_agent(self):
        output = self.agent.process("@AppleSupport My iPhone 13 screen randomly froze and won't turn off.")
        self.assertIn("drafted_reply", output)
        self.assertIn("should_escalate", output)
        self.assertIn("escalation_reason", output)
        self.assertFalse(output["should_escalate"])
        self.assertIn("HT201412", output["drafted_reply"])

if __name__ == "__main__":
    unittest.main()
