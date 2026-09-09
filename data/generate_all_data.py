import json
import os

os.makedirs("/Users/varsha/Desktop/hiver-support-agent/data", exist_ok=True)

# 1. KNOWLEDGE BASE
knowledge_base = [
    {
        "article_id": "HT201412",
        "title": "Force restart iPhone or iPad",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["freeze", "frozen", "unresponsive", "black screen", "crash", "stuck", "loop"],
        "summary": "Press and quickly release Volume Up, press and quickly release Volume Down, then hold the Side button until the Apple logo appears. This fixes unresponsiveness without data loss.",
        "url": "https://support.apple.com/HT201412",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Which model iPhone are you using, and does the screen turn black or stay on an Apple logo?"
    },
    {
        "article_id": "HT201263",
        "title": "Resolve Wi-Fi network connectivity issues on iOS",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["wifi", "wi-fi", "internet", "connection", "disconnect", "dropping", "network"],
        "summary": "Toggle Airplane Mode on and off. Forget the Wi-Fi network and reconnect. Reset Network Settings under Settings > General > Transfer or Reset iPhone > Reset > Reset Network Settings.",
        "url": "https://support.apple.com/HT201263",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Are other devices able to connect to this Wi-Fi network, or is it isolated to your iPhone?"
    },
    {
        "article_id": "HT201557",
        "title": "Bluetooth accessory connection and pairing issues",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["bluetooth", "airpods", "headphones", "disconnecting", "unpair", "carplay", "pairing"],
        "summary": "Turn Bluetooth off in Settings and turn back on. Put your accessory into pairing mode. Select Forget This Device in Settings > Bluetooth and re-pair.",
        "url": "https://support.apple.com/HT201557",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Does the Bluetooth device connect to any other phone, and does your iPhone connect to other Bluetooth accessories?"
    },
    {
        "article_id": "HT201252",
        "title": "If an app unexpectedly quits, stops responding, or won't open",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["app crash", "quits", "closing", "force quit", "instagram", "camera app", "whatsapp"],
        "summary": "Force close the app by swiping up from bottom of screen. Restart device. Check App Store for app updates. Delete and reinstall the app if the issue persists.",
        "url": "https://support.apple.com/HT201252",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Is this happening with only one third-party app or multiple apps?"
    },
    {
        "article_id": "HT204204",
        "title": "Update iOS or iPadOS to the latest version",
        "intent": "SOFTWARE_OS_TROUBLESHOOTING",
        "keywords": ["update", "ios 17", "ios 16", "software update", "install update", "storage full update"],
        "summary": "Connect to Wi-Fi and power. Go to Settings > General > Software Update and tap Download and Install. Ensure at least 5GB of free storage is available.",
        "url": "https://support.apple.com/HT204204",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "What error message appears when you attempt to update in Settings > General > Software Update?"
    },
    {
        "article_id": "HT204051",
        "title": "iPhone battery health and unexpected shutdown management",
        "intent": "HARDWARE_BATTERY_REPAIR",
        "keywords": ["battery", "drain", "draining", "dying", "percentage", "health", "maximum capacity", "overheating"],
        "summary": "Review Settings > Battery > Battery Health & Charging. If Maximum Capacity is below 80% or says Service, battery replacement at an Apple Store or authorized provider is required.",
        "url": "https://support.apple.com/HT204051",
        "action_type": "HYBRID_ESCALATION",
        "diagnostic_question": "What percentage does your iPhone show under Settings > Battery > Battery Health?"
    },
    {
        "article_id": "HT201407",
        "title": "Physical screen repair, cracked glass, and display replacement",
        "intent": "HARDWARE_BATTERY_REPAIR",
        "keywords": ["cracked", "screen broken", "shattered", "lines on screen", "flickering", "dropped", "touch unresponsive"],
        "summary": "Cracked screens and internal display damage require hardware replacement. Schedule an appointment at an Apple Store Genius Bar or start an express mail-in repair.",
        "url": "https://support.apple.com/repair",
        "action_type": "ESCALATE_GENIUS_BAR",
        "diagnostic_question": "Is there visible glass cracking or distortion, and do you have AppleCare+ coverage on the device?"
    },
    {
        "article_id": "HT207043",
        "title": "If your iPhone or iPad won't charge or charges intermittently",
        "intent": "HARDWARE_BATTERY_REPAIR",
        "keywords": ["charging", "won't charge", "loose port", "lightning cable", "magsafe", "accessory not supported"],
        "summary": "Check the charging port for lint or debris. Test with a certified Apple cable and wall adapter. If the port is physically loose or damaged, hardware inspection is needed.",
        "url": "https://support.apple.com/HT207043",
        "action_type": "HYBRID_ESCALATION",
        "diagnostic_question": "Have you tested with an official Apple charging cable and a different wall outlet?"
    },
    {
        "article_id": "HT204306",
        "title": "Reset forgotten Apple ID password and recover account access",
        "intent": "ACCOUNT_APPLE_ID_SECURITY",
        "keywords": ["forgot password", "locked", "apple id", "disabled", "security questions", "recovery", "iforgot"],
        "summary": "Go to iforgot.apple.com to initiate a password reset. If two-factor authentication is active, use a trusted device. Never share recovery codes publicly.",
        "url": "https://iforgot.apple.com",
        "action_type": "ESCALATE_DM",
        "diagnostic_question": "Do you have access to your trusted phone number or an authorized trusted Apple device?"
    },
    {
        "article_id": "HT204915",
        "title": "Two-factor authentication for Apple ID and verification code issues",
        "intent": "ACCOUNT_APPLE_ID_SECURITY",
        "keywords": ["2fa", "two-factor", "verification code", "trusted number", "code not received", "sms code"],
        "summary": "If you don't receive verification codes, tap 'Didn't get a code' on sign-in screen to send SMS to trusted number. If inaccessible, account recovery is required.",
        "url": "https://support.apple.com/HT204915",
        "action_type": "ESCALATE_DM",
        "diagnostic_question": "Are you able to select 'Didn't get a code' to send the SMS to your registered trusted phone number?"
    },
    {
        "article_id": "HT201365",
        "title": "Activation Lock removal and device ownership verification",
        "intent": "ACCOUNT_APPLE_ID_SECURITY",
        "keywords": ["activation lock", "icloud locked", "previous owner", "stolen", "bypass", "erase device"],
        "summary": "Activation Lock cannot be bypassed without the original owner credentials. If you are the original purchaser, submit proof of purchase at al-support.apple.com.",
        "url": "https://al-support.apple.com",
        "action_type": "ESCALATE_HUMAN",
        "diagnostic_question": "Are you the original purchaser of the device with the receipt containing the serial number?"
    },
    {
        "article_id": "HT204084",
        "title": "Request a refund for App Store or iTunes Store purchases",
        "intent": "BILLING_SUBSCRIPTIONS_REFUNDS",
        "keywords": ["refund", "charged", "accidental purchase", "cancel subscription", "in-app", "money back", "unauthorized charge"],
        "summary": "Visit reportaproblem.apple.com, sign in with your Apple ID, select 'Request a refund', choose the reason, and select the item. Decisions typically take 24-48 hours.",
        "url": "https://reportaproblem.apple.com",
        "action_type": "HYBRID_ESCALATION",
        "diagnostic_question": "Does the charge appear in your purchase history when you sign in to reportaproblem.apple.com?"
    },
    {
        "article_id": "HT204145",
        "title": "View, manage, and cancel recurring Apple and third-party subscriptions",
        "intent": "BILLING_SUBSCRIPTIONS_REFUNDS",
        "keywords": ["cancel subscription", "stop renewal", "apple music subscription", "recurring charge", "unsubscribe"],
        "summary": "Go to Settings > [your name] > Subscriptions on iOS. Tap the subscription you wish to modify and select Cancel Subscription.",
        "url": "https://support.apple.com/HT204145",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Do you see the active subscription listed in Settings under your Apple ID name > Subscriptions?"
    },
    {
        "article_id": "HT201269",
        "title": "Use Quick Start to transfer data to a new iPhone or iPad",
        "intent": "DEVICE_SETUP_COMPATIBILITY",
        "keywords": ["setup", "new iphone", "transfer", "quick start", "migration", "restore backup", "switch phone"],
        "summary": "Turn on Bluetooth and Wi-Fi on both devices. Bring them close together and follow the Quick Start animation prompt. Keep devices plugged into power.",
        "url": "https://support.apple.com/HT201269",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Are both your current device and new device running the same or updated version of iOS?"
    },
    {
        "article_id": "HT204568",
        "title": "Unpair and erase your Apple Watch, or pair with a new iPhone",
        "intent": "DEVICE_SETUP_COMPATIBILITY",
        "keywords": ["apple watch", "unpair", "pair watch", "watch sync", "series 7", "series 8", "series 9"],
        "summary": "Open Watch app on iPhone, tap My Watch > All Watches, tap the 'i' icon next to your watch, and select Unpair Apple Watch. Then open Watch app on new phone to pair.",
        "url": "https://support.apple.com/HT204568",
        "action_type": "SELF_SERVICE",
        "diagnostic_question": "Is the Apple Watch currently unlocked and close to your iPhone?"
    }
]

with open("/Users/varsha/Desktop/hiver-support-agent/data/knowledge_base.json", "w") as f:
    json.dump(knowledge_base, f, indent=2)

print("Saved knowledge_base.json")
