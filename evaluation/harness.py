"""
Unified Evaluation Harness for Hiver AI Support Agent.
Runs comparative evaluation on the 200 hand-labelled golden test set across:
1. Baseline 1 (Trivial Keyword/Canned Agent)
2. Baseline 2 (Simple Retrieval-Only Agent)
3. Proposed AI Support Agent (Intent-RAG + Stated-Reasoning Escalation)
"""

import os
import sys
import json
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_golden_eval_set
from src.config import INTENTS
from src.agent import AppleSupportAgent
from src.baselines import TrivialBaselineAgent, SimpleBaselineAgent
from evaluation.metrics import (
    compute_classification_metrics,
    compute_escalation_metrics,
    compute_rouge_l,
    compute_bleu_4,
    compute_grounding_recall
)
from evaluation.judge import SupportReplyJudge
from evaluation.agreement import evaluate_human_judge_agreement

def run_system_evaluation(system_name, agent, golden_dataset, judge):
    """Evaluates a single support agent system against the golden dataset."""
    print(f"Evaluating {system_name} on {len(golden_dataset)} test queries...")
    start_time = time.time()

    y_true_intent = []
    y_pred_intent = []
    y_true_escalate = []
    y_pred_escalate = []

    rouge_scores = []
    bleu_scores = []
    grounding_recalls = []
    judge_scores = []

    predictions = []

    for item in golden_dataset:
        q = item["customer_text"]
        true_intent = item["ground_truth_intent"]
        true_escalate = item["ground_truth_escalate"]
        ref_reply = item["reference_reply"]

        # Run system inference
        output = agent.process(q)

        pred_intent = output.get("predicted_intent", "SOFTWARE_OS_TROUBLESHOOTING")
        pred_escalate = output.get("should_escalate", False)
        pred_reason = output.get("escalation_reason", "")
        drafted_reply = output.get("drafted_reply", "")

        y_true_intent.append(true_intent)
        y_pred_intent.append(pred_intent)
        y_true_escalate.append(true_escalate)
        y_pred_escalate.append(pred_escalate)

        # Compute text metrics
        r_l = compute_rouge_l(drafted_reply, ref_reply)
        b_4 = compute_bleu_4(drafted_reply, ref_reply)
        g_rec = compute_grounding_recall(drafted_reply)

        rouge_scores.append(r_l)
        bleu_scores.append(b_4)
        grounding_recalls.append(g_rec)

        # Judge evaluation
        j_eval = judge.evaluate_reply(
            customer_query=q,
            generated_reply=drafted_reply,
            ground_truth_intent=true_intent,
            should_escalate_gt=true_escalate
        )
        judge_scores.append(j_eval["overall_score"])

        predictions.append({
            "id": item["id"],
            "query": q,
            "true_intent": true_intent,
            "pred_intent": pred_intent,
            "true_escalate": true_escalate,
            "pred_escalate": pred_escalate,
            "escalation_reason": pred_reason,
            "drafted_reply": drafted_reply,
            "reference_reply": ref_reply,
            "rouge_l": round(r_l, 3),
            "bleu_4": round(b_4, 3),
            "judge_score": j_eval["overall_score"],
            "judge_breakdown": j_eval
        })

    elapsed_time = round(time.time() - start_time, 2)

    # Compute aggregate metrics
    intent_metrics = compute_classification_metrics(y_true_intent, y_pred_intent, INTENTS)
    escalation_metrics = compute_escalation_metrics(y_true_escalate, y_pred_escalate)

    avg_rouge_l = round(sum(rouge_scores) / len(rouge_scores), 4)
    avg_bleu_4 = round(sum(bleu_scores) / len(bleu_scores), 4)
    avg_grounding = round(sum(grounding_recalls) / len(grounding_recalls), 4)
    avg_judge_score = round(sum(judge_scores) / len(judge_scores), 2)

    return {
        "system_name": system_name,
        "elapsed_seconds": elapsed_time,
        "intent_accuracy": intent_metrics.get("accuracy", 0.0),
        "intent_macro_f1": intent_metrics.get("macro_f1", 0.0),
        "escalation_accuracy": escalation_metrics.get("accuracy", 0.0),
        "escalation_precision": escalation_metrics.get("precision", 0.0),
        "escalation_recall": escalation_metrics.get("recall", 0.0),
        "escalation_f1": escalation_metrics.get("f1", 0.0),
        "under_escalation_rate": escalation_metrics.get("under_escalation_rate", 0.0),
        "cost_weighted_safety_risk": escalation_metrics.get("cost_weighted_safety_risk", 0.0),
        "avg_rouge_l": avg_rouge_l,
        "avg_bleu_4": avg_bleu_4,
        "avg_grounding_recall": avg_grounding,
        "avg_judge_score": avg_judge_score,
        "intent_breakdown": intent_metrics.get("per_class", {}),
        "escalation_breakdown": escalation_metrics,
        "predictions": predictions
    }

