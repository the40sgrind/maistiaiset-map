import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import pandas as pd
from datetime import datetime, time
import requests  # for geocoding

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Maistiaiset Map", layout="wide")

# -------------------------------------------------
# FIREBASE INIT
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
        "universe_domain": "googleapis.com",
    })
    firebase_admin.initialize_app(cred, {
        "storageBucket": "maistiaisetmap-images"
    })

db = firestore.client()

# -------------------------------------------------
# TRANSLATIONS
# -------------------------------------------------
translations = {
    "fi": {
        "app_title": "Maistiaiset Map",
        "subtitle": "Kaikki Suomen ilmaiset maistiaiset yhdessä sovelluksessa.",

        "product_name": "Tuotteen nimi",
        "brand_id": "Brändin ID",
        "store_name": "Myymälä",
        "address": "Osoite",
        "city": "Kaupunki",

        "map_tab": "🗺️ Kartta",
        "list_tab": "📋 Lista",
        "form_tab": "➕ Lisää tapahtumia",
        "admin_tab": "🔧 Admin",

        "start_date": "Aloituspäivä",
        "end_date": "Lopetuspäivä",
        "start_time": "Aloitusaika",
        "end_time": "Lopetusaika",
        "manual_times_label": "Syötä ajat käsin",

        "approved": "Hyväksytty",
        "pending": "Odottaa hyväksyntää",

        "create_event": "Luo tapahtuma",
        "no_events": "Ei tapahtumia listattavaksi.",
        "no_events_map": "Ei tapahtumia kartalla.",

        "login_title": "Admin kirjautuminen",
        "password": "Salasana",
        "login_button": "Kirjaudu",
        "wrong_password": "Väärä salasana",
        "admin_panel": "Admin-paneeli",
        "approve_button": "Hyväksy",
        "approved_msg": "Hyväksytty!",

        "filters_title": "Suodata tapahtumia",
        "filter_brand": "Brändi",
        "filter_store": "Myymälä",
        "filter_from": "Alkaen",
        "filter_to": "Päättyen",
        "filter_clear": "Tyhjennä suodattimet",
    },

    "en": {
        "app_title": "Maistiaiset Map",
        "subtitle": "All free tasting events in Finland in one place.",

        "product_name": "Product Name",
        "brand_id": "Brand ID",
        "store_name": "Store Name",
        "address": "Address",
        "city": "City",

        "map_tab": "🗺️ Map",
        "list_tab": "📋 List",
        "form_tab": "➕ Add Event",
        "admin_tab": "🔧 Admin",

        "start_date": "Start Date",
        "end_date": "End Date",
        "start_time": "Start Time",
        "end_time": "End Time",
        "manual_times_label": "Type times manually",

        "approved": "Approved",
        "pending": "Pending approval",

        "create_event": "Create Event",
        "no_events": "No events available.",
        "no_events_map": "No events on the map.",

        "login_title": "Admin Login",
        "password": "Password",
        "login_button": "Login",
        "wrong_password": "Incorrect password",
        "admin_panel": "Admin Panel",
        "approve_button": "Approve",
        "approved_msg": "Approved!",

        "filters_title": "Filter events",
        "filter_brand": "Brand",
        "filter_store": "Store",
        "filter_from": "From date",
        "filter_to": "To date",
        "filter_clear": "Clear filters",
    },

    "sv": {
        "app_title": "Maistiaiset Map",
        "subtitle": "Alla gratis provsmakningar i Finland på ett ställe.",

        "product_name": "Produktnamn",
        "brand_id": "Varumärkes-ID",
        "store_name": "Butik",
        "address": "Adress",
        "city": "Stad",

        "map_tab": "🗺️ Karta",
        "list_tab": "📋 Lista",
        "form_tab": "➕ Lägg till evenemang",
        "admin_tab": "🔧 Admin",

        "start_date": "Startdatum",
        "end_date": "Slutdatum",
        "start_time": "Starttid",
        "end_time": "Sluttid",
        "manual_times_label": "Skriv tider manuellt",

        "approved": "Godkänd",
        "pending": "Väntar på godkännande",

        "create_event": "Skapa Evenemang",
        "no_events": "Inga evenemang att visa.",
        "no_events_map": "Inga evenemang på kartan.",

        "login_title": "Admin inloggning",
        "password": "Lösenord",
        "login_button": "Logga in",
        "wrong_password": "Fel lösenord",
        "admin_panel": "Adminpanel",
        "approve_button": "Godkänn",
        "approved_msg": "Godkänd!",

        "filters_title": "Filtrera evenemang",
        "filter_brand": "Varumärke",
        "filter_store": "Butik",
        "filter_from": "Från datum",
        "filter_to": "Till datum",
        "filter_clear": "Rensa filter",
    },
}

