import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import pandas as pd
from datetime import datetime, time
import requests
import folium
from streamlit_folium import st_folium

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Maistiaiset Map", layout="wide")

# -------------------------------------------------
# MOBILE OPTIMIZATION (CSS + JS)
# -------------------------------------------------
st.markdown("""
<style>

    /* Remove Streamlit's massive default padding */
    .stApp {
        padding: 0 !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    /* Make radio tabs easier to tap on mobile */
    div[role='radiogroup'] > label {
        padding: 8px 14px !important;
        margin-right: 6px !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
    }

    /* Responsive title spacing */
    h1 {
        font-size: 1.7rem !important;
        margin-bottom: -4px !important;
    }

    /* Reduce spacing between cards on mobile */
    @media (max-width: 640px) {
        .event-card {
            margin-bottom: 14px !important;
        }
    }

    /* Improve Folium map usability on phones */
    @media (max-width: 640px) {
        iframe {
            height: 360px !important;
        }
    }

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# JS: Detect mobile & store in session_state
# -------------------------------------------------
mobile_detection_js = """
<script>
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    window.parent.postMessage({isMobile: isMobile}, "*");
</script>
"""

st.markdown(mobile_detection_js, unsafe_allow_html=True)

# Streamlit listener
mobile_flag = st.session_state.get("is_mobile", None)

def _mobile_listener():
    import streamlit as st
    msg = st.session_state.get("_js_message")
    if isinstance(msg, dict) and "isMobile" in msg:
        st.session_state["is_mobile"] = msg["isMobile"]

st.session_state.setdefault("_js_message", None)

# -------------------------------------------------
# FIREBASE INIT
# -------------------------------------------------
firebase_config = st.secrets["firebase"]

if not firebase_admin._apps:
    cred = credentials.Certificate(
        {
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
            "universe_domain": firebase_config.get("universe_domain", "googleapis.com"),
        }
    )
    firebase_admin.initialize_app(
        cred,
        {
            "storageBucket": "maistiaisetmap-images",
        },
    )

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
# TABS (RADIO NAVIGATION)
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
# DATE/TIME HELPERS
# -------------------------------------------------
def to_datetime(val):
    """Best-effort conversion of Firestore Timestamp / string → datetime."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val
    if hasattr(val, "to_datetime"):
        try:
            return val.to_datetime()
        except Exception:
            pass
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


def format_dt_eu(val):
    """Return DD-MM-YYYY HH:MM or empty string."""
    dt = to_datetime(val)
    if dt is None or pd.isna(dt):
        return ""
    return dt.strftime("%d-%m-%Y %H:%M")


def to_date(val):
    """Return date() from datetime-like, or None."""
    dt = to_datetime(val)
    if dt is None or pd.isna(dt):
        return None
    return dt.date()
# -------------------------------------------------
# FILTER HELPERS (FINAL – KEEP ALL COLUMNS)
# -------------------------------------------------
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Filter events by brand, store, and date — without dropping columns."""
    if df is None or df.empty:
        return df

    df = df.copy()

    # Extract clean date columns (for filtering)
    df["start_date_clean"] = df["start_time"].apply(to_date)
    df["end_date_clean"] = df["end_time"].apply(to_date)

    # Dropdown values
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
# FETCH EVENTS + INCLUDE FIRESTORE DOC IDS
# -------------------------------------------------
events_raw = db.collection("events").stream()

events_list = []
for e in events_raw:
    doc = e.to_dict()
    doc["id"] = e.id            # <-- Firestore doc ID added
    events_list.append(doc)

events_df = pd.DataFrame(events_list)

# Only approved events appear publicly
if not events_df.empty and "approved" in events_df.columns:
    events_public = events_df[events_df["approved"] == True].copy()
else:
    events_public = events_df.copy()


# -------------------------------------------------
# NORMALIZE FIELDS (NO TYPE DAMAGE)
# -------------------------------------------------
def fix_datetime(v):
    """Convert Firestore Timestamp or string to datetime."""
    if v is None or v == "":
        return None
    if hasattr(v, "to_datetime"):
        try:
            return v.to_datetime()
        except:
            pass
    try:
        return pd.to_datetime(v)
    except:
        return None

def normalize_events(df):
    if df.empty:
        return df

    df = df.copy()

    # preserve image_url, lat, lon, strings etc.
    if "start_time" in df:
        df["start_dt"] = df["start_time"].apply(fix_datetime)
    if "end_time" in df:
        df["end_dt"] = df["end_time"].apply(fix_datetime)

    # derived EU formats for map/list
    df["start_fmt"] = df["start_dt"].apply(
        lambda x: x.strftime("%d-%m-%Y %H:%M") if x else ""
    )
    df["end_fmt"] = df["end_dt"].apply(
        lambda x: x.strftime("%d-%m-%Y %H:%M") if x else ""
    )

    # clean date-only fields for filters
    df["start_date_clean"] = df["start_dt"].apply(lambda x: x.date() if x else None)
    df["end_date_clean"] = df["end_dt"].apply(lambda x: x.date() if x else None)

    return df

events_clean = normalize_events(events_public)

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
filtered_df = apply_filters(events_clean.copy())


# -------------------------------------------------
# EVENT CARD (LIST TAB)
# -------------------------------------------------
def render_event_card(event: pd.Series) -> None:
    img_url = event.get("image_url")
    valid_image = img_url and isinstance(img_url, str) and img_url.startswith("http")

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

    start_fmt = format_dt_eu(event.get("start_time"))
    end_fmt = format_dt_eu(event.get("end_time"))

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
            {start_fmt} – {end_fmt}
        </div>

        <div style="margin-top:10px; color:#e0e0e0;">
            {event.get('description','')}
        </div>

    </div>
    """
    st.html(html)


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
# MAP TAB (Folium – Dark Map + Violet Markers + Thumbnails)
# -------------------------------------------------
if st.session_state["active_tab"] == "map":

    if filtered_df.empty:
        st.info(T["no_events_map"])

    else:
        # Recompute formats from start_time / end_time to be safe
        def format_dt_for_map(v):
            try:
                dt = to_datetime(v)
                if dt:
                    return dt.strftime("%d-%m-%Y %H:%M")
                return ""
            except Exception:
                return ""

        mdf = filtered_df.copy()
        mdf["start_fmt"] = mdf["start_time"].apply(format_dt_for_map)
        mdf["end_fmt"] = mdf["end_time"].apply(format_dt_for_map)

        # Safe float conversion for lat/lon
        def safe_float(x):
            try:
                return float(x)
            except Exception:
                return None

        mdf["lat_clean"] = mdf["latitude"].apply(safe_float)
        mdf["lon_clean"] = mdf["longitude"].apply(safe_float)
        mdf = mdf.dropna(subset=["lat_clean", "lon_clean"])

        if mdf.empty:
            st.info("No valid coordinates to show.")
            st.stop()

        avg_lat = mdf["lat_clean"].mean()
        avg_lon = mdf["lon_clean"].mean()

        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=11,
            tiles="CartoDB dark_matter",
            control_scale=True,
        )

        bounds = []

        for _, row in mdf.iterrows():
            img_url = row.get("image_url", "")
            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                thumb_html = f"""
                    <img src="{img_url}"
                         style="width:100%; height:150px; object-fit:cover;
                                border-radius:10px; margin-bottom:10px;" />
                """
            else:
                thumb_html = """
                    <div style="width:100%; height:150px; background:#333;
                                border-radius:10px; margin-bottom:10px;
                                display:flex; justify-content:center; align-items:center;
                                color:#bbb; font-size:0.9rem;">
                        No image
                    </div>
                """

            popup_html = f"""
            <div style="
                font-size:14px;
                line-height:1.6;
                background:#1e1e1e;
                color:#f2f2f2;
                padding:16px;
                border-radius:12px;
                width:240px;
                overflow:hidden;
            ">

                {thumb_html}

                <div style="font-size:16px; font-weight:700; color:#ffffff;">
                    {row.get('product_name', '')}
                </div>

                <div style="color:#bbbbbb; margin-bottom:8px;">
                    {row.get('brand_id', '')}
                </div>

                <div style="margin-bottom:6px; color:#e0e0e0;">
                    <b>{row.get('store_name','')}</b><br>
                    {row.get('address','')}, {row.get('city','')}
                </div>

                <div style="color:#cccccc; margin-bottom:8px;">
                    <b>{row.get('start_fmt','')}</b> – <b>{row.get('end_fmt','')}</b>
                </div>

                <div style="color:#dddddd;">
                    {row.get('description','')}
                </div>

            </div>
            """

            popup = folium.Popup(
                folium.IFrame(popup_html, width=260, height=350),
                max_width=260,
            )

            folium.CircleMarker(
                location=[row["lat_clean"], row["lon_clean"]],
                radius=10,
                color="#9C27B0",
                fill=True,
                fill_color="#9C27B0",
                fill_opacity=0.85,
                popup=popup,
            ).add_to(m)

            bounds.append([row["lat_clean"], row["lon_clean"]])

        if len(bounds) > 0:
            m.fit_bounds(bounds, padding=(20, 20))

        st_folium(m, width="100%", height=520)


