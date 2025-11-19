import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
import pandas as pd
from datetime import datetime, time, timedelta

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
        "universe_domain": "googleapis.com"
    })
    # Set default storage bucket to your custom bucket
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

        # Step 7 filters
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

        # Step 7 filters
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

        # Step 7 filters
        "filters_title": "Filtrera evenemang",
        "filter_brand": "Varumärke",
        "filter_store": "Butik",
        "filter_from": "Från datum",
        "filter_to": "Till datum",
        "filter_clear": "Rensa filter",
    }
}

# -------------------------------------------------
# LANGUAGE + TAB STATE
# -------------------------------------------------
st.session_state.setdefault("lang", "fi")
st.session_state.setdefault("active_tab", "map")

cols = st.columns([0.12, 0.12, 0.12, 0.64])
if cols[0].button("🇫🇮 Suomi"):
    st.session_state.lang = "fi"
if cols[1].button("🇬🇧 English"):
    st.session_state.lang = "en"
if cols[2].button("🇸🇪 Svenska"):
    st.session_state.lang = "sv"

T = translations[st.session_state["lang"]]

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title(T["app_title"])
st.caption(T["subtitle"])
st.markdown("---")

# -------------------------------------------------
# EMOJI-SAFE RADIO TABS
# -------------------------------------------------
tab_keys = ["map", "list", "form", "admin"]
tab_labels = [T["map_tab"], T["list_tab"], T["form_tab"], T["admin_tab"]]

active_label = st.radio(
    "navigation",
    tab_labels,
    index=tab_keys.index(st.session_state["active_tab"]),
    horizontal=True,
    key="tab_selector",
    label_visibility="collapsed"
)

active = tab_keys[tab_labels.index(active_label)]

if active != st.session_state["active_tab"]:
    st.session_state["active_tab"] = active
    st.rerun()

# -------------------------------------------------
# TIME CLEANER (DISPLAY ONLY)
# -------------------------------------------------
def clean_time(v):
    try:
        if hasattr(v, "strftime"):
            return v.strftime("%H:%M")
    except Exception:
        pass

    s = str(v).strip()

    if " " in s and ":" in s:
        try:
            return datetime.fromisoformat(s.replace("Z", "")).strftime("%H:%M")
        except Exception:
            pass

    if len(s) == 5 and s[2] == ":":
        return s

    if "klo" in s:
        try:
            return s.split("klo")[1].strip()
        except Exception:
            pass

    return s

# -------------------------------------------------
# PARSE MANUAL TIME INPUT (FOR STORAGE)
# -------------------------------------------------
def parse_manual_time_string(s: str) -> time:
    s = str(s).strip()
    if "klo" in s:
        s = s.split("klo")[-1].strip()
    s = s.replace(".", ":")
    if len(s) == 5 and s[2] == ":":
        try:
            return datetime.strptime(s, "%H:%M").time()
        except Exception:
            pass
    # fallback default
    return time(12, 0)

# -------------------------------------------------
# EVENT CARD (WITH IMAGE SUPPORT)
# -------------------------------------------------
def render_event_card(event):
    start = clean_time(event.get("start_time"))
    end = clean_time(event.get("end_time"))

    image_url = event.get("image_url")
    if image_url:
        image_html = f"""
        <div style="margin-bottom:10px;">
            <img src="{image_url}" 
                 style="width:100%; max-height:220px; object-fit:cover; border-radius:10px;" />
        </div>
        """
    else:
        # Fallback placeholder for old events
        image_html = """
        <div style="margin-bottom:10px; height:180px; border-radius:10px;
                    background:linear-gradient(135deg,#333,#222);
                    display:flex; align-items:center; justify-content:center;
                    color:#777; font-size:0.9rem;">
            No image
        </div>
        """

    html = f"""
    <div style="border-radius: 12px; border: 1px solid #333; padding: 18px;
                margin-bottom: 16px; background-color: #1e1e1e; color: #f2f2f2;">
        {image_html}
        <div style="display: flex; justify-content: space-between;
                    align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 700; font-size: 1.2rem;">
                {event.get('product_name','')}
                <span style="font-weight:400; color:#bbbbbb;">
                    {('– ' + event.get('brand_id','')) if event.get('brand_id') else ''}
                </span>
            </div>

            <div style="font-size: 0.8rem; padding: 3px 10px; border-radius: 999px;
                        background-color: #00c85333; color: #00c853;
                        border: 1px solid #00c85355; font-weight: 600;">
                {T["approved"]}
            </div>
        </div>

        <div style="color:#e0e0e0; margin-top:6px;">
            {event.get('store_name','')} • {event.get('address','')}
        </div>

        <div style="color:#cccccc; margin-top:6px;">
            {start} – {end}
        </div>

        <div style="margin-top:10px;">
            {event.get('description','')}
        </div>
    </div>
    """

    st.html(html)

# -------------------------------------------------
# FETCH EVENTS FROM FIRESTORE
# -------------------------------------------------
events = db.collection("events").stream()
events_list = [e.to_dict() for e in events]
events_df = pd.DataFrame(events_list)

events_public = (
    events_df[events_df["approved"] == True] if "approved" in events_df else events_df
)

