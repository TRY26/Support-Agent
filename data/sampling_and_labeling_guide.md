# Golden Evaluation Set: Sampling & Labeling Methodology

## 1. Overview & Objective
This document outlines the sampling methodology, taxonomy definitions, and annotation guidelines used to construct the **Golden Evaluation Set of 200 hand-labelled examples** for the **AppleSupport** AI agent.

The objective of this evaluation set is to provide a rigorous, leak-free benchmark that assesses:
1. **Intent Classification Accuracy**: Can the agent correctly classify incoming customer tweets into 6 defined domain intents?
2. **Escalation Precision & Safety**: Does the agent correctly recognize when an issue can be safely auto-handled vs. when it must be escalated to a human/private channel (DM/Genius Bar)?
3. **Response Quality & Brand Grounding**: Does the drafted reply provide accurate, grounded technical steps adhering to Apple Support's signature tone and policy constraints?

---

## 2. Sampling Strategy & Stratification

To ensure the evaluation set is representative of real-world Twitter customer support traffic while testing critical edge cases, a **stratified sampling protocol** was employed:

### A. Intent Distribution (200 Total Cases)
| Intent Class | Count | Percentage | Primary Symptoms / Scenarios |
| :--- | :--- | :--- | :--- |
| `SOFTWARE_OS_TROUBLESHOOTING` | 46 | 23.0% | Freezing, app crashes, Wi-Fi/Bluetooth disconnects, iOS update bugs, Safari lag |
| `HARDWARE_BATTERY_REPAIR` | 38 | 19.0% | Cracked screens, battery degradation, swollen batteries, liquid damage, loose ports |
| `ACCOUNT_APPLE_ID_SECURITY` | 36 | 18.0% | Locked Apple IDs, forgot password, 2FA code delivery, Activation Lock, phishing scams |
| `BILLING_SUBSCRIPTIONS_REFUNDS` | 36 | 18.0% | Accidental in-app purchases, unauthorized renewals, billing disputes, refund requests |
| `DEVICE_SETUP_COMPATIBILITY` | 30 | 15.0% | Quick Start transfers, iCloud restore, accessory compatibility, Apple Watch pairing |
| `OUT_OF_SCOPE_FEEDBACK_RANT` | 14 | 7.0% | General brand feedback, rants without technical symptoms, jokes, praise |

### B. Escalation Balance
- **Auto-Handle (`AUTO_HANDLE = False`)**: **106 cases (53.0%)**
  - Problems resolvable through diagnostic questions, standard self-serve troubleshooting (restart, reset network settings, update iOS), or linking to official Apple Support guides (`support.apple.com`).
- **Escalate to Human (`ESCALATE_HUMAN = True`)**: **94 cases (47.0%)**
  - Scenarios requiring human intervention, private credential exchange (DM), financial authorization, or physical in-store hardware inspection (Genius Bar).

### C. Difficulty Breakdown
- **Easy (40%)**: Explicit symptom, clear device mentioned, single intent, no emotional hostility.
- **Medium (38%)**: Implicit symptom, missing OS version or device, ambiguous network failure, mild user frustration.
- **Hard / Edge Cases (22%)**: Multi-turn repeated troubleshooting failure ("I restarted 5 times already"), physical danger (swollen battery), account security breach / fraud, sarcasm, threat of churn or legal action.

---

## 3. Labeling Taxonomy & Annotation Guidelines

### Intent Classification Rubric
Each customer tweet is assigned exactly one primary intent based on the following precedence rules:
1. If the message mentions **credentials, password reset, 2FA, or Activation Lock**, classify as `ACCOUNT_APPLE_ID_SECURITY`.
2. If the message mentions **charges, credit cards, subscriptions, or refunds**, classify as `BILLING_SUBSCRIPTIONS_REFUNDS`.
3. If the message describes **physical physical damage, cracked glass, battery swelling, water contact, or port failure**, classify as `HARDWARE_BATTERY_REPAIR`.
4. If the message relates to **moving data between devices, pairing new accessories, or device specs**, classify as `DEVICE_SETUP_COMPATIBILITY`.
5. If the message describes **software glitches, freezes, connectivity issues, app crashes, or updates**, classify as `SOFTWARE_OS_TROUBLESHOOTING`.
6. If the message contains **no actionable technical or account query** (praise, insults, general design feedback), classify as `OUT_OF_SCOPE_FEEDBACK_RANT`.

### Escalation Decision Rubric
An example is labelled `should_escalate = True` if and only if any of the following triggers are met:
1. **`ACCOUNT_SECURITY_PII`**: The customer requires verification of private data, unlocking an Apple ID, or reporting a hacked account. (PII cannot be processed by an automated public tweet).
2. **`BILLING_REFUND_DISPUTE`**: The customer is disputing an automated refund denial, experiencing repeated fraudulent charges, or demanding financial compensation.
3. **`HARDWARE_DAMAGE_REPAIR`**: Physical damage, broken screen, battery bulge, or liquid damage requiring Genius Bar hardware inspection.
4. **`REPEATED_FAILED_TROUBLESHOOTING`**: The customer has already executed standard troubleshooting (force restart, DFU restore) and the issue persists with severe disruption.
5. **`AMBIGUOUS_COMPLAINT`**: Customer threatens legal action, reports severe store staff misconduct, or presents severe brand reputation risks.

---

## 4. Quality Control & Calibration
- **Annotation Independence**: The 200 samples were reviewed to eliminate ambiguous label collisions.
- **50-Item Calibration Set**: A subset of 50 examples was annotated with multi-dimensional human scores (1-5 across Grounding, Helpfulness, Tone, and Escalation Safety) to provide ground truth for evaluating the LLM-as-a-Judge and computing Inter-Annotator Agreement (Cohen's Kappa & Spearman Correlation).
