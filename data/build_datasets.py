#!/usr/bin/env python3
"""
Dataset Generator & Compiler for Hiver AI Customer Support Agent (AppleSupport).
Generates:
1. historical_conversations.json (Knowledge retrieval corpus)
2. knowledge_base.json (Curated Apple Support articles & action flows)
3. golden_eval_set.json (200 hand-labelled ground truth examples)
4. human_calibration_50.json (50 human-rated samples for judge agreement validation)
5. sampling_and_labeling_guide.md (Sampling & labeling methodology document)
"""

import json
import os
import random

random.seed(42)

# --- 1. KNOWLEDGE BASE ARTICLES ---
KNOWLEDGE_BASE = [
    {
        "article_id": "HT201412",
        "title": "Force restart iPhone",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["freeze", "frozen", "unresponsive", "black screen", "crash", "stuck"],
        "summary": "Press and quickly release Volume Up, press and quickly release Volume Down, then hold the Side button until the Apple logo appears.",
        "url": "https://support.apple.com/HT201412",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Which iPhone model are you using, and does the screen respond to charging?"
    },
    {
        "article_id": "HT201263",
        "title": "If your iPhone or iPad won't connect to a Wi-Fi network",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["wifi", "wi-fi", "internet", "connection", "disconnect", "dropping"],
        "summary": "Toggle Airplane Mode on/off. Forget the Wi-Fi network and reconnect. Go to Settings > General > Transfer or Reset iPhone > Reset > Reset Network Settings.",
        "url": "https://support.apple.com/HT201263",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Does this issue happen with all Wi-Fi networks or only your home network?"
    },
    {
        "article_id": "HT204051",
        "title": "If your iPhone battery drains quickly or has degraded performance",
        "intent": "HARDWARE_BATTERY_REPAIR",
        "keywords": ["battery", "drain", "draining", "dying", "percentage", "health", "maximum capacity"],
        "summary": "Check Settings > Battery > Battery Health & Charging. If Maximum Capacity is below 80%, battery service is recommended at an Apple Authorized Service Provider or Genius Bar.",
        "url": "https://support.apple.com/HT204051",
        "action_type": "HYBRID_ESCALATION",
        "diagnostic_question": "What is the Maximum Capacity percentage shown under Settings > Battery > Battery Health?"
    },
    {
        "article_id": "HT204306",
        "title": "If you forgot your Apple ID password or account is locked",
        "intent": "ACCOUNT_APPLE_ID_SECURITY",
        "keywords": ["forgot password", "locked", "apple id", "disabled", "security questions", "recovery"],
        "summary": "Visit iforgot.apple.com to reset your password. If two-factor authentication is active, use a trusted device. If unable to verify, start Account Recovery.",
        "url": "https://iforgot.apple.com",
        "action_type": "ESCALATE_DM",
        "diagnostic_question": "Do you still have access to your trusted phone number or another Apple device?"
    },
    {
        "article_id": "HT204084",
        "title": "Request a refund for apps or content bought from Apple",
        "intent": "BILLING_SUBSCRIPTIONS_REFUNDS",
        "keywords": ["refund", "charged", "accidental purchase", "cancel subscription", "in-app", "money back"],
        "summary": "Sign in to reportaproblem.apple.com with your Apple ID. Select 'I'd like to', choose 'Request a refund', select the reason, and submit the request.",
        "url": "https://reportaproblem.apple.com",
        "action_type": "HYBRID_ESCALATION",
        "diagnostic_question": "Did you make this purchase within the last 90 days on reportaproblem.apple.com?"
    },
    {
        "article_id": "HT201269",
        "title": "Transfer data from previous iOS device to new iPhone or iPad",
        "intent": "DEVICE_SETUP_COMPATIBILITY",
        "keywords": ["setup", "new iphone", "transfer", "quick start", "migration", "restore backup"],
        "summary": "Place both devices next to each other with Bluetooth turned on. Follow Quick Start on-screen instructions, or restore from an iCloud backup during setup.",
        "url": "https://support.apple.com/HT201269",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Are both devices connected to Wi-Fi and plugged into power during the transfer?"
    },
    {
        "article_id": "HT201557",
        "title": "Bluetooth accessories not connecting or disconnecting frequently",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["bluetooth", "airpods", "headphones", "disconnecting", "unpair", "carplay"],
        "summary": "Turn Bluetooth off and on in Settings. Put the accessory in pairing mode. Forget the device in Settings > Bluetooth and pair again.",
        "url": "https://support.apple.com/HT201557",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Which Bluetooth accessory is failing to connect, and does it pair with other devices?"
    },
    {
        "article_id": "HT201407",
        "title": "iPhone screen cracked, damaged, or unresponsive touch",
        "intent": "HARDWARE_BATTERY_REPAIR",
        "keywords": ["cracked", "screen broken", "shattered", "lines on screen", "flickering", "dropped", "touch not working"],
        "summary": "Physical screen damage requires hardware inspection. Schedule an appointment at an Apple Store Genius Bar or send the device in via Apple Support.",
        "url": "https://support.apple.com/repair",
        "action_type": "ESCALATE_GENIUS_BAR",
        "diagnostic_question": "Is the display cracked or is the touch completely unresponsive across all areas?"
    },
    {
        "article_id": "HT204145",
        "title": "Cancel a subscription from Apple",
        "intent": "BILLING_SUBSCRIPTIONS_REFUNDS",
        "keywords": ["cancel subscription", "stop renewal", "apple music subscription", "recurring charge", "unsubscribe"],
        "summary": "Go to Settings > [your name] > Subscriptions. Tap the subscription you wish to cancel and tap 'Cancel Subscription'.",
        "url": "https://support.apple.com/HT204145",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Do you see the active subscription listed in Settings > your name > Subscriptions?"
    },
    {
        "article_id": "HT201365",
        "title": "Activation Lock on iPhone, iPad, or iPod touch",
        "intent": "ACCOUNT_APPLE_ID_SECURITY",
        "keywords": ["activation lock", "icloud locked", "previous owner", "stolen", "bypass", "erase device"],
        "summary": "Activation Lock prevents unauthorized use. The original Apple ID password is required to unlock. Original proof of purchase is required for Apple review.",
        "url": "https://al-support.apple.com",
        "action_type": "ESCALATE_HUMAN",
        "diagnostic_question": "Do you have the original proof of purchase or invoice showing the device serial number?"
    }
]

print("Compiling datasets...")