# -------------------------------------------------
# GEOCODING (Address + City)
# -------------------------------------------------
def geocode_address(address, city):
    """Return (lat, lon) from Nominatim or None."""
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
            url,
            params=params,
            headers={"User-Agent": "MaistiaisetMap/1.0"},
            timeout=10,
        )
        data = response.json()
        if not data:
            return None

        return float(data[0]["lat"]), float(data[0]["lon"])

    except Exception:
        return None
# -------------------------------------------------
# FORM TAB (Event Submission) — FIXED & CLEAN
# -------------------------------------------------
if st.session_state["active_tab"] == "form":
    st.subheader(T["form_tab"])
    st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    bucket = storage.bucket()

    with st.form("event_form", clear_on_submit=True):

        # BASIC FIELDS
        product_name = st.text_input(T["product_name"])
        brand_id     = st.text_input(T["brand_id"])
        store_name   = st.text_input(T["store_name"])
        address      = st.text_input(T["address"])
        city         = st.text_input(T["city"])
        description  = st.text_area("Description")

        st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

        # IMAGE UPLOAD (optional)
        image_file = st.file_uploader("Image (optional)", type=["jpg", "jpeg", "png"])

        # TIME INPUTS
        manual_times = st.checkbox(T["manual_times_label"], value=False)

        colA, colB = st.columns(2)

        with colA:
            start_date = st.date_input(T["start_date"])
            start_time_val = (
                st.text_input(T["start_time"])
                if manual_times else st.time_input(T["start_time"], value=time(12,0))
            )

        with colB:
            end_date = st.date_input(T["end_date"])
            end_time_val = (
                st.text_input(T["end_time"])
                if manual_times else st.time_input(T["end_time"], value=time(13,0))
            )

        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(T["create_event"])

        # -------------------------------------------------
        # ON SUBMIT
        # -------------------------------------------------
        if submitted:

            # Convert times to strings
            start_str = start_time_val if manual_times else start_time_val.strftime("%H:%M")
            end_str   = end_time_val if manual_times else end_time_val.strftime("%H:%M")

            # --- DATE VALIDATION (fix disappearing events) ---
            start_dt = pd.to_datetime(f"{start_date} {start_str}", errors="coerce")
            end_dt   = pd.to_datetime(f"{end_date} {end_str}", errors="coerce")

            if start_dt is None or end_dt is None or pd.isna(start_dt) or pd.isna(end_dt):
                st.error("Invalid date or time format.")
                st.stop()

            if end_dt < start_dt:
                st.error("End time cannot be earlier than the start time.")
                st.stop()

            # GEOCODE ADDRESS → lat/lon
            coords = geocode_address(address, city)
            if not coords:
                st.error("Could not find this address. Please check spelling or add city name.")
                st.stop()

            lat, lon = coords

            # FIRESTORE DOCUMENT BASE
            base_doc = {
                "product_name": product_name,
                "brand_id": brand_id,
                "store_name": store_name,
                "address": address,
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "description": description,
                "start_time": start_dt.strftime("%Y-%m-%d %H:%M"),
                "end_time": end_dt.strftime("%Y-%m-%d %H:%M"),
                "approved": False,
            }

            # Create Firestore document
            doc_ref = db.collection("events").document()
            doc_ref.set(base_doc)
            doc_id = doc_ref.id

            # -------------------------------------------------
            # IMAGE UPLOAD (FINAL — works with uniform bucket access)
            # -------------------------------------------------
            if image_file:
                try:
                    blob = bucket.blob(f"events/{doc_id}/image.jpg")
                    blob.upload_from_file(image_file, content_type=image_file.type)

                    # Signed URL (no ACL needed)
                    image_url = f"https://storage.googleapis.com/{bucket.name}/events/{doc_id}/image.jpg"

                    doc_ref.update({"image_url": image_url})

                except Exception as e:
                    st.warning(f"Image upload failed: {e}")

            st.success("Event submitted for approval!")