# -------------------------------------------------
# LANGUAGE + TAB STATE
# -------------------------------------------------
st.session_state.setdefault("lang", "fi")
st.session_state.setdefault("active_tab", "map")

lang_cols = st.columns([0.12, 0.12, 0.12, 0.64])
if lang_cols[0].button("🇫🇮 Suomi"):
    st.session_state.lang = "fi"
if lang_cols[1].button("🇬🇧 English"):
    st.session_state.lang = "en"
if lang_cols[2].button("🇸🇪 Svenska"):
    st.session_state.lang = "sv"

T = translations[st.session_state["lang"]]

# -------------------------------------------------
# TITLE + SPACING
# -------------------------------------------------
st.title(T["app_title"])
st.caption(T["subtitle"])
st.markdown("<div style='margin-top:-10px;'></div>", unsafe_allow_html=True)
st.markdown("---")

# -------------------------------------------------
# MOBILE-FRIENDLY TABS
# -------------------------------------------------
tab_keys = ["map", "list", "form", "admin"]
tab_labels = [T["map_tab"], T["list_tab"], T["form_tab"], T["admin_tab"]]

active_label = st.radio(
    "navigation",
    tab_labels,
    index=tab_keys.index(st.session_state["active_tab"]),
    horizontal=True,
    key="tab_selector",
    label_visibility="collapsed",
)

active = tab_keys[tab_labels.index(active_label)]

if active != st.session_state["active_tab"]:
    st.session_state["active_tab"] = active
    st.rerun()

st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------
# FILTER HELPERS
# -------------------------------------------------
def to_date(val):
    try:
        parsed = pd.to_datetime(val, utc=False)
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None

def apply_filters(df):
    if df.empty:
        return df

    df = df.copy()
    df["start_date_clean"] = df["start_time"].apply(to_date)
    df["end_date_clean"] = df["end_time"].apply(to_date)

    brands = sorted([b for b in df.get("brand_id", []).dropna().unique() if b])
    stores = sorted([s for s in df.get("store_name", []).dropna().unique() if s])

    st.markdown(f"### {T['filters_title']}")

    c1, c2 = st.columns(2)
    brand = c1.selectbox(T["filter_brand"], [""] + brands)
    store = c2.selectbox(T["filter_store"], [""] + stores)

    valid_starts = df["start_date_clean"].dropna()
    valid_ends = df["end_date_clean"].dropna()

    today = datetime.today().date()
    min_date = valid_starts.min() if not valid_starts.empty else today
    max_date = valid_ends.max() if not valid_ends.empty else today

    c3, c4, c5 = st.columns([1, 1, 0.7])
    date_from = c3.date_input(T["filter_from"], value=min_date)
    date_to = c4.date_input(T["filter_to"], value=max_date)

    if c5.button(T["filter_clear"]):
        st.rerun()

    f = df.copy()
    if brand:
        f = f[f["brand_id"] == brand]
    if store:
        f = f[f["store_name"] == store]
    if date_from:
        f = f[f["end_date_clean"] >= date_from]
    if date_to:
        f = f[f["start_date_clean"] <= date_to]

    st.markdown("<div style='margin-bottom:4px;'></div>", unsafe_allow_html=True)
    return f

# -------------------------------------------------
# FETCH EVENTS
# -------------------------------------------------
events = db.collection("events").stream()
events_list = [e.to_dict() for e in events]
events_df = pd.DataFrame(events_list)

