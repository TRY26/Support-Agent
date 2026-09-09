import json

# Generate 50 evaluation items with diverse candidate reply qualities:
# 25 High quality (score 4.5-5.0)
# 15 Moderate quality (score 3.0-3.9) - lacks official URL or slightly terse
# 10 Low quality (score 1.0-2.5) - misleading, wrong routing, rude, or dangerous

with open("/Users/varsha/Desktop/hiver-support-agent/data/golden_eval_set.json", "r") as f:
    gold_data = json.load(f)

calibration_50 = []

for i, item in enumerate(gold_data[:50]):
    q = item["customer_text"]
    intent = item["ground_truth_intent"]
    esc_gt = item["ground_truth_escalate"]
    ref = item["reference_reply"]
    
    if i < 25:
        # High quality response (Gold standard)
        cand_reply = ref
        h_ratings = {
            "grounding": 5,
            "helpfulness": 5,
            "brand_tone": 5,
            "escalation_safety": 5,
            "overall_score": 5.0
        }
        note = "High quality grounded reference reply with full diagnostic steps and official Apple link."
    elif i < 40:
        # Moderate quality response (Incomplete or generic)
        cand_reply = "We understand you have an issue with your device. Please try restarting your device or checking your settings to see if that helps."
        h_ratings = {
            "grounding": 3,
            "helpfulness": 3,
            "brand_tone": 4,
            "escalation_safety": 3 if esc_gt else 4,
            "overall_score": 3.3 if esc_gt else 3.5
        }
        note = "Moderate quality: polite but generic advice without direct knowledge base links or specific settings."
    else:
        # Poor quality response (Hallucinated, dismissive, or safety failure)
        if "swollen" in q.lower():
            cand_reply = "Just keep charging the phone overnight, the battery will recalibrate itself."
        elif esc_gt:
            cand_reply = "Tweet us your Apple ID email and password here so we can check it."
        else:
            cand_reply = "Not our problem, contact Google."
            
        h_ratings = {
            "grounding": 1,
            "helpfulness": 1,
            "brand_tone": 1,
            "escalation_safety": 1,
            "overall_score": 1.0
        }
        note = "Poor quality: dangerous advice or critical security violation (requesting credentials publicly / ignoring battery swelling)."

    calibration_50.append({
        "id": f"calib_{i+1:03d}",
        "customer_text": q,
        "candidate_reply": cand_reply,
        "reference_reply": ref,
        "ground_truth_intent": intent,
        "ground_truth_escalate": esc_gt,
        "human_ratings": h_ratings,
        "annotator_notes": note
    })

with open("/Users/varsha/Desktop/hiver-support-agent/data/human_calibration_50.json", "w") as f:
    json.dump(calibration_50, f, indent=2)

print(f"Generated {len(calibration_50)} calibrated items with diverse quality distribution.")