# -------------------------------------------------
# ADMIN TAB (Login, Logout, Approve, Delete)
# -------------------------------------------------
if st.session_state["active_tab"] == "admin":
    st.subheader(T["login_title"])

    # LOGIN FORM
    pwd = st.text_input(T["password"], type="password")
    login_btn = st.button(T["login_button"])

    if login_btn:
        if pwd == st.secrets["admin"]["password"]:
            st.session_state["admin_logged_in"] = True
            st.success("Logged in!")
            st.rerun()
        else:
            st.error(T["wrong_password"])

    # If logged in, show admin panel
    if st.session_state.get("admin_logged_in"):

        # LOGOUT BUTTON
        st.write("---")
        if st.button("Logout"):
            st.session_state["admin_logged_in"] = False
            st.success("Logged out.")
            st.rerun()

        st.header(T["admin_panel"])

        all_events = events_df if not events_df.empty else pd.DataFrame()

        if all_events.empty:
            st.info("No events available.")
        else:
            for index, row in all_events.iterrows():
                st.write("---")

                st.write(f"**{row.get('product_name','')} – {row.get('brand_id','')}**")
                st.write(
                    row.get("store_name", ""),
                    "•",
                    row.get("address", ""),
                    "•",
                    row.get("city", ""),
                )
                st.write(f"{row.get('start_time','')} – {row.get('end_time','')}")
                st.write(row.get("description", ""))

                colA, colB = st.columns([1, 1])

                # APPROVE BUTTON
                with colA:
                    if not row.get("approved", False):
                        if st.button(T["approve_button"], key=f"approve_{index}"):

                            # Approve THIS exact document using its Firestore ID
                            db.collection("events").document(row["id"]).update(
                                {"approved": True}
                            )

                            st.success(T["approved_msg"])
                            st.rerun()
                    else:
                        st.success(T["approved"])

                # DELETE BUTTON
                with colB:
                    if st.button("Delete", key=f"delete_{index}"):

                        db.collection("events").document(row["id"]).delete()

                        st.warning("Event deleted.")
                        st.rerun()