events_public = (
    events_df[events_df["approved"] == True] if "approved" in events_df else events_df
)

filtered_df = apply_filters(events_public)
# -------------------------------------------------
# EVENT CARD (mobile-friendly + safe fallback image)
# -------------------------------------------------
def render_event_card(event):
    img_url = event.get("image_url")

    # Determine if image URL is valid
    valid_image = False
    if img_url and isinstance(img_url, str) and img_url.startswith("http"):
        valid_image = True

    if not valid_image:
        img_html = """
        <div style="width:100%; height:180px; background:#333;
                    border-radius:10px; display:flex; justify-content:center;
                    align-items:center; color:#bbb; font-size:0.9rem;">
            No image
        </div>
        """
    else:
        img_html = f"""
        <img src="{img_url}" style="width:100%; height:180px; object-fit:cover;
             border-radius:10px;" onerror="this.style.display='none';" />
        """

    html = f"""
    <div style="border-radius:12px; border:1px solid #333; padding:16px;
                margin-bottom:18px; background-color:#1e1e1e; color:#f2f2f2;">

        {img_html}

        <div style="margin-top:10px; display:flex; justify-content:space-between;
                    align-items:center;">

            <div style="font-weight:700; font-size:1.15rem;">
                {event.get('product_name','')}
                <span style="font-weight:400; color:#bbbbbb;">
                    {(" – " + event.get('brand_id','')) if event.get('brand_id') else ""}
                </span>
            </div>

            <div style="font-size:0.75rem; padding:3px 10px; border-radius:999px;
                        background-color:#00c85333; color:#00c853;
                        border:1px solid #00c85355; font-weight:600;">
                {T["approved"]}
            </div>
        </div>

        <div style="color:#ccc; margin-top:6px;">
            {event.get('store_name','')} • {event.get('address','')}, {event.get('city','')}
        </div>

        <div style="color:#aaa; margin-top:6px;">
            {event.get('start_time','')} – {event.get('end_time','')}
        </div>

        <div style="margin-top:10px; color:#e0e0e0;">
            {event.get('description','')}
        </div>

    </div>
    """
    st.html(html)


# -------------------------------------------------
# MAP TAB
# -------------------------------------------------
if st.session_state["active_tab"] == "map":
    if filtered_df.empty:
        st.info(T["no_events_map"])
    else:
        mdf = filtered_df.rename(columns={"latitude": "lat", "longitude": "lon"})
        st.map(mdf[["lat", "lon"]])


# -------------------------------------------------
# LIST TAB
# -------------------------------------------------
if st.session_state["active_tab"] == "list":
    if filtered_df.empty:
        st.info(T["no_events"])
    else:
        for _, row in filtered_df.iterrows():
            render_event_card(row)
# -------------------------------------------------
# GEOCODING FUNCTION (Address + City)
# -------------------------------------------------
def geocode_address(address, city):
    """Return (lat, lon) or None if not found."""
    try:
        query = f"{address}, {city}, Finland"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "fi",
        }
        response = requests.get(
            url, params=params, headers={"User-Agent": "MaistiaisetMap/1.0"}
        )
        data = response.json()
        if len(data) == 0:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None