def run_full_benchmark():
    """Runs end-to-end benchmark across all three systems and prints comparison table."""
    golden_dataset = load_golden_eval_set()
    judge = SupportReplyJudge()

    # Instantiate the three systems
    trivial_agent = TrivialBaselineAgent()
    simple_agent = SimpleBaselineAgent(confidence_cutoff=1.5)
    proposed_agent = AppleSupportAgent()

    results_trivial = run_system_evaluation("Baseline 1 (Trivial Regex/Canned)", trivial_agent, golden_dataset, judge)
    results_simple = run_system_evaluation("Baseline 2 (Simple BM25 Copy)", simple_agent, golden_dataset, judge)
    results_proposed = run_system_evaluation("Proposed AI Support Agent", proposed_agent, golden_dataset, judge)

    agreement_results = evaluate_human_judge_agreement()

    benchmark_summary = {
        "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_size": len(golden_dataset),
        "systems": [results_trivial, results_simple, results_proposed],
        "human_judge_agreement": agreement_results
    }

    # Save results to JSON
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        # Strip individual predictions for clean summary
        summary_to_save = dict(benchmark_summary)
        summary_to_save["systems"] = [
            {k: v for k, v in sys_res.items() if k != "predictions"}
            for sys_res in benchmark_summary["systems"]
        ]
        json.dump(summary_to_save, f, indent=2)

    # Print Headline Comparison Table
    print("\n" + "=" * 95)
    print(" " * 25 + "HEADLINE EVALUATION RESULTS VS BASELINES")
    print("=" * 95)
    print(f"{'Metric':<32} | {'Baseline 1 (Trivial)':<20} | {'Baseline 2 (Simple)':<20} | {'Proposed Agent':<18}")
    print("-" * 95)
    print(f"{'Intent Accuracy':<32} | {results_trivial['intent_accuracy']:<20.2%} | {results_simple['intent_accuracy']:<20.2%} | {results_proposed['intent_accuracy']:<18.2%}")
    print(f"{'Intent Macro-F1':<32} | {results_trivial['intent_macro_f1']:<20.4f} | {results_simple['intent_macro_f1']:<20.4f} | {results_proposed['intent_macro_f1']:<18.4f}")
    print(f"{'Escalation Decision F1':<32} | {results_trivial['escalation_f1']:<20.4f} | {results_simple['escalation_f1']:<20.4f} | {results_proposed['escalation_f1']:<18.4f}")
    print(f"{'Under-Escalation Rate (FN)':<32} | {results_trivial['under_escalation_rate']:<20.2%} | {results_simple['under_escalation_rate']:<20.2%} | {results_proposed['under_escalation_rate']:<18.2%}")
    print(f"{'Cost-Weighted Safety Risk':<32} | {results_trivial['cost_weighted_safety_risk']:<20.4f} | {results_simple['cost_weighted_safety_risk']:<20.4f} | {results_proposed['cost_weighted_safety_risk']:<18.4f}")
    print(f"{'ROUGE-L Score':<32} | {results_trivial['avg_rouge_l']:<20.4f} | {results_simple['avg_rouge_l']:<20.4f} | {results_proposed['avg_rouge_l']:<18.4f}")
    print(f"{'BLEU-4 Score':<32} | {results_trivial['avg_bleu_4']:<20.4f} | {results_simple['avg_bleu_4']:<20.4f} | {results_proposed['avg_bleu_4']:<18.4f}")
    print(f"{'Official Grounding Recall':<32} | {results_trivial['avg_grounding_recall']:<20.2%} | {results_simple['avg_grounding_recall']:<20.2%} | {results_proposed['avg_grounding_recall']:<18.2%}")
    print(f"{'LLM Judge Rating (1-5)':<32} | {results_trivial['avg_judge_score']:<20.2f} | {results_simple['avg_judge_score']:<20.2f} | {results_proposed['avg_judge_score']:<18.2f}")
    print("=" * 95)
    print(f"\n[+] Human-Judge Agreement Evidence:")
    print(f"    - Calibration Samples: {agreement_results['sample_size']}")
    print(f"    - Cohen's Kappa (κ): {agreement_results['cohen_kappa']} ({agreement_results['interpretation']})")
    print(f"    - Spearman's Rank Correlation (ρ): {agreement_results['spearman_rho']}")
    print(f"    - Pearson Linear Correlation (r): {agreement_results['pearson_r']}")
    print(f"    - Overall Mean Absolute Error (MAE): {agreement_results['overall_mae']}")
    print(f"\n[+] Results saved to: {output_path}")

    return benchmark_summary

if __name__ == "__main__":
    run_full_benchmark()
