"""
Prompt Engineering Platform — Capstone Project
Zero-cost stack: Streamlit + Google Gemini (free tier) + Hugging Face Inference API (free)
"""

import streamlit as st
import json
import os
import time
import datetime
import uuid

DATA_FILE = "data.json"

# ---------------------------------------------------------------------------
# Data persistence helpers
# ---------------------------------------------------------------------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"prompts": {}, "history": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ---------------------------------------------------------------------------
# Pricing table (public per-1K-token rates, used ONLY to estimate what this
# would have cost on a paid tier — actual calls in this app are free-tier)
# ---------------------------------------------------------------------------

PRICING = {
    "Gemini 2.5 Flash": {"input": 0.000075, "output": 0.0003},
    "Hugging Face (Mistral-7B)": {"input": 0.0, "output": 0.0},  # free inference API
}

# ---------------------------------------------------------------------------
# Model callers
# ---------------------------------------------------------------------------

def call_gemini(prompt, api_key):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    start = time.time()
    response = model.generate_content(prompt)
    elapsed = time.time() - start
    text = response.text
    return text, elapsed


def call_huggingface(prompt, api_key, model_id="Qwen/Qwen2.5-7B-Instruct"):
    from huggingface_hub import InferenceClient
    client = InferenceClient(token=api_key)
    start = time.time()
    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model=model_id,
        max_tokens=300,
    )
    result = response.choices[0].message.content
    elapsed = time.time() - start
    return result, elapsed


