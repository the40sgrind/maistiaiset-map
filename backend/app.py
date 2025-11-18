import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import uuid

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Maistiaiset Map", layout="wide")

# -------------------------------------------------
# FIREBASE INIT (USING STREAMLIT SECRETS)
# -------------------------------------------------
firebase_config = st.secrets["firebase"]

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": firebase_config["type"],
        "project_id": firebase_config["project_id"],
        "private_key_id": firebase_config["private_key_id"],
        "private_key": firebase_config["private_key"],
        "client_email": firebase_config["client_email"],
        "client_id": firebase_config["client_id"],
        "auth_uri": firebase_config["auth_uri"],
        "token_uri": firebase_config["token_uri"],
        "auth_provider_x509_cert_url": firebase_config["auth_provider_x509_cert_url"],
        "client_x509_cert_url": firebase_config["client_x509_cert_url"],
        "universe_domain": "googleapis.com"
    })
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------------------------------
# ADMIN PASSWORD (FROM STREAMLIT SECRETS)
# -------------------------------------------------
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def format_time(dt):
    if hasattr(dt, "strftime"):
        return dt.strftime("%d.%m.%Y klo %H:%M")
    return str(dt)


def render_event_card(event):
    """Render a dark-mode card using an HTML iframe."""
    product_name = event.get("product_name", "")
    brand_id = event.get("brand_id", "")
    store_name = event.get("store_name", "")
    address = event.get("address", "")
    description = event.get("description", "")
    start_time = format_time(event.get("start_time"))
    end_time = format_time(event.get("end_time"))
    approved = event.get("approved", False)

    status_label = "Hyväksytty" if approved else "Odottaa hyväksyntää"
    status_color = "#00c853" if approved else "#ffd600"

    html = f"""
    <html>
    <body style="margin:0; padding:0; background-color:#0e1117;">
        <div style="
            border-radius:12px;
            border:1px solid #333;
            padding:18px;
            margin-bottom:16px;
            background-color:#1e1e1e;
            color:#f2f2f2;
            font-family:sans-serif;
        ">

            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-weight:700; font-size:1.2rem; color:#ffffff;">
                    {product_name}
                    <span style="font-weight:400; color:#bbbbbb;">
                        {("– " + brand_id) if brand_id else ""}
                    </span>
                </div>

                <div style="
                    font-size:0.8rem;
                    padding:3px 10px;
                    border-radius:999px;
                    background-color:{status_color}33;
                    color:{status_color};
                    border:1px solid {status_color}55;
                    font-weight:600;
                ">
                    {status_label}
                </div>
            </div>

            <div style="margin-top:6px; color:#e0e0e0;">
                {store_name} • {address}
            </div>

            <div style="margin-top:6px; color:#cccccc; font-size:0.9rem;">
                {start_time} – {end_time}
            </div>

            <div style="margin-top:10px;">
                {description}
            </div>

        </div>
    </body>
    </html>
    """

    iframe_id = uuid.uuid4().hex
    iframe = f"""
        <iframe id="{iframe_id}" srcdoc='{html}'
            style="width:100%; height:260px; border:none; overflow:hidden;">
        </iframe>
    """

    st.components.v1.html(iframe, height=260)

# -------------------------------------------------
# FETCH ALL EVENTS FROM FIRESTORE
# -------------------------------------------------
events_ref = db.collection("events")
events_stream = events_ref.stream()

events_list = []
events_raw = []
for doc in events_stream:
    data = doc.to_dict()
    data["id"] = doc.id
    events_raw.append(data)

events_df = pd.DataFrame(events_raw)

# Public events (approved only)
if "approved" in events_df.columns:
    events_public = events_df[events_df["approved"] == True]
else:
    events_public = events_df

# Pending events
if "approved" in events_df.columns:
    events_pending = events_df[events_df["approved"] == False]
else:
    events_pending = pd.DataFrame()

# -------------------------------------------------
# UI LAYOUT
# -------------------------------------------------
st.title("Maistiaiset Map")
st.caption("Kaikki Suomen ilmaiset maistiaiset yhdessä sovelluksessa.")
st.markdown("---")

tab_map, tab_list, tab_form, tab_admin = st.tabs(
    ["🗺️ Kartta", "📋 Lista", "➕ Lisää tapahtuma", "🔑 Admin"]
)

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
        start_time_val = st.time_input("Start Time")
        end_date = st.date_input("End Date")
        end_time_val = st.time_input("End Time")

        submitted = st.form_submit_button("Create Event")

        if submitted:
            start_dt = datetime.combine(start_date, start_time_val)
            end_dt = datetime.combine(end_date, end_time_val)

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
                "approved": False  # NOW pending
            }

            db.collection("events").add(doc)
            st.success("Event submitted for approval!")


# -------------------------------------------------
# ADMIN TAB
# -------------------------------------------------
with tab_admin:
    st.subheader("Admin Dashboard")

    # Login form
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        entered_pw = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login"):
            if entered_pw == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Logged in!")
            else:
                st.error("Incorrect password.")
        st.stop()

    # Admin content
    st.success("Admin logged in.")

    st.markdown("### Pending Events")
    if events_pending.empty:
        st.info("No pending events.")
    else:
        for _, row in events_pending.iterrows():
            render_event_card(row)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✔ Approve", key=f"approve_{row['id']}"):
                    db.collection("events").document(row["id"]).update({"approved": True})
                    st.success("Event approved.")
                    st.rerun()

            with col2:
                if st.button("❌ Delete", key=f"delete_{row['id']}"):
                    db.collection("events").document(row["id"]).delete()
                    st.warning("Event deleted.")
                    st.rerun()