# -------------------------------------------------
# STEP 7 – FILTERS (BRAND / STORE / DATE RANGE)
# -------------------------------------------------
def to_date(val):
    """Convert Firestore value or string to datetime.date (for filtering)."""
    # Case 1: already datetime (Firestore timestamp or Python datetime)
    if hasattr(val, "date"):
        try:
            return val.date()
        except Exception:
            pass

    s = str(val).strip()
    if not s:
        return None

    # Case 2: looks like plain time "HH:MM" → fallback: today
    if len(s) == 5 and s[2] == ":":
        return datetime.today().date()

    # Try generic parsing
    try:
        parsed = pd.to_datetime(s, utc=False)
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def apply_filters(df):
    if df.empty:
        st.markdown(f"### {T['filters_title']}")
        st.info(T["no_events"])
        return df

    df = df.copy()

    # Build clean date columns (no timezone issues)
    df["start_date_clean"] = df["start_time"].apply(to_date)
    df["end_date_clean"] = df["end_time"].apply(to_date)

    # Brand / store options
    brands = sorted([b for b in df.get("brand_id", pd.Series([])).dropna().unique() if b])
    stores = sorted([s for s in df.get("store_name", pd.Series([])).dropna().unique() if s])

    st.markdown(f"### {T['filters_title']}")

    col1, col2 = st.columns(2)
    brand = col1.selectbox(T["filter_brand"], [""] + brands)
    store = col2.selectbox(T["filter_store"], [""] + stores)

    # Date defaults from valid rows only
    valid_starts = df["start_date_clean"].dropna()
    valid_ends = df["end_date_clean"].dropna()

    today = datetime.today().date()
    min_date = valid_starts.min() if not valid_starts.empty else today
    max_date = valid_ends.max() if not valid_ends.empty else today

    col3, col4, col5 = st.columns([1, 1, 0.7])

    date_from = col3.date_input(T["filter_from"], value=min_date)
    date_to = col4.date_input(T["filter_to"], value=max_date)

    if col5.button(T["filter_clear"]):
        st.rerun()

    # Apply filters
    f = df.copy()

    if brand:
        f = f[f["brand_id"] == brand]

    if store:
        f = f[f["store_name"] == store]

    if date_from:
        f = f[f["end_date_clean"] >= date_from]

    if date_to:
        f = f[f["start_date_clean"] <= date_to]

    return f

# Apply filters to public events
filtered_df = apply_filters(events_public)

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
# FORM TAB – NOW SAVES REAL DATETIMES + IMAGE
# -------------------------------------------------
if st.session_state["active_tab"] == "form":
    st.subheader(T["form_tab"])

    with st.form("event_form"):

        product_name = st.text_input(T["product_name"])
        brand_id = st.text_input(T["brand_id"])
        store_name = st.text_input(T["store_name"])
        address = st.text_input(T["address"])
        latitude = st.number_input("Latitude", format="%.6f")
        longitude = st.number_input("Longitude", format="%.6f")
        description = st.text_area("Description")
        image_file = st.file_uploader("Event image (optional)", type=["png", "jpg", "jpeg"])

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

        submitted = st.form_submit_button(T["create_event"])

        if submitted:
            # Convert manual or widget times into time objects
            if manual_times:
                start_time_obj = parse_manual_time_string(start_time_val)
                end_time_obj = parse_manual_time_string(end_time_val)
            else:
                start_time_obj = start_time_val  # already datetime.time
                end_time_obj = end_time_val

            # Real datetime objects for Firestore
            start_dt = datetime.combine(start_date, start_time_obj)
            end_dt = datetime.combine(end_date, end_time_obj)

            # Base event document
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
                "approved": False,
            }

            # Create a document reference first so we know its ID
            doc_ref = db.collection("events").document()

            # Handle image upload if provided
            if image_file is not None:
                try:
                    bucket = storage.bucket()  # uses default "maistiaisetmap-images"
                    blob = bucket.blob(f"events/{doc_ref.id}/image")

                    # Read file bytes and upload
                    file_bytes = image_file.read()
                    blob.upload_from_string(file_bytes, content_type=image_file.type)

                    # Generate long-lived signed URL (1 year)
                    url = blob.generate_signed_url(
                        expiration=timedelta(days=365),
                        method="GET"
                    )
                    doc["image_url"] = url
                except Exception as e:
                    st.warning(f"Image upload failed: {e}")

            # Save event to Firestore
            doc_ref.set(doc)
            st.success("Event submitted for approval!")

# -------------------------------------------------
# ADMIN TAB
# -------------------------------------------------
if st.session_state["active_tab"] == "admin":
    st.subheader(T["login_title"])

    pwd = st.text_input(T["password"], type="password")
    if st.button(T["login_button"]):
        if pwd == st.secrets["admin"]["password"]:
            st.session_state["admin_logged_in"] = True
        else:
            st.error(T["wrong_password"])

    if st.session_state.get("admin_logged_in"):
        st.header(T["admin_panel"])

        pending = (
            events_df[events_df["approved"] == False]
            if "approved" in events_df
            else pd.DataFrame()
        )

        for index, row in pending.iterrows():
            st.write("---")
            st.write(f"**{row['product_name']} – {row.get('brand_id','')}**")
            st.write(row["store_name"], "•", row["address"])
            st.write(f"{clean_time(row['start_time'])} – {clean_time(row['end_time'])}")
            st.write(row["description"])

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
