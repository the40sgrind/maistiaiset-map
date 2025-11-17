import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Maistiaiset Map", layout="wide")

# -------------------------------------------------
# FIREBASE INIT
# -------------------------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def format_time(dt):
    """Format datetime into Finnish style or return raw string."""
    if hasattr(dt, "strftime"):
        return dt.strftime("%d.%m.%Y klo %H:%M")
    return str(dt)

def render_event_card(event_row):
    product_name = event_row.get("product_name", "")
    brand_id = event_row.get("brand_id", "")
    store_name = event_row.get("store_name", "")
    address = event_row.get("address", "")
    description = event_row.get("description", "")
    start_time = format_time(event_row.get("start_time"))
    end_time = format_time(event_row.get("end_time"))
    approved = event_row.get("approved", False)

    status_label = "Hyväksytty" if approved else "Odottaa hyväksyntää"
    status_color = "#00c853" if approved else "#ffd600"

    st.html(
        f"""
        <div style="
            border-radius: 12px;
            border: 1px solid #333;
            padding: 18px;
            margin-bottom: 16px;
            background-color: #1e1e1e; /* DARK MODE background */
            color: #f2f2f2;            /* FORCE text light */
            font-family: sans-serif;
        ">

            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            ">
                <div style="
                    font-weight: 700;
                    font-size: 1.2rem;
                    color: #ffffff; /* FORCE visible title */
                ">
                    {product_name}
                    <span style="font-weight:400; color:#bbbbbb;">
                        {("– " + brand_id) if brand_id else ""}
                    </span>
                </div>

                <div style="
                    font-size: 0.8rem;
                    padding: 3px 10px;
                    border-radius: 999px;
                    background-color: {status_color}33;
                    color: {status_color};
                    border: 1px solid {status_color}55;
                    font-weight: 600;
                ">
                    {status_label}
                </div>
            </div>

            <div style="font-size: 1rem; margin-top: 6px; color:#e0e0e0;">
                {store_name} • {address}
            </div>

            <div style="font-size: 0.9rem; margin-top: 6px; color:#cccccc;">
                {start_time} – {end_time}
            </div>

            <div style="font-size: 1rem; margin-top: 10px; color:#f2f2f2;">
                {description}
            </div>

        </div>
        """
    )


# -------------------------------------------------
# FETCH EVENTS FROM FIRESTORE
# -------------------------------------------------
events_ref = db.collection("events")
events = events_ref.stream()

event_list = []
for event in events:
    event_list.append(event.to_dict())

events_df = pd.DataFrame(event_list)

if "approved" in events_df.columns:
    events_public = events_df[events_df["approved"] == True]
else:
    events_public = events_df

# -------------------------------------------------
# UI LAYOUT
# -------------------------------------------------
st.title("Maistiaiset Map")
st.caption("Kaikki Suomen ilmaiset maistiaiset yhdessä sovelluksessa.")
st.markdown("---")

tab_map, tab_list, tab_form = st.tabs(["🗺️ Kartta", "📋 Lista", "➕ Lisää tapahtuma"])

# -------------------------------------------------
# MAP TAB
# -------------------------------------------------
with tab_map:
    st.subheader("Maistiaiset kartalla")

    if events_public.empty:
        st.info("Ei tapahtumia kartalla.")
    else:
        map_df = events_public.rename(columns={"latitude": "lat", "longitude": "lon"})
        st.map(map_df[["lat", "lon"]])

# -------------------------------------------------
# LIST TAB
# -------------------------------------------------
with tab_list:
    st.subheader("Tulevat maistiaiset")

    if events_public.empty:
        st.info("Ei tapahtumia listattavaksi.")
    else:
        for _, row in events_public.iterrows():
            render_event_card(row)

# -------------------------------------------------
# FORM TAB
# -------------------------------------------------
with tab_form:
    st.subheader("Lisää uusi tapahtuma")

    with st.form("event_form"):
        product_name = st.text_input("Product Name")
        brand_id = st.text_input("Brand ID")
        store_name = st.text_input("Store Name")
        address = st.text_input("Address")
        latitude = st.number_input("Latitude", format="%.6f")
        longitude = st.number_input("Longitude", format="%.6f")
        description = st.text_area("Description")

        start_date = st.date_input("Start Date")
        start_time_input = st.time_input("Start Time")

        end_date = st.date_input("End Date")
        end_time_input = st.time_input("End Time")

        submitted = st.form_submit_button("Create Event")

        if submitted:
            start_dt = datetime.combine(start_date, start_time_input)
            end_dt = datetime.combine(end_date, end_time_input)

            doc = {
                "product_name": product_name,
                "brand_id": brand_id,
                "store_name": store_name,
                "address": address,
                "latitude": float(latitude),
                "longitude": float(longitude),
                "description": description,
                "start_time": start_dt,
                "end_time": end_dt,
                "approved": True
            }

            db.collection("events").add(doc)
            st.success("Event added successfully!")
