#!/usr/bin/env python3
"""
Interactive Demonstration CLI for AppleSupport AI Agent.
Allows testing sample customer queries or entering custom tweets.
Usage:
    python3 demo_agent.py
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import AppleSupportAgent

SAMPLE_TWEETS = [
    {
        "title": "Software Freeze (Safe to Auto-Handle)",
        "tweet": "@AppleSupport My iPhone 14 Pro screen is frozen on the home screen and won't respond to my touch."
    },
    {
        "title": "Battery Safety Hazard (Urgent Safety Escalation)",
        "tweet": "@AppleSupport My MacBook battery has visibly swollen up and is pushing the trackpad out of the case!"
    },
    {
        "title": "Account Security / Phishing (Critical Escalation)",
        "tweet": "@AppleSupport Someone compromised my Apple ID, changed my email to a Russian domain, and bought $300 in gift cards."
    },
    {
        "title": "Billing Dispute (Disputed Refund Escalation)",
        "tweet": "@AppleSupport I was billed $49.99 for an annual subscription that I cancelled during the trial, and the refund bot denied my appeal!"
    },
    {
        "title": "Wi-Fi Connectivity (Self-Service Auto-Handle)",
        "tweet": "@AppleSupport My iPad keeps disconnecting from my home Wi-Fi every 10 minutes since updating to iPadOS 17."
    },
    {
        "title": "Device Migration (Setup FAQ Auto-Handle)",
        "tweet": "@AppleSupport Just bought an iPhone 15 Pro! How do I move my photos and messages from my old iPhone 11?"
    }
]

def format_output(result: dict):
    print("\n" + "-" * 75)
    print(f"📥 CUSTOMER QUERY: {result['customer_query']}")
    print("-" * 75)
    print(f"🏷️  PREDICTED INTENT : {result['predicted_intent']} (Confidence: {result['intent_confidence']:.1%})")
    print(f"🚦 ESCALATION STATUS: {'🚨 ESCALATE TO HUMAN' if result['should_escalate'] else '✅ AUTO-HANDLE'}")
    print(f"📌 CATEGORY         : {result['escalation_category']}")
    print(f"💡 STATED REASON    : {result['escalation_reason']}")
    print(f"🛡️  RISK LEVEL       : {result['risk_level']}")
    
    top_kb = result['grounding_context'].get('top_kb_article')
    if top_kb:
        print(f"📚 GROUNDED KB REF  : {top_kb['article_id']} ({top_kb['title']})")
    
    print("\n💬 DRAFTED REPLY:")
    print(f"   \"{result['drafted_reply']}\"")
    print("-" * 75)

def main():
    agent = AppleSupportAgent()
    print("=" * 75)
    print(" 🍎 @AppleSupport AI Agent - Interactive Demonstration CLI")
    print("=" * 75)
    print("Running automated demonstration across 6 representative real-world scenarios...\n")

    for i, item in enumerate(SAMPLE_TWEETS, 1):
        print(f"\n[Scenario {i}/6]: {item['title']}")
        res = agent.process(item["tweet"])
        format_output(res)

    print("\n" + "=" * 75)
    print(" Interactive Mode: Type an incoming tweet to test the agent live (or 'q' to exit).")
    print("=" * 75)

    while True:
        try:
            user_input = input("\nEnter customer tweet > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['q', 'exit', 'quit']:
                print("Exiting demo. Thank you!")
                break

            res = agent.process(user_input)
            format_output(res)
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break

if __name__ == "__main__":
    main()
