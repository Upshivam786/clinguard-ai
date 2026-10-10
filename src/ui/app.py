
import os

import requests
import streamlit as st


API_BASE_URL = os.getenv(
    "CLINGUARD_API_URL",
    "http://api:8000",
).rstrip("/")

st.set_page_config(
    page_title="ClinGuard AI",
    page_icon="🩺",
    layout="wide",
)

if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


def login(username: str, password: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": username,
                "password": password,
            },
            timeout=15,
        )
        if response.status_code == 200:
            return response.json(), None
        if response.status_code == 401:
            return None, "Invalid username or password."
        return None, f"Login failed (HTTP {response.status_code})."
    except requests.RequestException:
        return None, "Cannot reach the API. Please try again later."


def logout():
    st.session_state.access_token = None
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()


st.title("🩺 ClinGuard AI")
st.caption(
    "Privacy-first clinical information retrieval "
    "with patient-scoped search and grounded AI responses."
)

if not st.session_state.access_token:
    st.subheader("Clinician sign in")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
        )

    if submitted:
        if not username.strip() or not password:
            st.error("Enter both username and password.")
        else:
            result, error = login(username.strip(), password)
            if error:
                st.error(error)
            else:
                st.session_state.access_token = result["access_token"]
                st.session_state.username = username.strip()
                st.session_state.role = result["role"]
                st.rerun()

    st.info(
        "Sign in with your configured ClinGuard API account. "
        "Do not enter real patient identifiers or personal details "
        "in this portfolio demonstration."
    )
    st.stop()


with st.sidebar:
    st.subheader("Signed in")
    st.write(st.session_state.username)
    st.caption(f"Role: {st.session_state.role}")
    st.button("Sign out", on_click=logout, use_container_width=True)

st.subheader("Clinical question")

with st.form("clinical_query_form"):
    patient_id = st.number_input(
        "Patient ID",
        min_value=1,
        value=7,
        step=1,
    )

    admission_choice = st.selectbox(
        "Admission scope",
        options=["All admissions for this patient", "Specific admission"],
    )

    admission_id = None
    if admission_choice == "Specific admission":
        admission_id = st.number_input(
            "Admission ID",
            min_value=1,
            value=11,
            step=1,
        )

    question = st.text_area(
        "Question",
        placeholder="Example: What medications were documented?",
        max_chars=2000,
        height=110,
    )

    submitted = st.form_submit_button(
        "Run clinical query",
        type="primary",
    )

if submitted:
    if not question.strip():
        st.warning("Enter a clinical question.")
        st.stop()

    payload = {
        "question": question.strip(),
        "patient_id": int(patient_id),
        "admission_id": (
            int(admission_id)
            if admission_id is not None
            else None
        ),
        "top_k": 100,
        "max_context_events": 8,
    }

    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json",
    }

    with st.spinner("Retrieving relevant records and generating an answer..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/query",
                json=payload,
                headers=headers,
                timeout=180,
            )

            if response.status_code == 401:
                st.session_state.access_token = None
                st.session_state.username = None
                st.session_state.role = None
                st.warning("Your session expired. Please sign in again.")
                st.rerun()

            if response.status_code == 403:
                st.error("Your account is not authorized for this operation.")
                st.stop()

            if not response.ok:
                st.error(
                    f"Query failed (HTTP {response.status_code}). "
                    "The API could not process the request."
                )
                st.stop()

            result = response.json()

        except requests.Timeout:
            st.error("The query timed out. Please try again.")
            st.stop()
        except requests.RequestException:
            st.error("Cannot reach the API. Please try again later.")
            st.stop()

    st.subheader("Answer")

    st.markdown(result["answer"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Patient ID", result["patient_id"])
    col2.metric("Retrieved events", result["retrieved_count"])
    col3.metric("Context events", result["context_event_count"])

    st.caption(
        "AI-generated information is limited to retrieved records "
        "and is not a diagnosis or treatment recommendation. "
        "The retrieved results may not represent a complete patient history."
    )