def estimate_tokens(text):
    # rough heuristic: ~4 chars per token
    return max(1, len(text) // 4)


def estimate_cost(model_name, input_text, output_text):
    rates = PRICING.get(model_name, {"input": 0, "output": 0})
    in_tok = estimate_tokens(input_text)
    out_tok = estimate_tokens(output_text)
    cost = (in_tok / 1000) * rates["input"] + (out_tok / 1000) * rates["output"]
    return cost, in_tok, out_tok


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Prompt Engineering Platform", layout="wide")

st.sidebar.title("⚙️ Prompt Engineering Platform")
page = st.sidebar.radio(
    "Navigate",
    ["📁 Prompt Manager", "🆚 A/B Testing", "📊 Analytics", "💰 Cost Tracker"],
)

st.sidebar.markdown("---")
st.sidebar.caption("API Keys (stored only in this session)")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")
hf_key = st.sidebar.text_input("Hugging Face API Key", type="password")
st.sidebar.caption("Both have free tiers — no billing required.")

# ---------------------------------------------------------------------------
# PAGE 1: Prompt Manager
# ---------------------------------------------------------------------------

if page == "📁 Prompt Manager":
    st.title("📁 Prompt Manager")
    st.write("Create, save, and version your prompts.")

    with st.expander("➕ New / Edit Prompt", expanded=True):
        name = st.text_input("Prompt name")
        category = st.selectbox("Category", ["General", "Coding", "Writing", "Analysis", "Other"])
        text = st.text_area("Prompt text", height=150)

        if st.button("Save Prompt"):
            if not name or not text:
                st.warning("Please provide both a name and prompt text.")
            else:
                if name not in data["prompts"]:
                    data["prompts"][name] = {"category": category, "versions": []}
                version_num = len(data["prompts"][name]["versions"]) + 1
                data["prompts"][name]["versions"].append({
                    "version": version_num,
                    "text": text,
                    "created": str(datetime.datetime.now()),
                })
                save_data(data)
                st.success(f"Saved '{name}' as version {version_num}")

    st.subheader("📚 Prompt Library")
    if not data["prompts"]:
        st.info("No prompts saved yet.")
    else:
        for pname, pdata in data["prompts"].items():
            with st.expander(f"{pname} ({pdata['category']}) — {len(pdata['versions'])} version(s)"):
                for v in reversed(pdata["versions"]):
                    st.markdown(f"**v{v['version']}** — {v['created']}")
                    st.code(v["text"])

# ---------------------------------------------------------------------------
# PAGE 2: A/B Testing
# ---------------------------------------------------------------------------

elif page == "🆚 A/B Testing":
    st.title("🆚 A/B Testing")
    st.write("Run the same prompt against two models and compare results.")

    prompt_names = list(data["prompts"].keys())
    if not prompt_names:
        st.warning("Create a prompt in Prompt Manager first.")
    else:
        chosen = st.selectbox("Choose a saved prompt", prompt_names)
        versions = data["prompts"][chosen]["versions"]
        version_labels = [f"v{v['version']}" for v in versions]
        chosen_version = st.selectbox("Version", version_labels, index=len(version_labels) - 1)
        prompt_text = versions[version_labels.index(chosen_version)]["text"]

        st.text_area("Prompt to test", value=prompt_text, height=100, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            model_a = st.selectbox("Model A", ["Gemini 2.5 Flash", "Hugging Face (Mistral-7B)"], key="a")
        with col2:
            model_b = st.selectbox("Model B", ["Hugging Face (Mistral-7B)", "Gemini 2.5 Flash"], key="b")

        if st.button("🚀 Run A/B Test"):
            results = {}
            for label, model in [("A", model_a), ("B", model_b)]:
                try:
                    if model == "Gemini 2.5 Flash":
                        if not gemini_key:
                            st.error("Enter a Gemini API key in the sidebar.")
                            st.stop()
                        output, elapsed = call_gemini(prompt_text, gemini_key)
                    else:
                        if not hf_key:
                            st.error("Enter a Hugging Face API key in the sidebar.")
                            st.stop()
                        output, elapsed = call_huggingface(prompt_text, hf_key)
                    cost, in_tok, out_tok = estimate_cost(model, prompt_text, output)
                    results[label] = {
                        "model": model, "output": output, "elapsed": elapsed,
                        "cost": cost, "in_tok": in_tok, "out_tok": out_tok,
                    }
                except Exception as e:
                    st.error(f"Model {label} ({model}) failed: {e}")
                    st.stop()

            col1, col2 = st.columns(2)
            for label, col in [("A", col1), ("B", col2)]:
                r = results[label]
                with col:
                    st.subheader(f"Model {label}: {r['model']}")
                    st.write(r["output"])
                    st.caption(
                        f"⏱ {r['elapsed']:.2f}s | 📝 {len(r['output'].split())} words | "
                        f"💵 est. ${r['cost']:.6f}"
                    )

            # log to history
            data["history"].append({
                "id": str(uuid.uuid4()),
                "timestamp": str(datetime.datetime.now()),
                "prompt": chosen,
                "model_a": results["A"]["model"],
                "model_b": results["B"]["model"],
                "time_a": results["A"]["elapsed"],
                "time_b": results["B"]["elapsed"],
                "cost_a": results["A"]["cost"],
                "cost_b": results["B"]["cost"],
            })
            save_data(data)
            st.success("Test logged to Analytics.")

# ---------------------------------------------------------------------------
# PAGE 3: Analytics
# ---------------------------------------------------------------------------

elif page == "📊 Analytics":
    st.title("📊 Analytics Dashboard")

    history = data["history"]
    if not history:
        st.info("No test history yet. Run an A/B test first.")
    else:
        st.metric("Total Tests Run", len(history))

        import pandas as pd
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        st.subheader("Response Time by Test")
        chart_df = df[["timestamp", "time_a", "time_b"]].set_index("timestamp")
        chart_df.columns = ["Model A time (s)", "Model B time (s)"]
        st.line_chart(chart_df)

        st.subheader("Cost per Test (estimated)")
        cost_df = df[["timestamp", "cost_a", "cost_b"]].set_index("timestamp")
        cost_df.columns = ["Model A cost ($)", "Model B cost ($)"]
        st.bar_chart(cost_df)

        st.subheader("Raw Test Log")
        st.dataframe(df[["timestamp", "prompt", "model_a", "model_b", "time_a", "time_b"]])

# ---------------------------------------------------------------------------
# PAGE 4: Cost Tracker
# ---------------------------------------------------------------------------

elif page == "💰 Cost Tracker":
    st.title("💰 Cost Tracker")

    history = data["history"]
    if not history:
        st.info("No usage yet.")
    else:
        total_cost = sum(h["cost_a"] + h["cost_b"] for h in history)
        total_calls = len(history) * 2
        st.metric("Total Estimated Cost (paid-tier equivalent)", f"${total_cost:.6f}")
        st.metric("Total API Calls Made", total_calls)
        st.metric("Actual Amount Spent", "$0.00 (free tier)")
        st.success(
            f"By using free tiers, this platform avoided an estimated ${total_cost:.6f} "
            "in API costs versus paid-tier pricing."
        )

        st.caption(
            "Cost estimates use public per-1K-token pricing for each model as a reference point. "
            "All calls made by this app run on free-tier quotas."
        )
