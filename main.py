import streamlit as st
from pathlib import Path
from PIL import Image
import base64
from datetime import date
from query_store import get_query_count, update_query_count, get_data,save_data
from log_store import log_entry
import os
import joblib
from helper import get_all_features, get_last_available_aqi_date
import pandas as pd

from dotenv import load_dotenv
load_dotenv()
import os


# -------------------------------
# App setup
# -------------------------------
st.set_page_config(
    page_title="AQI Prediction System",
    page_icon="assets/logo.png" 
)

MAX_QUERIES = 25  # shared daily limit

# -------------------------------
# Cached initialization
# -------------------------------
@st.cache_resource
def load_model():
    return joblib.load("artifacts/selected_features_gradboost.joblib")
def load_features():
    return joblib.load("artifacts/selected_features.joblib")

model = load_model()
indi=load_features()


# -------------------------------
# Load query count once per session
# -------------------------------
data = get_data()
today = str(date.today())

if "last_reset" not in st.session_state or st.session_state.get("last_reset") != today:
    st.session_state["query_count"] = get_query_count()
    st.session_state["last_reset"] = today

# -------------------------------
# prediction function
# -------------------------------
def predict(target_date, prev_aqi):
    count = st.session_state["query_count"]
    if count >= MAX_QUERIES:
        return None,None, "⚠️ Sorry, the total prediction limit for today has been reached. Please try again tomorrow."

    try:
        # Feature generation
        X = get_all_features(str(target_date), prev_aqi)
        X=X[indi]

        # Prediction
        y_pred = float(model.predict(X)[0])
        
        # Increment and persist count 
        new_count = count + 1
        update_query_count(new_count)
        st.session_state["query_count"] = new_count

        # Log success
        log_entry(
            query=f"target_date={target_date}, prev_aqi={prev_aqi}",
            response=f"predicted_aqi={y_pred}",
            route="prediction",
            score=None,
        )

        return y_pred,X, None
    
    except Exception as e:
        # Log failure as well
        log_entry(
            query=f"target_date={target_date}, prev_aqi={prev_aqi}",
            response=str(e),
            route="prediction_error",
            score=None,
        )
        return None,None, "Prediction failed. Please try again later."

# -------------------------------
# Header and Branding
# -------------------------------
st.markdown("<h2 style='text-align: center;'>NEXT DAY PM2.5 AQI (US EPA standard) Prediction system for BTM layout station Bengaluru</h2>", unsafe_allow_html=True)
st.markdown(
    """
    <p style='text-align: center; font-size: 14px; color: gray;'>
    💡 This model is a student project developed for learning purposes.
    </p>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <p style='text-align: center; font-size: 14px; color: gray;'>
    <b>(Predictions are limited. Expand the left panel from top arrows for details.)</b>
    </p>
    """,
    unsafe_allow_html=True,
)


# -------------------------------
# Sidebar info
# -------------------------------
count = st.session_state.get("query_count", 0)
st.sidebar.markdown("### USAGE INFO:")
st.sidebar.info(
    f"💬 **Predictions used today (shared across all users):** {count} / {MAX_QUERIES}\n\n"
    f"⏰ **Auto-reset daily at midnight**"
)
st.sidebar.progress(min(count / MAX_QUERIES, 1.0))

st.sidebar.markdown("---")
st.sidebar.markdown("### PROJECT INFO:")
st.sidebar.markdown(
    f"""
    <p><b>To predict tomorrow’s PM2.5 AQI:</b><br>
    Enter tomorrow’s date (target date) and today’s PM2.5 AQI value.</p>

    <p><b>Data Sources (Free APIs):</b><br>
    Weather: <a href="https://www.visualcrossing.com/" target="_blank">Visual Crossing Weather API</a><br>
    AQI: <a href="https://aqicn.org/historical/#!city:india/bangalore/btm" target="_blank">World Air Quality Index (WAQI)</a>
    </p>

    <p><b>Limits:</b><br>
    Using free APIs — daily limit = {MAX_QUERIES} predictions (shared across users)
    </p>
    """,
    unsafe_allow_html=True
)


st.sidebar.markdown("---")
st.sidebar.markdown("""
👨‍💻 **Contact:** Vinay S  
📧 [vins.techn@gmail.com](mailto:vins.techn@gmail.com)
""")

# -------------------------------
# predcition Interface
# -------------------------------
last_sheet_date = get_last_available_aqi_date()

# Allow prediction up to (last_date + 2)
max_target_date = last_sheet_date + pd.Timedelta(days=2)

with st.form("aqi_form"):
    target_date = st.date_input(
        "Tommorow's Date (Target date)",
        max_value=max_target_date
    )
    st.caption(
        f"ℹ️ You can predict AQI up to {max_target_date.strftime('%d %b %Y')} "
        f"based on the latest available AQI data."
    )
    prev_day = target_date - pd.Timedelta(days=1)
    prev_aqi = st.number_input(f"Today's AQI (AQI for {prev_day.strftime('%d %b %Y')})", min_value=0.0)
    submit = st.form_submit_button("Predict AQI")

if submit:
    with st.spinner("Predicting AQI..."):
        pred, features_df, err = predict(target_date, prev_aqi)
    if err:
        st.error(err)
    else:
        st.success(f"Predicted AQI: {pred:.1f}")

        # AQI reference table
        with st.expander("📊 AQI Levels & Health Implications (source : waqi)"):
            img = Image.open("assets/aqi_table.png")
            st.image(img, width="stretch")

    if features_df is not None:
        with st.expander("🔍 View features used for prediction"):
            st.dataframe(
                features_df.T,
                width="stretch"
            )



