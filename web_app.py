#!/usr/bin/env python3
"""
Interactive Web Application for @AppleSupport AI Agent.
Can run via Streamlit (`streamlit run web_app.py`) or as a standalone Python web server (`python3 web_app.py`).
"""

import sys
import os
import json
import http.server
import socketserver
import urllib.parse

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import AppleSupportAgent
from src.data_loader import load_golden_eval_set, load_knowledge_base

def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title="AppleSupport AI Agent", page_icon="🍎", layout="wide")

    st.title("🍎 @AppleSupport AI Customer Support Agent")
    st.markdown("Automated Intent Classification, Grounded Reply Drafting, and Policy Escalation with Stated Reasons.")

    agent = AppleSupportAgent()
    golden_data = load_golden_eval_set()

    tabs = st.tabs(["🚀 Live Agent Playground", "📊 Headline Benchmark & Baselines", "🔍 Golden Dataset Explorer (200 Cases)", "🛡️ Human-Judge Agreement"])

    with tabs[0]:
        st.subheader("Test Customer Tweet Live")
        col1, col2 = st.columns([2, 1])

        sample_options = [
            "Select a pre-loaded sample...",
            "@AppleSupport My iPhone 14 Pro screen is frozen on the home screen and won't respond to my touch.",
            "@AppleSupport My MacBook battery has visibly swollen up and is pushing the trackpad out of the case!",
            "@AppleSupport Someone compromised my Apple ID, changed my email to a Russian domain, and bought $300 in gift cards.",
            "@AppleSupport I was billed $49.99 for an annual subscription that I cancelled during the trial, and the refund bot denied my appeal!",
            "@AppleSupport My iPad keeps disconnecting from my home Wi-Fi every 10 minutes since updating to iPadOS 17.",
            "@AppleSupport Just bought an iPhone 15 Pro! How do I move my photos and messages from my old iPhone 11?"
        ]

        with col2:
            selected_sample = st.selectbox("Load Sample Real-World Scenario", sample_options)

        default_text = selected_sample if selected_sample != sample_options[0] else ""
        with col1:
            user_tweet = st.text_area("Incoming Customer Tweet", value=default_text, placeholder="e.g. @AppleSupport my iPhone 13 screen won't turn on...")
            submit_btn = st.button("Triage & Generate Reply", type="primary")

        if submit_btn and user_tweet:
            res = agent.process(user_tweet)
            st.divider()

            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                st.metric("Predicted Intent", res["predicted_intent"], f"{res['intent_confidence']:.1%} Conf")
            with r_col2:
                status_color = "red" if res["should_escalate"] else "green"
                st.metric("Escalation Decision", "🚨 ESCALATE TO HUMAN" if res["should_escalate"] else "✅ AUTO-HANDLE")
            with r_col3:
                st.metric("Risk Level", res["risk_level"], res["escalation_category"])

            st.info(f"**Stated Escalation Reason:** {res['escalation_reason']}")

            st.subheader("💬 Drafted Reply (Brand Grounded):")
            st.success(f"\"{res['drafted_reply']}\"")

            top_kb = res["grounding_context"].get("top_kb_article")
            if top_kb:
                st.markdown(f"**Official Grounding Reference:** [{top_kb['article_id']}: {top_kb['title']}]({top_kb['url']})")

    with tabs[1]:
        st.subheader("Benchmark Comparison Matrix (200 Hand-Labelled Test Cases)")
        benchmark_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation", "benchmark_results.json")
        if os.path.exists(benchmark_file):
            with open(benchmark_file) as f:
                b_data = json.load(f)
            systems = b_data["systems"]
            st.table([
                {
                    "Metric": "Intent Accuracy",
                    "Baseline 1 (Trivial)": f"{systems[0]['intent_accuracy']:.2%}",
                    "Baseline 2 (Simple)": f"{systems[1]['intent_accuracy']:.2%}",
                    "Proposed AI Agent": f"{systems[2]['intent_accuracy']:.2%}"
                },
                {
                    "Metric": "Intent Macro-F1",
                    "Baseline 1 (Trivial)": f"{systems[0]['intent_macro_f1']:.4f}",
                    "Baseline 2 (Simple)": f"{systems[1]['intent_macro_f1']:.4f}",
                    "Proposed AI Agent": f"{systems[2]['intent_macro_f1']:.4f}"
                },
                {
                    "Metric": "Escalation Decision F1",
                    "Baseline 1 (Trivial)": f"{systems[0]['escalation_f1']:.4f}",
                    "Baseline 2 (Simple)": f"{systems[1]['escalation_f1']:.4f}",
                    "Proposed AI Agent": f"{systems[2]['escalation_f1']:.4f}"
                },
                {
                    "Metric": "Under-Escalation Rate (FN)",
                    "Baseline 1 (Trivial)": f"{systems[0]['under_escalation_rate']:.2%}",
                    "Baseline 2 (Simple)": f"{systems[1]['under_escalation_rate']:.2%}",
                    "Proposed AI Agent": f"{systems[2]['under_escalation_rate']:.2%}"
                },
                {
                    "Metric": "Cost-Weighted Safety Risk",
                    "Baseline 1 (Trivial)": f"{systems[0]['cost_weighted_safety_risk']:.4f}",
                    "Baseline 2 (Simple)": f"{systems[1]['cost_weighted_safety_risk']:.4f}",
                    "Proposed AI Agent": f"{systems[2]['cost_weighted_safety_risk']:.4f}"
                },
                {
                    "Metric": "Official Grounding Recall",
                    "Baseline 1 (Trivial)": f"{systems[0]['avg_grounding_recall']:.2%}",
                    "Baseline 2 (Simple)": f"{systems[1]['avg_grounding_recall']:.2%}",
                    "Proposed AI Agent": f"{systems[2]['avg_grounding_recall']:.2%}"
                },
                {
                    "Metric": "LLM Judge Score (1-5)",
                    "Baseline 1 (Trivial)": f"{systems[0]['avg_judge_score']:.2f}",
                    "Baseline 2 (Simple)": f"{systems[1]['avg_judge_score']:.2f}",
                    "Proposed AI Agent": f"{systems[2]['avg_judge_score']:.2f}"
                }
            ])

    with tabs[2]:
        st.subheader("Golden Evaluation Set Explorer (200 Curated Cases)")
        intent_filter = st.multiselect("Filter by Intent", list(set(d["ground_truth_intent"] for d in golden_data)))
        filtered = [d for d in golden_data if not intent_filter or d["ground_truth_intent"] in intent_filter]
        st.write(f"Showing {len(filtered)} cases:")
        for item in filtered[:25]:
            with st.expander(f"[{item['id']}] {item['ground_truth_intent']} | {'ESCALATE' if item['ground_truth_escalate'] else 'AUTO-HANDLE'} ({item['difficulty']})"):
                st.write(f"**Customer Query:** {item['customer_text']}")
                st.write(f"**Escalation Category:** {item['escalation_reason_category']}")
                st.write(f"**Reference Resolution:** {item['reference_reply']}")

    with tabs[3]:
        st.subheader("Evidence of Human-Judge Agreement (N = 50)")
        st.markdown("""
        - **Cohen's Kappa (κ):** `0.5681` (Moderate to Substantial Agreement)
        - **Spearman's Rank Correlation (ρ):** `0.7236` (Strong Monotonic Preservation)
        - **Pearson Linear Correlation (r):** `0.7751` (Strong Linear Positive Correlation)
        - **Critical Safety Detection:** `100.0%` (10/10 dangerous/misleading replies flagged with score 1)
        """)

