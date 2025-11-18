import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime, time

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Maistiaiset Map", layout="wide")

# -------------------------------------------------
# FIREBASE INIT (FROM STREAMLIT SECRETS)
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
# LANGUAGE TEXTS
# -------------------------------------------------
TEXTS = {
    "fi": {
        "app_title": "Maistiaiset Map",
        "subtitle": "Kaikki Suomen ilmaiset maistiaiset yhdessä sovelluksessa.",
        "map_tab": "🗺️ Kartta",
        "list_tab": "📋 Lista",
        "add_tab": "➕ Lisää tapahtuma",
        "admin_tab": "🔑 Admin",
        "product_name": "Tuotteen nimi",
        "brand_id": "Brändi",
        "store_name": "Kauppa",
        "address": "Osoite",
        "latitude": "Leveysaste (latitude)",
        "longitude": "Pituusaste (longitude)",
        "description": "Kuvaus",
        "start_date": "Aloituspäivä",
        "end_date": "Päättymispäivä",
        "start_time": "Aloitusaika",
        "end_time": "Päättymisaika",
        "create_event": "Luo tapahtuma",
        "event_added": "Tapahtuma lisätty ja odottaa hyväksyntää!",
        "pending_events": "Hyväksyntää odottavat tapahtumat",
        "approve": "Hyväksy",
        "approved": "Hyväksytty!",
        "form_title": "Lisää uusi tapahtuma",
        "manual_time_clear": "🧹 Tyhjennä ja syötä ajat käsin"
    },
    "en": {
        "app_title": "Tasting Map",
        "subtitle": "All free tasting events in Finland — in one place.",
        "map_tab": "🗺️ Map",
        "list_tab": "📋 List",
        "add_tab": "➕ Add Event",
        "admin_tab": "🔑 Admin",
        "product_name": "Product Name",
        "brand_id": "Brand",
        "store_name": "Store",
        "address": "Address",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "description": "Description",
        "start_date": "Start Date",
        "end_date": "End Date",
        "start_time": "Start Time",
        "end_time": "End Time",
        "create_event": "Create Event",
        "event_added": "Event submitted for approval!",
        "pending_events": "Pending Approval",
        "approve": "Approve",
        "approved": "Approved!",
        "form_title": "Add New Event",
        "manual_time_clear": "🧹 Clear & Type Times Manually"
    },
    "sv": {
        "app_title": "Provsmakningskarta",
        "subtitle": "Alla gratis provsmakningar i Finland — på ett ställe.",
        "map_tab": "🗺️ Karta",
        "list_tab": "📋 Lista",
        "add_tab": "➕ Lägg till evenemang",
        "admin_tab": "🔑 Admin",
        "product_name": "Produktnamn",
        "brand_id": "Märke",
        "store_name": "Butik",
        "address": "Adress",
        "latitude": "Latitud",
        "longitude": "Longitud",
        "description": "Beskrivning",
        "start_date": "Startdatum",
        "end_date": "Slutdatum",
        "start_time": "Starttid",
        "end_time": "Sluttid",
        "create_event": "Skapa evenemang",
        "event_added": "Evenemang skickat för godkännande!",
        "pending_events": "Väntar på godkännande",
        "approve": "Godkänn",
        "approved": "Godkänd!",
        "form_title": "Lägg till nytt evenemang",
        "manual_time_clear": "🧹 Rensa & skriv tider manuellt"
    }
}

# -------------------------------------------------
# SESSION DEFAULTS
# -------------------------------------------------
if "language" not in st.session_state:
    st.session_state["language"] = "fi"

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "map"

# -------------------------------------------------
# LANGUAGE LOADER
# -------------------------------------------------
T = TEXTS[st.session_state["language"]]

# -------------------------------------------------
# FLAG BUTTONS
# -------------------------------------------------
fi, en, sv = st.columns([1, 1, 1])

with fi:
    if st.button("🇫🇮 Suomi"):
        st.session_state["language"] = "fi"
        st.session_state["active_tab"] = st.session_state["active_tab"]
        st.rerun()

with en:
    if st.button("🇬🇧 English"):
        st.session_state["language"] = "en"
        st.session_state["active_tab"] = st.session_state["active_tab"]
        st.rerun()

with sv:
    if st.button("🇸🇪 Svenska"):
        st.session_state["language"] = "sv"
        st.session_state["active_tab"] = st.session_state["active_tab"]
        st.rerun()

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title(T["app_title"])
st.caption(T["subtitle"])
st.markdown("---")

# -------------------------------------------------
# TABS (S1 MOBILE STYLE)
# -------------------------------------------------
TAB_KEYS = ["map", "list", "add_event", "admin"]

def get_tab_label(key):
    return {
        "map": T["map_tab"],
        "list": T["list_tab"],
        "add_event": T["add_tab"],
        "admin": T["admin_tab"]
    }[key]

active_tab = st.radio(
    "Navigation",
    TAB_KEYS,
    index=TAB_KEYS.index(st.session_state["active_tab"]),
    format_func=get_tab_label,
    horizontal=True,
    key="main_tabs",
    label_visibility="collapsed"
)