# -------------------------------------------------
# FORM TAB
# -------------------------------------------------
if st.session_state["active_tab"] == "form":
    st.subheader(T["form_tab"])
    st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    bucket = storage.bucket()

    with st.form("event_form", clear_on_submit=True):

        # ---------------------------
        # BASIC FIELDS
        # ---------------------------
        product_name = st.text_input(T["product_name"])
        brand_id = st.text_input(T["brand_id"])
        store_name = st.text_input(T["store_name"])
        address = st.text_input(T["address"])
        city = st.text_input(T["city"])
        description = st.text_area("Description")

        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

        # IMAGE UPLOAD
        # collect an optional image file; upload will occur after the Firestore doc is created
        image_file = st.file_uploader("Image (optional)", type=["jpg", "jpeg", "png"])

        # ---------------------------
        # TIME INPUTS
        # ---------------------------
        manual_times = st.checkbox(T["manual_times_label"], value=False)

        colA, colB = st.columns(2)
        with colA:
            start_date = st.date_input(T["start_date"])
            start_time_val = (
                st.text_input(T["start_time"])
                if manual_times
                else st.time_input(T["start_time"], value=time(12, 0))
            )

        with colB:
            end_date = st.date_input(T["end_date"])
            end_time_val = (
                st.text_input(T["end_time"])
                if manual_times
                else st.time_input(T["end_time"], value=time(13, 0))
            )

        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(T["create_event"])

        if submitted:
            # TIME STRINGS
            start_str = (
                start_time_val if manual_times else start_time_val.strftime("%H:%M")
            )
            end_str = (
                end_time_val if manual_times else end_time_val.strftime("%H:%M")
            )

            # GEOCODE
            coords = geocode_address(address, city)
            if not coords:
                st.error(
                    "Could not find this address. Please check spelling or add city name."
                )
                st.stop()

            lat, lon = coords

            # BASE DOC
            base_doc = {
                "product_name": product_name,
                "brand_id": brand_id,
                "store_name": store_name,
                "address": address,
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "description": description,
                "start_time": f"{start_date} {start_str}",
                "end_time": f"{end_date} {end_str}",
                "approved": False,
            }

            # Create Firestore doc
            doc_ref = db.collection("events").document()
            doc_ref.set(base_doc)
            doc_id = doc_ref.id

            # IMAGE UPLOAD (fixed for uniform bucket-level access)
            if image_file:
                try:
                    blob = bucket.blob(f"events/{doc_id}/image.jpg")
                    blob.upload_from_file(image_file, content_type=image_file.type)

                    # Public URL format that works with uniform access
                    image_url = (
                        f"https://storage.googleapis.com/{bucket.name}/events/{doc_id}/image.jpg"
                    )

                    doc_ref.update({"image_url": image_url})

                except Exception as e:
                    st.warning(f"Image upload failed: {e}")

            st.success("Event submitted for approval!")

# -------------------------------------------------
# ADMIN TAB (includes Approve + Delete)
# -------------------------------------------------
if st.session_state["active_tab"] == "admin":
    st.subheader(T["login_title"])

    # Password field
    pwd = st.text_input(T["password"], type="password")

    # Login button
    if st.button(T["login_button"]):
        if pwd == st.secrets["admin"]["password"]:
            st.session_state["admin_logged_in"] = True
        else:
            st.error(T["wrong_password"])

    # If logged in, show pending + approved events
    if st.session_state.get("admin_logged_in"):
        st.header(T["admin_panel"])

        # Show ALL events (pending + approved)
        all_events = events_df if not events_df.empty else pd.DataFrame()

        if all_events.empty:
            st.info("No events available.")
        else:
            for index, row in all_events.iterrows():
                st.write("---")
                st.write(f"**{row['product_name']} – {row.get('brand_id','')}**")
                st.write(row["store_name"], "•", row["address"], "•", row.get("city", ""))
                st.write(f"{row['start_time']} – {row['end_time']}")
                st.write(row.get("description", ""))

                colA, colB = st.columns([1, 1])

                # APPROVE BUTTON
                with colA:
                    if not row.get("approved", False):
                        if st.button(T["approve_button"], key=f"approve_{index}"):
                            matches = (
                                db.collection("events")
                                .where("product_name", "==", row["product_name"])
                                .stream()
                            )
                            for ev in matches:
                                db.collection("events").document(ev.id).update(
                                    {"approved": True}
                                )
                            st.success(T["approved_msg"])
                            st.rerun()
                    else:
                        st.success("Approved")

                # DELETE BUTTON
                with colB:
                    if st.button("Delete", key=f"delete_{index}"):
                        matches = (
                            db.collection("events")
                            .where("product_name", "==", row["product_name"])
                            .stream()
                        )
                        for ev in matches:
                            db.collection("events").document(ev.id).delete()

                        st.warning("Event deleted.")
                        st.rerun()