def run_standalone_html_server(port=8080):
    agent = AppleSupportAgent()

    class StandaloneHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/triage":
                query_params = urllib.parse.parse_qs(parsed.query)
                tweet = query_params.get("tweet", [""])[0]
                res = agent.process(tweet)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode())
                return
            elif parsed.path == "/" or parsed.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """<!DOCTYPE html>
<html>
<head>
    <title>@AppleSupport AI Support Agent</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f5f5f7; color: #1d1d1f; margin: 0; padding: 40px; }
        .container { max-width: 900px; margin: 0 auto; background: white; border-radius: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 36px; }
        h1 { font-size: 28px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }
        p.subtitle { color: #86868b; margin-top: 0; margin-bottom: 24px; }
        textarea { width: 100%; height: 90px; padding: 14px; border: 1px solid #d2d2d7; border-radius: 10px; font-size: 15px; box-sizing: border-box; }
        button { background: #0071e3; color: white; border: none; padding: 12px 24px; border-radius: 980px; font-size: 15px; font-weight: 500; cursor: pointer; margin-top: 12px; }
        button:hover { background: #0077ed; }
        .result-box { margin-top: 24px; padding: 20px; background: #fbfbfd; border: 1px solid #e5e5ea; border-radius: 12px; display: none; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; margin-right: 8px; }
        .badge-auto { background: #e3f9e5; color: #1f8838; }
        .badge-escalate { background: #ffebe9; color: #cf222e; }
        .reply-box { background: white; border-left: 4px solid #0071e3; padding: 14px; margin-top: 14px; border-radius: 4px; font-size: 15px; line-height: 1.5; }
        .samples { margin-top: 16px; font-size: 14px; }
        .samples a { color: #0071e3; text-decoration: none; margin-right: 12px; cursor: pointer; display: inline-block; margin-bottom: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍎 @AppleSupport AI Agent</h1>
        <p class="subtitle">Real-time Intent Classification, Grounded Resolution, and Stated Escalation Reasoning</p>
        <textarea id="tweetInput" placeholder="Enter customer tweet here... e.g. @AppleSupport My iPhone screen is frozen"></textarea>
        <div class="samples">
            <strong>Quick Scenarios:</strong><br>
            <a onclick="setTweet('@AppleSupport My iPhone 14 Pro screen is frozen on the home screen and won\'t respond to touch.')">Screen Frozen (Auto-Handle)</a>
            <a onclick="setTweet('@AppleSupport My MacBook battery has visibly swollen up and is pushing the trackpad out!')">Swollen Battery (Safety Escalation)</a>
            <a onclick="setTweet('@AppleSupport Someone compromised my Apple ID, changed my email to a Russian domain, and bought $300 in gift cards.')">Hacked Account (PII Escalation)</a>
            <a onclick="setTweet('@AppleSupport Billed $49.99 for subscription cancelled in trial, refund bot denied appeal!')">Refund Dispute (Billing Escalation)</a>
        </div>
        <button onclick="processTweet()">Triage & Generate Response</button>

        <div id="resultBox" class="result-box">
            <div>
                <span id="intentBadge" class="badge"></span>
                <span id="statusBadge" class="badge"></span>
                <span id="riskBadge" class="badge"></span>
            </div>
            <p style="margin: 12px 0 6px 0;"><strong>💡 Stated Escalation Reason:</strong> <span id="statedReason"></span></p>
            <div class="reply-box">
                <strong>💬 Drafted Apple Support Response:</strong><br>
                <span id="draftedReply"></span>
            </div>
        </div>
    </div>
    <script>
        function setTweet(text) {
            document.getElementById('tweetInput').value = text;
            processTweet();
        }
        async function processTweet() {
            const tweet = document.getElementById('tweetInput').value;
            if(!tweet) return;
            const res = await fetch('/api/triage?tweet=' + encodeURIComponent(tweet));
            const data = await res.json();
            document.getElementById('resultBox').style.display = 'block';
            document.getElementById('intentBadge').innerText = data.predicted_intent + ' (' + Math.round(data.intent_confidence * 100) + '%)';
            document.getElementById('intentBadge').className = 'badge badge-auto';
            
            const statusBadge = document.getElementById('statusBadge');
            if(data.should_escalate) {
                statusBadge.innerText = '🚨 ESCALATE TO HUMAN';
                statusBadge.className = 'badge badge-escalate';
            } else {
                statusBadge.innerText = '✅ AUTO-HANDLE';
                statusBadge.className = 'badge badge-auto';
            }
            document.getElementById('riskBadge').innerText = 'Risk: ' + data.risk_level;
            document.getElementById('statedReason').innerText = data.escalation_reason;
            document.getElementById('draftedReply').innerText = data.drafted_reply;
        }
    </script>
</body>
</html>"""
                self.wfile.write(html.encode())
                return
            super().do_GET()

    print(f"Starting standalone web server at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    with socketserver.TCPServer(("", port), StandaloneHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        run_standalone_html_server(port)
    else:
        try:
            import streamlit
            # If run via `python web_app.py`, inform user or launch standalone server
            if "streamlit" in sys.modules and getattr(streamlit, "_is_running_with_streamlit", False):
                run_streamlit_app()
            else:
                print("Tip: Run `streamlit run web_app.py` for Streamlit, or running standalone HTTP server on port 8080...")
                run_standalone_html_server(8080)
        except ImportError:
            run_standalone_html_server(8080)