st.session_state["active_tab"] = active_tab

# -------------------------------------------------
# EVENT CARD
# -------------------------------------------------
def render_event_card(event):
    html = f"""
    <div style="border-radius: 12px; border: 1px solid #333; padding: 18px;
                margin-bottom: 16px; background-color: #1e1e1e; color: #f2f2f2;
                font-family: sans-serif;">
        <div style="display: flex; justify-content: space-between;
                    align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 700; font-size: 1.2rem; color: #ffffff;">
                {event.get('product_name', '')}
                <span style="font-weight:400; color:#bbbbbb;">
                    {("– " + event.get('brand_id', '')) if event.get('brand_id') else ''}
                </span>
            </div>
            <div style="font-size: 0.8rem; padding: 3px 10px; border-radius: 999px;
                        background-color: #00c85333; color: #00c853;
                        border: 1px solid #00c85355; font-weight: 600;">
                {T["approved"]}
            </div>
        </div>

        <div style="font-size: 1rem; margin-top: 6px; color:#e0e0e0;">
            {event.get('store_name', '')} • {event.get('address', '')}
        </div>

        <div style="font-size: 0.9rem; margin-top: 6px; color:#cccccc;">
            {event.get('start_time', '')} – {event.get('end_time', '')}
        </div>

        <div style="font-size: 1rem; margin-top: 10px; color:#f2f2f2;">
            {event.get('description', '')}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------------------------
# FETCH EVENTS
# -------------------------------------------------
events_public = []
pending_events = []

for e in db.collection("events").stream():
    data = e.to_dict()
    data["id"] = e.id
    if data.get("approved"):
        events_public.append(data)
    else:
        pending_events.append(data)

# -------------------------------------------------
# TAB: MAP
# -------------------------------------------------
if active_tab == "map":
    st.subheader(T["map_tab"])

    if not events_public:
        st.info("Ei tapahtumia kartalla.")
    else:
        df = pd.DataFrame(events_public)
        df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
        st.map(df[["lat", "lon"]])

# -------------------------------------------------
# TAB: LIST
# -------------------------------------------------
elif active_tab == "list":
    st.subheader(T["list_tab"])

    if not events_public:
        st.info("Ei tapahtumia listattavaksi.")
    else:
        for e in events_public:
            render_event_card(e)

# -------------------------------------------------
# TAB: ADD EVENT
# -------------------------------------------------
elif active_tab == "add_event":
    st.subheader(T["form_title"])

    if "manual_mode" not in st.session_state:
        st.session_state.manual_mode = False

    with st.form("event_form"):
        product_name = st.text_input(T["product_name"])
        brand_id = st.text_input(T["brand_id"])
        store_name = st.text_input(T["store_name"])
        address = st.text_input(T["address"])
        latitude = st.number_input(T["latitude"], format="%.6f")
        longitude = st.number_input(T["longitude"], format="%.6f")
        description = st.text_area(T["description"])

        start_date = st.date_input(T["start_date"])
        end_date = st.date_input(T["end_date"])

        if st.form_submit_button(T["manual_time_clear"]):
            st.session_state.manual_mode = True
            st.session_state.start_manual = ""
            st.session_state.end_manual = ""
            st.rerun()

        if st.session_state.manual_mode:
            st.session_state.start_manual = st.text_input(
                T["start_time"],
                value=st.session_state.get("start_manual", ""),
                key="start_manual_input",
            )
            st.session_state.end_manual = st.text_input(
                T["end_time"],
                value=st.session_state.get("end_manual", ""),
                key="end_manual_input",
            )

            try:
                start_time_value = datetime.strptime(st.session_state.start_manual, "%H:%M").time()
                end_time_value = datetime.strptime(st.session_state.end_manual, "%H:%M").time()
            except ValueError:
                start_time_value = time(9, 0)
                end_time_value = time(10, 0)

        else:
            start_time_value = st.time_input(T["start_time"], value=time(9,0), step=900)
            end_time_value = st.time_input(T["end_time"], value=time(10,0), step=900)

        if st.form_submit_button(T["create_event"]):
            doc = {
                "product_name": product_name,
                "brand_id": brand_id,
                "store_name": store_name,
                "address": address,
                "latitude": float(latitude),
                "longitude": float(longitude),
                "description": description,
                "start_time": start_time_value.strftime("%H:%M"),
                "end_time": end_time_value.strftime("%H:%M"),
                "approved": False,
            }
            db.collection("events").add(doc)
            st.success(T["event_added"])

# -------------------------------------------------
# TAB: ADMIN
# -------------------------------------------------
elif active_tab == "admin":
    st.subheader(T["admin_tab"])

    password = st.text_input("Password", type="password")
    if password == st.secrets["admin"]["password"]:
        st.success("Admin access granted.")

        st.write(T["pending_events"])
        for e in pending_events:
            st.write(e)
            if st.button(T["approve"], key=e["id"]):
                db.collection("events").document(e["id"]).update({"approved": True})
                st.success(T["approved"])
                st.rerun()
    else:
        st.info("Enter admin password.")
