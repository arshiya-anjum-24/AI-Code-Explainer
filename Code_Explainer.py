import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ======= 🌍 LOAD ENV VARIABLES =======
load_dotenv()

IBM_API_KEY = os.getenv("IBM_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL")

# ======= 🔑 FETCH IBM IAM TOKEN =======
@st.cache_resource
def get_cached_token():
    return get_iam_token(IBM_API_KEY)

def get_iam_token(api_key):
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"apikey={api_key}&grant_type=urn:ibm:params:oauth:grant-type:apikey"
    response = requests.post(url, headers=headers, data=data)

    if "access_token" not in response.json():
        st.error("❌ Failed to get IBM IAM token")
        st.code(response.text)
        raise RuntimeError("Token fetch failed")

    return response.json()["access_token"]

# ======= 🤖 ASK WATSONX FOR CODE EXPLANATION =======
def explain_code(code_snippet, language, token):
    url = f"{WATSONX_URL}/ml/v1/text/generation?version=2024-05-01"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are a helpful coding tutor. Explain the following {language} code in simple English for a beginner:

```{language}
{code_snippet}
Now provide a beginner-friendly explanation of what this code does, step by step.
"""
    payload = {
        "model_id": "ibm/granite-20b-code-instruct",
        "input": prompt.strip(),
        "project_id": PROJECT_ID,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 1300
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        return response.json()['results'][0]['generated_text']
    except Exception:
        raise RuntimeError(f"❌ WatsonX API failed:\nStatus Code: {response.status_code}\nResponse:\n{response.text}")
    # ======= 🚀 STREAMLIT WEB APP UI =======
st.set_page_config(page_title="AI Code Explainer", layout="wide")
st.title("💡 AI Code Explainer (Watsonx.ai)")
st.markdown("Paste your code and get a plain English explanation using IBM's Granite-20B Code model.")

language = st.selectbox("Select Programming Language", ["Python", "JavaScript", "Java", "C++"])
code_input = st.text_area("Paste your code here 👇", height=300)

if st.button("🧠 Explain Code"):
    if code_input.strip() == "":
        st.warning("⚠️ Please paste some code first.")
    else:
        with st.spinner("💭 Watsonx is thinking..."):
            try:
                token = get_cached_token()
                explanation = explain_code(code_input, language, token)
                st.success("📘 Explanation:")
                st.markdown(explanation)
            except Exception as e:
                st.error("❌ Something went wrong.")
                st.code(str(e))
