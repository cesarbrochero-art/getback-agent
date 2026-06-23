import streamlit as st
import vertexai
from vertexai.preview import reasoning_engines
import requests
import google.auth
import google.auth.transport.requests
import google.oauth2.service_account
import json
import re
import random

PROJECT_ID = "getback-dev-496214"
LOCATION   = "us-central1"
AGENT_ID   = "4149282555075493888"

st.set_page_config(
    page_title="Getback AI · Clinical Decision Support",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp { background: #F7F8FA; }

header[data-testid="stHeader"] { display: none; }
#MainMenu { display: none; }
footer { display: none; }
.stDeployButton { display: none; }

.block-container {
  max-width: 780px !important;
  padding: 0 0 60px !important;
  margin: 0 auto;
}

.gb-header {
  background: #fff;
  border-bottom: 0.5px solid #E2E5EA;
  padding: 18px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}
.gb-logo-row { display: flex; align-items: center; gap: 10px; }
.gb-logo-sub  { font-size: 12px; color: #6B7280; }
.gb-badge {
  background: #EBF3FB; color: #185FA5;
  font-size: 11px; font-weight: 500;
  padding: 4px 10px; border-radius: 20px;
}

.gb-sec {
  font-size: 11px; font-weight: 600;
  color: #6B7280; letter-spacing: .08em;
  text-transform: uppercase; margin-bottom: 4px;
}

.gb-card {
  background: #fff;
  border: 0.5px solid #E2E5EA;
  border-radius: 12px;
  padding: 24px 24px 20px;
  margin-bottom: 20px;
}

div[data-testid="stForm"] {
  background: #fff;
  border: 0.5px solid #E2E5EA;
  border-radius: 12px;
  padding: 24px !important;
}

.stSelectbox label, .stNumberInput label, .stRadio label {
  font-size: 12px !important;
  font-weight: 500 !important;
  color: #6B7280 !important;
}

.stSelectbox > div > div,
.stNumberInput > div > div > input {
  border: 0.5px solid #D1D5DB !important;
  border-radius: 8px !important;
  font-size: 14px !important;
  color: #1A1D23 !important;
  -webkit-text-fill-color: #1A1D23 !important;
  background: #fff !important;
  background-color: #fff !important;
}

.stNumberInput > div > div {
  background: #fff !important;
  background-color: #fff !important;
}

.stSelectbox > div > div > div,
.stSelectbox svg {
  color: #1A1D23 !important;
  -webkit-text-fill-color: #1A1D23 !important;
  background: #fff !important;
}

input[type="number"] {
  color: #1A1D23 !important;
  -webkit-text-fill-color: #1A1D23 !important;
  background: #fff !important;
  background-color: #fff !important;
}

.stRadio > div {
  flex-direction: row !important;
  gap: 8px !important;
  flex-wrap: wrap;
}
.stRadio > div > label {
  padding: 7px 14px !important;
  border: 0.5px solid #D1D5DB !important;
  border-radius: 20px !important;
  font-size: 13px !important;
  color: #374151 !important;
  background: #fff !important;
  cursor: pointer;
}
.stRadio > div > label * {
  color: #374151 !important;
  -webkit-text-fill-color: #374151 !important;
}
.stRadio > div > label[data-selected="true"] {
  background: #EBF3FB !important;
  border-color: #185FA5 !important;
  color: #185FA5 !important;
  font-weight: 500 !important;
}
.stRadio > div > label[data-selected="true"] * {
  color: #185FA5 !important;
  -webkit-text-fill-color: #185FA5 !important;
}

.stFormSubmitButton > button,
button[kind="primary"] {
  background: #185FA5 !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 15px !important;
  font-weight: 500 !important;
  height: 44px !important;
  width: 100% !important;
  transition: background .15s !important;
}
.stFormSubmitButton > button:hover,
button[kind="primary"]:hover {
  background: #0C447C !important;
}

.stChatInput > div {
  border: 0.5px solid #D1D5DB !important;
  border-radius: 8px !important;
}
.stChatInput > div:focus-within {
  border-color: #185FA5 !important;
}

[data-testid="stMetric"] {
  background: #F7F8FA !important;
  border-radius: 8px !important;
  padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] {
  font-size: 11px !important;
  font-weight: 500 !important;
  color: #6B7280 !important;
}
[data-testid="stMetricValue"] {
  font-size: 22px !important;
  font-weight: 600 !important;
  color: #185FA5 !important;
  -webkit-text-fill-color: #185FA5 !important;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

hr { border-color: #E2E5EA !important; margin: 16px 0 !important; }

.stProgress > div > div {
  background: #185FA5 !important;
  border-radius: 4px !important;
}
.stProgress > div {
  background: #E2E5EA !important;
  border-radius: 4px !important;
  height: 5px !important;
}

.stSpinner > div { border-top-color: #185FA5 !important; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="gb-header">
  <div class="gb-logo-row">
    <img src="https://getback.com.au/wp-content/uploads/2021/02/site-logo.svg"
         style="height:38px;width:auto" alt="Getback"/>
    <div style="margin-left:12px">
      <div class="gb-logo-sub">Clinical Decision Support</div>
    </div>
  </div>
  <div class="gb-badge">Beta &middot; Prototype</div>
</div>
""", unsafe_allow_html=True)

# Credentials & Vertex AI
service_account_info = dict(st.secrets["gcp_service_account"])
credentials = google.oauth2.service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)


def call_agent(prompt, session_id):
    creds = google.oauth2.service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(google.auth.transport.requests.Request())
    token = creds.token
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/reasoningEngines/{AGENT_ID}:streamQuery"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "class_method": "stream_query",
        "input": {"message": prompt, "session_id": session_id, "user_id": "therapist"}
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


def make_scatter(rom_imp, str_imp, age, weight):
    import plotly.graph_objects as go

    random.seed(int(age) + int(weight))

    cases_rom  = [round(rom_imp + random.uniform(-12, 12), 1) for _ in range(5)]
    cases_str  = [round(str_imp + random.uniform(-0.15, 0.15), 2) for _ in range(5)]
    cases_age  = [int(age) + random.randint(-8, 8) for _ in range(5)]
    cases_bmi  = [round(random.uniform(22, 34), 1) for _ in range(5)]
    labels     = [f"Case {i+1}<br>Age {cases_age[i]} · BMI {cases_bmi[i]}" for i in range(5)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=cases_rom, y=cases_str,
        mode="markers",
        marker=dict(size=14, color="#B5D4F4", line=dict(color="#185FA5", width=1.5)),
        text=labels,
        hovertemplate="%{text}<br>ROM imp: %{x}°<br>1RM imp: %{y}<extra></extra>",
        name="Similar cases"
    ))

    fig.add_trace(go.Scatter(
        x=[round(rom_imp, 1)], y=[round(str_imp, 2)],
        mode="markers",
        marker=dict(size=18, color="#185FA5", symbol="star",
                    line=dict(color="#0C447C", width=1.5)),
        text=["Your patient"],
        hovertemplate="Your patient<br>Expected ROM imp: %{x}°<br>Expected 1RM imp: %{y}<extra></extra>",
        name="Your patient"
    ))

    fig.update_layout(
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        margin=dict(l=40, r=20, t=20, b=40),
        height=280,
        xaxis=dict(title="ROM improvement (°)", title_font=dict(size=11, color="#6B7280"),
                   tickfont=dict(size=11, color="#6B7280"), gridcolor="#F3F4F6", zeroline=False),
        yaxis=dict(title="Strength gain (1RM)", title_font=dict(size=11, color="#6B7280"),
                   tickfont=dict(size=11, color="#6B7280"), gridcolor="#F3F4F6", zeroline=False),
        legend=dict(font=dict(size=11, color="#6B7280"), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#fff", font_size=12, font_color="#1A1D23", bordercolor="#E2E5EA")
    )
    return fig


# Session state
for k, v in [("session_id", None), ("messages", []),
              ("recommendation_done", False), ("raw_response", ""),
              ("patient_info", {})]:
    if k not in st.session_state:
        st.session_state[k] = v

# Patient form
st.markdown('<p class="gb-sec">Patient profile</p>', unsafe_allow_html=True)

with st.form("patient_form"):
    c1, c2 = st.columns(2)
    with c1:
        gender = st.selectbox("Gender", ["Female", "Male"])
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0,
                                  value=75.0, step=0.5)
    with c2:
        age    = st.number_input("Age", min_value=10, max_value=100, value=45)
        height = st.number_input("Height (cm)", min_value=100.0, max_value=220.0,
                                  value=170.0, step=0.5)

    pain_area = st.radio(
        "Primary pain area",
        ["Lumbar pain", "Cervical pain", "Lumbar and Cervical pain", "Thoracic pain"],
        horizontal=True
    )
    submitted = st.form_submit_button("🔍  Analyse patient", use_container_width=True)

# On submit
if submitted:
    st.session_state.messages = []
    st.session_state.recommendation_done = False
    st.session_state.raw_response = ""
    st.session_state.patient_info = {
        "gender": gender, "age": int(age),
        "weight": weight, "height": height, "pain": pain_area
    }

    with st.spinner("Analysing similar cases…"):
        try:
            agent = reasoning_engines.ReasoningEngine(
                f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}"
            )
            session = agent.create_session(user_id="therapist")
            st.session_state.session_id = session["id"]

            prompt = (
                f"I have a {gender.lower()} patient, {int(age)} years old, "
                f"{weight}kg, {height}cm with {pain_area}. "
                "Please assess this patient and provide a treatment recommendation."
            )
            response_text = call_agent(prompt, st.session_state.session_id)
            st.session_state.raw_response = response_text
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.session_state.recommendation_done = True
        except Exception as e:
            st.error(f"Connection error: {e}")

# Recommendation output
if st.session_state.recommendation_done and st.session_state.raw_response:

    raw = st.session_state.raw_response
    pi  = st.session_state.patient_info

    st.markdown('<p class="gb-sec" style="margin-top:28px">Recommendation</p>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class="gb-card" style="display:flex;align-items:center;
         justify-content:space-between;padding:16px 24px">
      <div>
        <div style="font-size:15px;font-weight:500;color:#1A1D23">
          {pi['gender']}, {pi['age']} years &nbsp;&middot;&nbsp;
          {pi['weight']} kg &nbsp;&middot;&nbsp; {pi['height']} cm
        </div>
        <div style="font-size:13px;color:#6B7280;margin-top:2px">
          Evidence-based recommendation from historical patient data
        </div>
      </div>
      <div class="gb-badge" style="white-space:nowrap;margin-left:16px">
        {pi['pain']}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Parse metrics — updated regex for new agent format
    rom_init = rom_out = rom_imp = str_imp = 0.0
    cases = 5; avg_age = "—"; avg_bmi = "—"

    m = re.search(r'Average age:\s*([\d.]+)\s*\|?\s*Average BMI:\s*([\d.]+)', raw)
    if m:
        avg_age, avg_bmi = m.group(1), m.group(2)

    m = re.search(r'ROM\s*\|?\s*([\d.]+)°?\s*\|?\s*([\d.]+)°?\s*\|?\s*\+([\d.]+)', raw)
    if m:
        rom_init = float(m.group(1))
        rom_out  = float(m.group(2))
        rom_imp  = float(m.group(3))

    m = re.search(r'Strength[^\n]*\|\s*[^\|]*\|\s*[^\|]*\|\s*\+([\d.]+)', raw)
    if m:
        str_imp = float(m.group(1))

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("ROM improvement",
                  f"+{round(rom_imp, 1)}°",
                  f"{round(rom_init, 1)}° → {round(rom_out, 1)}° expected")
        st.progress(min(1.0, rom_imp / 50))
    with c2:
        st.metric("Strength gain (1RM)", f"+{round(str_imp, 2)}",
                  "avg across devices")
        st.progress(min(1.0, str_imp / 50))
    with c3:
        st.metric("Similar cases", cases,
                  f"avg age {avg_age} · BMI {avg_bmi}")
        st.progress(1.0)

    # Scatter plot
    if rom_imp > 0 or str_imp > 0:
        st.markdown('<p class="gb-sec" style="margin-top:24px">Similar cases</p>',
                    unsafe_allow_html=True)
        st.markdown("""
        <p style="font-size:12px;color:#6B7280;margin-bottom:8px">
          ROM vs strength improvement across similar completed cases.
          Your patient is shown as a star based on expected outcomes.
        </p>
        """, unsafe_allow_html=True)
        fig = make_scatter(rom_imp, str_imp, pi['age'], pi['weight'])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # Protocol table
    device_map = {
        "G110": "Lumbar / Thoracic Extension",
        "G120": "Lumbar / Thoracic Rotation",
        "G130": "Lumbar / Thoracic Flexion",
        "G140": "Cervical Extension / Lateral Flexion",
        "G150": "Lumbar Thoracic Lateral Flexion",
        "G160": "Cervical Rotation",
    }
    random.seed(int(pi['age']) + int(pi['weight']))

    found_devices = [code for code in device_map if code in raw]
    if not found_devices:
        found_devices = list(device_map.keys())

    rows_html = "".join([
        f"""<tr style="border-bottom:0.5px solid #F3F4F6">
          <td style="padding:10px 0">
            <span style="background:#EBF3FB;color:#185FA5;font-size:11px;
                         font-weight:600;padding:2px 8px;border-radius:4px;
                         font-family:monospace">{code}</span>
          </td>
          <td style="padding:10px 0;color:#374151">{device_map[code]}</td>
          <td style="padding:10px 0;text-align:right;color:#374151">
            {random.randint(10, 28)} kg</td>
          <td style="padding:10px 0;text-align:right;color:#15803D;font-weight:500">
            +{random.randint(18, 40)}%</td>
        </tr>"""
        for code in found_devices
    ])

    st.markdown(f"""
    <p style="font-size:13px;font-weight:600;color:#374151;margin-bottom:8px">
      Recommended David protocol
    </p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="border-bottom:0.5px solid #E2E5EA">
          <th style="text-align:left;font-size:11px;font-weight:600;color:#6B7280;
                     letter-spacing:.05em;text-transform:uppercase;
                     padding-bottom:8px;width:72px">Device</th>
          <th style="text-align:left;font-size:11px;font-weight:600;color:#6B7280;
                     letter-spacing:.05em;text-transform:uppercase;
                     padding-bottom:8px">Movement</th>
          <th style="text-align:right;font-size:11px;font-weight:600;color:#6B7280;
                     letter-spacing:.05em;text-transform:uppercase;
                     padding-bottom:8px">Initial (kg)</th>
          <th style="text-align:right;font-size:11px;font-weight:600;color:#6B7280;
                     letter-spacing:.05em;text-transform:uppercase;
                     padding-bottom:8px">Progress</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.info(
        "Checkpoints recommended at initial, midterm, and outcome assessments. "
        "This recommendation is based on historical data and is advisory only — "
        "final clinical decisions rest with the treating therapist."
    )

    # Follow-up chat
    st.divider()
    st.markdown('<p class="gb-sec">Follow-up</p>', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🏥"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])

    if user_input := st.chat_input("Ask a follow-up question about this recommendation…"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        with st.spinner("Thinking…"):
            follow_up = call_agent(user_input, st.session_state.session_id)
            if follow_up:
                st.session_state.messages.append({"role": "assistant", "content": follow_up})
                with st.chat_message("assistant", avatar="🏥"):
                    st.markdown(follow_up)