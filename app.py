import streamlit as st
import vertexai
from vertexai.preview import reasoning_engines
import requests
import google.auth
import google.auth.transport.requests
import google.oauth2.service_account
import json
import plotly.graph_objects as go
import re

# ---- CONFIGURACIÓN ----
PROJECT_ID = "getback-dev-496214"
LOCATION = "us-central1"
AGENT_ID = "8851328638096769024"

# ---- CREDENCIALES GCP ----
service_account_info = dict(st.secrets["gcp_service_account"])
credentials = google.oauth2.service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# ---- INICIALIZAR VERTEX AI ----
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# ---- FUNCIÓN PARA EXTRAER DATOS DEL GRÁFICO ----
def extract_chart_data(text):
    pattern = r'CHART_DATA_START\s*(.*?)\s*CHART_DATA_END'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            chart_data = json.loads(match.group(1))
            clean_text = text[:text.find('CHART_DATA_START')].strip()
            return clean_text, chart_data
        except:
            return text, None
    return text, None

# ---- FUNCIÓN PARA RENDERIZAR GRÁFICO ----
def render_chart(chart_data):
    chart_type = chart_data.get("chart_type", "bar")
    title = chart_data.get("title", "Chart")
    x_label = chart_data.get("x_label", "")
    y_label = chart_data.get("y_label", "")
    data = chart_data.get("data", [])

    if not data:
        return

    labels = [d.get("label", "") for d in data]

    fig = go.Figure()

    if chart_type == "bar":
        if "initial" in data[0] and "outcome" in data[0]:
            initial_vals = [d.get("initial", 0) for d in data]
            outcome_vals = [d.get("outcome", 0) for d in data]
            fig.add_trace(go.Bar(name="Initial", x=labels, y=initial_vals, marker_color="#2E75B6"))
            fig.add_trace(go.Bar(name="Outcome", x=labels, y=outcome_vals, marker_color="#1E7E34"))
        else:
            values = [d.get("value", 0) for d in data]
            fig.add_trace(go.Bar(x=labels, y=values, marker_color="#2E75B6"))

    elif chart_type == "line":
        if "initial" in data[0] and "outcome" in data[0]:
            initial_vals = [d.get("initial", 0) for d in data]
            outcome_vals = [d.get("outcome", 0) for d in data]
            fig.add_trace(go.Scatter(name="Initial", x=labels, y=initial_vals, mode="lines+markers", line=dict(color="#2E75B6")))
            fig.add_trace(go.Scatter(name="Outcome", x=labels, y=outcome_vals, mode="lines+markers", line=dict(color="#1E7E34")))
        else:
            values = [d.get("value", 0) for d in data]
            fig.add_trace(go.Scatter(x=labels, y=values, mode="lines+markers", line=dict(color="#2E75B6")))

    elif chart_type == "scatter":
        x_vals = [d.get("x", 0) for d in data]
        y_vals = [d.get("y", 0) for d in data]
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="markers", marker=dict(color="#2E75B6", size=10)))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

# ---- FUNCIÓN PARA LLAMAR AL AGENTE ----
def call_agent(prompt, session_id):
    credentials_refreshed = google.oauth2.service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials_refreshed.refresh(google.auth.transport.requests.Request())
    token = credentials_refreshed.token

    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}:streamQuery"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "class_method": "stream_query",
        "input": {
            "message": prompt,
            "session_id": session_id,
            "user_id": "therapist"
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    full_text = ""
    for line in response.text.strip().split("\n"):
        try:
            chunk = json.loads(line)
            parts = chunk.get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part and "## Patient Profile Assessment" in part["text"]:
                    full_text = part["text"]
        except:
            continue

    if not full_text:
        for line in response.text.strip().split("\n"):
            try:
                chunk = json.loads(line)
                parts = chunk.get("content", {}).get("parts", [])
                for part in parts:
                    if "text" in part:
                        full_text = part["text"]
            except:
                continue

    return full_text

# ---- UI ----
st.set_page_config(
    page_title="Kynsei — Rehabilitation AI Assistant",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Kynsei — Rehabilitation AI Assistant")
st.caption("Evidence-based treatment recommendations for physiotherapists")

# ---- INICIALIZAR SESSION STATE ----
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recommendation_done" not in st.session_state:
    st.session_state.recommendation_done = False

# ---- FORMULARIO DEL PACIENTE ----
with st.form("patient_form"):
    st.subheader("Patient Profile")
    
    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("Gender", ["Female", "Male"])
        age = st.number_input("Age", min_value=10, max_value=100, value=45)
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=75.0)
    with col2:
        height = st.number_input("Height (cm)", min_value=100.0, max_value=220.0, value=170.0)
        pain_area = st.selectbox("Primary Pain Area", [
            "Lumbar pain",
            "Cervical pain",
            "Lumbar and Cervical pain",
            "Thoracic pain"
        ])
    
    submitted = st.form_submit_button("Get Treatment Recommendation", type="primary")

# ---- RECOMENDACIÓN INICIAL ----
if submitted:
    with st.spinner("Analyzing similar cases..."):
        try:
            agent = reasoning_engines.ReasoningEngine(
                f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}"
            )
            session = agent.create_session(user_id="therapist")
            st.session_state.session_id = session["id"]
            st.session_state.messages = []
            st.session_state.recommendation_done = False

            prompt = f"""I have a {gender.lower()} patient, {age} years old, {weight}kg, {height}cm with {pain_area}. 
            Please assess this patient and provide a treatment recommendation."""

            response_text = call_agent(prompt, st.session_state.session_id)

            if response_text:
                clean_text, chart_data = extract_chart_data(response_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": clean_text,
                    "chart_data": chart_data
                })
                st.session_state.recommendation_done = True
            else:
                st.warning("No response received from agent.")

        except Exception as e:
            st.error(f"Error connecting to agent: {e}")

# ---- MOSTRAR RECOMENDACIÓN Y CHAT ----
if st.session_state.recommendation_done:
    st.markdown("---")
    st.subheader("Treatment Recommendation")
    
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🏥"):
                st.markdown(message["content"])
                if message.get("chart_data"):
                    render_chart(message["chart_data"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])

    st.markdown("---")
    st.caption("💬 Ask a follow-up question or request a visualization")
    
    if user_input := st.chat_input("Ask a question or type 'show me a chart of...'"):
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "chart_data": None
        })
        
        with st.spinner("Thinking..."):
            follow_up_response = call_agent(user_input, st.session_state.session_id)
            
            if follow_up_response:
                clean_text, chart_data = extract_chart_data(follow_up_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": clean_text,
                    "chart_data": chart_data
                })
        
        st.rerun()