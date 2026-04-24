import io
import os
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus.doctemplate import IndexingFlowable
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DictionaryObject, ArrayObject, NameObject, NumberObject,
    TextStringObject,
)

LOGO_PATH = "cec_logo.png"

# ── Prepopulated data ─────────────────────────────────────────────────────────

CONTACTS = {
    "Lisa Worrall": "916-661-8367",
    "Eric Veerkamp": "916-555-0202",
    "Renee Longman": "916-937-3538",
    "Ali Jahani": "916-555-0404",
}

# ── Load project presets from ODS ─────────────────────────────────────────────

BOOLEAN_FIELDS = {
    "ceqa_nop", "ceqa_early_cons", "ceqa_neg_dec", "ceqa_mit_neg", "ceqa_draft_eir", "ceqa_sub_eir",
    "ceqa_other_check", "nepa_section", "nepa_noi", "nepa_ea", "nepa_eis", "nepa_fonsi",
    "other_section", "other_joint", "other_final", "other_custom_check",
    "lat_gpu", "lat_gpa", "lat_gpe", "lat_cp", "lat_sp", "lat_mp", "lat_pud", "lat_rezone",
    "lat_prezone", "lat_annex", "lat_redevel", "lat_use", "lat_coastal", "lat_site", "lat_land_div",
    "lat_other_check", "dev_power", "dev_power_wind", "dev_power_solar", "dev_power_bess", "dev_power_other",
    "dev_nonpower", "dev_residential", "dev_office", "dev_commercial", "dev_industrial", "dev_educational",
    "dev_recreational", "dev_water", "dev_transportation", "dev_mining", "dev_waste", "dev_hazardous",
    "dev_other", "issue_aesthetic_visual", "issue_agricultural_land", "issue_air_quality",
    "issue_archeological_historical", "issue_biological_resources", "issue_coastal_zone", "issue_cumulative_effects",
    "issue_drainage_absorption", "issue_economic_jobs", "issue_energy", "issue_fiscal",
    "issue_flood_plain_flooding", "issue_forest_land_fire_hazard", "issue_geologic_seismic",
    "issue_greenhouse_gas_emissions", "issue_growth_inducement", "issue_land_use", "issue_minerals",
    "issue_noise", "issue_other", "issue_population_housing_balance", "issue_public_services_facilities",
    "issue_recreation_parks", "issue_schools_universities", "issue_septic_systems", "issue_sewer_capacity",
    "issue_soil_erosion_compaction_grading", "issue_solid_waste", "issue_toxic_hazardous",
    "issue_traffic_circulation", "issue_tribal_cultural_resources", "issue_vegetation", "issue_water_quality",
    "issue_water_supply_groundwater", "issue_wetland_riparian", "ra_air", "ra_boating", "ra_cal_ema",
    "ra_chp", "ra_caltrans_dist", "ra_caltrans_aero", "ra_caltrans_plan", "ra_cvfpb", "ra_coachella",
    "ra_coastal", "ra_colorado", "ra_conservation", "ra_corrections", "ra_delta", "ra_education", "ra_energy",
    "ra_fish", "ra_food", "ra_forestry", "ra_general_svc", "ra_health", "ra_housing", "ra_nahc", "ra_ohp",
    "ra_opsc", "ra_parks", "ra_pesticide", "ra_puc", "ra_wqcb", "ra_resources", "ra_recycling", "ra_sfbay",
    "ra_san_gabriel", "ra_san_joaquin", "ra_santa_monica", "ra_state_lands", "ra_swrcb_cwg", "ra_swrcb_wq",
    "ra_swrcb_wr", "ra_tahoe", "ra_toxic", "ra_water_res",
}
DATE_FIELDS = {"review_start", "review_end"}

HEADER_ALIASES = {
    "county": "county",
    "project_county": "county",
    "city": "city",
    "project_city": "city",
    "zip": "zip",
    "project_zip": "zip",
    "latgpu": "lat_gpu",
    "latgpa": "lat_gpa",
    "latgpe": "lat_gpe",
    "latcp": "lat_cp",
    "latsp": "lat_sp",
    "latmp": "lat_mp",
    "latpud": "lat_pud",
    "latrezone": "lat_rezone",
    "latprezone": "lat_prezone",
    "latannex": "lat_annex",
    "latredevel": "lat_redevel",
    "latuse": "lat_use",
    "latcoastal": "lat_coastal",
    "latsite": "lat_site",
    "latlanddiv": "lat_land_div",
    "latothercheck": "lat_other_check",
    "latothertext": "lat_other_text",
    "lafirmname": "la_firm_name",
    "lafirmaddress": "la_firm_address",
    "lafirmcsz": "la_firm_csz",
    "lafirmcontact": "la_firm_contact",
    "lafirmphone": "la_firm_phone",
    "laappname": "la_app_name",
    "laappaddress": "la_app_address",
    "laappcsz": "la_app_csz",
    "laappphone": "la_app_phone",
}


def normalize_header(name):
    if name is None:
        return ""
    raw = str(name).strip()
    if not raw:
        return ""
    compact = "".join(ch for ch in raw.lower() if ch.isalnum())
    return HEADER_ALIASES.get(compact, raw)


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "t", "yes", "y", "1", "x"):
        return True
    if s in ("false", "f", "no", "n", "0", ""):
        return False
    return default


def clean_scalar(value, fallback=""):
    if value is None:
        return fallback
    s = str(value).strip()
    return fallback if s in ("", "nan", "None", "NaT") else s


def parse_date_value(value):
    if value is None:
        return None
    try:
        import pandas as pd
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


@st.cache_data
def load_presets():
    import pandas as pd
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [os.path.join(base_dir, "project_data.ods"), os.path.join(base_dir, "project_data(5).ods")]
    candidate_paths.extend(
        os.path.join(base_dir, name)
        for name in sorted(os.listdir(base_dir))
        if name.lower().endswith(".ods")
    )
    ods_path = next((path for path in candidate_paths if os.path.exists(path)), None)
    if not ods_path:
        st.warning(f"No project_data ODS file found in: {base_dir}")
        return {}
    try:
        df = pd.read_excel(ods_path, engine="odf", dtype=object)
        df = df.rename(columns=lambda col: normalize_header(col))
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.dropna(how="all")
        presets = {}
        for _, row in df.iterrows():
            raw_row = {normalize_header(key): value for key, value in row.to_dict().items()}
            row_dict = {}
            for key, raw_value in raw_row.items():
                if not key:
                    continue
                if key in BOOLEAN_FIELDS:
                    row_dict[key] = parse_bool(raw_value, False)
                elif key in DATE_FIELDS:
                    row_dict[key] = parse_date_value(raw_value)
                else:
                    row_dict[key] = clean_scalar(raw_value, "")
            title = clean_scalar(row_dict.get("project_title", ""), "")
            if title:
                presets[title] = row_dict
        return presets
    except Exception as e:
        st.error(f"Failed to load project presets from ODS: {e}")
        return {}

PRESETS = load_presets()
PROJECT_TITLES = list(PRESETS.keys()) if PRESETS else []

def preset_val(preset, key, fallback=""):
    if not preset:
        return fallback
    return clean_scalar(preset.get(key, fallback), fallback)

def preset_bool(preset, key, fallback=False):
    if not preset:
        return fallback
    return parse_bool(preset.get(key), fallback)

def preset_date(preset, key):
    if not preset:
        return None
    return parse_date_value(preset.get(key))


def hydrate_conditional_text(preset, key):
    """Ensure conditional text inputs pick up ODS values when first shown."""
    if not preset:
        return
    current = clean_scalar(st.session_state.get(key, ""), "")
    if current:
        return
    preset_value = preset_val(preset, key, "")
    if preset_value:
        st.session_state[key] = preset_value

FIELD_KEY_MAP = {
    "county": "project_county",
    "city": "project_city",
    "zip": "project_zip",
}


def apply_preset_to_session(project_title):
    preset = PRESETS.get(project_title, {})
    if st.session_state.get("_loaded_project_title") == project_title:
        return preset
    if not project_title:
        st.session_state["_loaded_project_title"] = ""
        return {}
    for key, value in preset.items():
        if key == "project_title":
            continue
        target_key = FIELD_KEY_MAP.get(key, key)
        if key in BOOLEAN_FIELDS:
            st.session_state[target_key] = parse_bool(value, False)
        elif key in DATE_FIELDS:
            parsed_date = parse_date_value(value)
            st.session_state[target_key] = parsed_date
            if key == "review_start":
                st.session_state.date_start = parsed_date
            elif key == "review_end":
                st.session_state.date_end = parsed_date
        else:
            st.session_state[target_key] = clean_scalar(value, "")
    if clean_scalar(preset.get("contact_name"), ""):
        st.session_state["contact_name"] = clean_scalar(preset.get("contact_name"), "")
    st.session_state["_loaded_project_title"] = project_title
    return preset


# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Notice of Completion Generator", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Georgia&display=swap');

/* ── Force light mode everywhere ── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stSidebar"], [data-baseweb="select"],
[data-baseweb="popover"], [role="listbox"], [role="option"],
[data-baseweb="menu"], [data-baseweb="input"],
[data-baseweb="textarea"], [data-testid="stForm"] {
    color-scheme: light !important;
    background-color: unset;
}

/* Force all select/dropdown menus to light */
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-baseweb="popover"] > div,
[role="listbox"],
[role="option"] {
    background-color: #fffef5 !important;
    color: #1a2a3a !important;
}

[role="option"]:hover {
    background-color: #ccd8e8 !important;
    color: #001a33 !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, header[data-testid="stHeader"], footer { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Page background ── */
.stApp {
    background-color: #d4dce8;
    background-image: url("data:image/svg+xml,%3Csvg width='4' height='4' viewBox='0 0 4 4' xmlns='http://www.w3.org/2000/svg'%3E%3Crect x='0' y='0' width='1' height='1' fill='%23b0bccf' fill-opacity='0.18'/%3E%3C/svg%3E");
}

/* ── Main content wrapper ── */
.block-container {
    background-color: #f0f4f8;
    border: 2px solid #7a92aa;
    border-top: 4px solid #003366;
    padding: 18px 28px 28px 28px !important;
    max-width: 760px !important;
    box-shadow: 3px 3px 0px #7a92aa, 6px 6px 0px #b0bccf;
}

/* ── Page title banner ── */
h1 {
    font-family: Georgia, "Times New Roman", serif !important;
    font-size: 1.25rem !important;
    font-weight: bold !important;
    color: #ffffff !important;
    background: linear-gradient(180deg, #2a5298 0%, #003366 100%);
    border: 2px outset #5577aa;
    padding: 8px 14px !important;
    margin-bottom: 2px !important;
    letter-spacing: 0.01em;
    text-shadow: 1px 1px 2px #001a33;
}

/* ── Caption / subtitle ── */
.stCaption, [data-testid="stCaptionContainer"] p {
    font-family: Georgia, "Times New Roman", serif !important;
    font-size: 0.78rem !important;
    color: #4a5568 !important;
    font-style: italic;
    margin-top: 0px !important;
    padding-left: 2px;
}

/* ── Section subheaders ── */
h2, h3 {
    font-family: Georgia, "Times New Roman", serif !important;
    font-size: 0.95rem !important;
    font-weight: bold !important;
    color: #ffffff !important;
    background: linear-gradient(180deg, #4a6fa5 0%, #2a4a7f 100%);
    border: 1px outset #7a92aa;
    padding: 4px 10px !important;
    margin-top: 14px !important;
    margin-bottom: 6px !important;
    letter-spacing: 0.02em;
}

/* ── Body text / labels ── */
label, .stTextInput label, .stSelectbox label,
.stTextArea label, p, li {
    font-family: Verdana, Tahoma, Geneva, sans-serif !important;
    font-size: 0.78rem !important;
    color: #1a2a3a !important;
}

/* ── Inputs ── */
input[type="text"], textarea, select,
.stTextInput input, .stTextArea textarea {
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.78rem !important;
    background-color: #fffef5 !important;
    border: 1px inset #7a92aa !important;
    color: #1a2a3a !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background-color: #fffef5 !important;
    border: 1px inset #7a92aa !important;
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.78rem !important;
}

/* ── Checkboxes ── */
.stCheckbox label {
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.78rem !important;
    color: #1a2a3a !important;
}

/* ── Dividers ── */
hr {
    border: none !important;
    border-top: 2px inset #7a92aa !important;
    margin: 10px 0 !important;
}

/* ── Primary button (Generate PDF) ── */
.stButton > button[kind="primary"] {
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: bold !important;
    background: linear-gradient(180deg, #5588bb 0%, #2a5298 100%) !important;
    color: #ffffff !important;
    border: 2px outset #7aaad4 !important;
    border-radius: 2px !important;
    padding: 6px 18px !important;
    text-shadow: 1px 1px 1px #001a33;
    letter-spacing: 0.03em;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, #6699cc 0%, #3a62a8 100%) !important;
    border: 2px inset #7aaad4 !important;
}
.stButton > button[kind="primary"]:active {
    border: 2px inset #4a6a94 !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.78rem !important;
    background: linear-gradient(180deg, #e8f0e8 0%, #c8d8c8 100%) !important;
    color: #1a3a1a !important;
    border: 2px outset #88aa88 !important;
    border-radius: 2px !important;
}

/* ── Bold markdown labels (CEQA, NEPA, Other) ── */
strong {
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.8rem !important;
    color: #003366 !important;
}

/* ── Success / error messages ── */
.stSuccess, .stAlert {
    font-family: Verdana, Tahoma, sans-serif !important;
    font-size: 0.78rem !important;
    border: 1px solid #5588bb !important;
    border-radius: 0px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Notice of Completion & Environmental Document Transmittal")
st.caption("California Energy Commission — ADA-Compliant Form Generator")
st.divider()

# ── SECTION: Overview ─────────────────────────────────────────────────────────

st.subheader("Overview")

project_title = st.selectbox("Project Title", options=[""] + PROJECT_TITLES, key="project_title")
preset = apply_preset_to_session(project_title)

preset_contact = preset_val(preset, "contact_name")
contact_options = [""] + list(CONTACTS.keys())
contact_index = contact_options.index(preset_contact) if preset_contact in contact_options else 0
contact_name = st.selectbox("Contact Person", options=contact_options, index=contact_index, key="contact_name")

phone_number = st.text_input(
    "Phone",
    value=preset_val(preset, "phone"),
    key="phone",
    help="Imported from the selected project in the ODS"
)

preset_sch = preset_val(preset, "sch_number")
sch_number = st.text_input("SCH Number", value=preset_val(preset, "sch_number"), placeholder="e.g. 2024010001", key="sch_number")

st.divider()

# ── SECTION: Project Location ─────────────────────────────────────────────────

st.subheader("Project Location")

col1, col2 = st.columns(2)
with col1:
    project_county = st.text_input("County", placeholder="e.g. Kern", key="project_county")
    cross_streets = st.text_input("Cross Streets", placeholder="e.g. Hwy 58 & Wind Farm Rd", value=preset_val(preset, "cross_streets"), key="cross_streets")
    latitude = st.text_input("Latitude", placeholder="e.g. 35° 21' 14\" N", value=preset_val(preset, "latitude"), key="latitude")
with col2:
    project_city = st.text_input("City / Nearest Community", placeholder="e.g. Mojave", key="project_city")
    project_zip = st.text_input("ZIP Code", placeholder="e.g. 93501", key="project_zip")
    longitude = st.text_input("Longitude", placeholder="e.g. 118° 09' 22\" W", value=preset_val(preset, "longitude"), key="longitude")

total_acres = st.text_input("Total Acres", placeholder="e.g. 4,200", value=preset_val(preset, "total_acres"), key="total_acres")

col1, col2, col3, col4 = st.columns(4)
with col1:
    assessor_parcel = st.text_input("Assessor Parcel No.", placeholder="e.g. 0141-030-090", value=preset_val(preset, "assessor_parcel"), key="assessor_parcel")
with col2:
    section = st.text_input("Section", placeholder="e.g. 1", value=preset_val(preset, "section"), key="section")
with col3:
    township = st.text_input("Township", placeholder="e.g. 6N", value=preset_val(preset, "township"), key="township")
with col4:
    range_ = st.text_input("Range", placeholder="e.g. 1W", value=preset_val(preset, "range_"), key="range_")

col1, col2 = st.columns(2)
with col1:
    state_highways = st.text_input("State Highways (within 2 miles)", placeholder="e.g. I-505, I-80", value=preset_val(preset, "state_highways"), key="state_highways")
    railways = st.text_input("Railways", placeholder="e.g. Union Pacific", value=preset_val(preset, "railways"), key="railways")
with col2:
    airports = st.text_input("Airports", placeholder="e.g. Nut Tree Airport", value=preset_val(preset, "airports"), key="airports")
    schools = st.text_input("Schools", placeholder="e.g. Blake Austin College", value=preset_val(preset, "schools"), key="schools")

st.divider()

# ── SECTION: Document Type ────────────────────────────────────────────────────

st.subheader("Document Type")

# -- CEQA (always expanded) ---------------------------------------------------
st.markdown("**CEQA**")

col1, col2, col3 = st.columns(3)
with col1:
    ceqa_nop = st.checkbox("NOP", value=preset_bool(preset, "ceqa_nop", False), key="ceqa_nop")
    ceqa_neg_dec = st.checkbox("Neg Dec", value=preset_bool(preset, "ceqa_neg_dec", False), key="ceqa_neg_dec")
    ceqa_draft_eir = st.checkbox("Draft EIR", value=preset_bool(preset, "ceqa_draft_eir", False), key="ceqa_draft_eir")
with col2:
    ceqa_early_cons = st.checkbox("Early Cons", value=preset_bool(preset, "ceqa_early_cons", False), key="ceqa_early_cons")
    ceqa_mit_neg = st.checkbox("Mit Neg Dec", value=preset_bool(preset, "ceqa_mit_neg", False), key="ceqa_mit_neg")
    ceqa_sub_eir = st.checkbox("Supplement/Subsequent EIR", value=preset_bool(preset, "ceqa_sub_eir", False), key="ceqa_sub_eir")
with col3:
    ceqa_other_check = st.checkbox("Other (CEQA)", value=preset_bool(preset, "ceqa_other_check", False), key="ceqa_other_check")

# Supplement/Subsequent EIR → prompt for Prior SCH No.
ceqa_prior_sch = ""
if ceqa_sub_eir:
    ceqa_prior_sch = st.text_input("Prior SCH No. (required for Supplement/Subsequent EIR)",
                                   placeholder="e.g. 2019010001")

# CEQA Other free-text
ceqa_other_text = ""
if ceqa_other_check:
    ceqa_other_text = st.text_input("CEQA — Other (please specify)", placeholder="Describe other CEQA document type", value=preset_val(preset, "ceqa_other_text"), key="ceqa_other_text")

# -- NEPA (collapsed behind a checkbox) ---------------------------------------
st.markdown("**NEPA**")
nepa_section = st.checkbox("NEPA document included", value=preset_bool(preset, "nepa_section", False), key="nepa_section")

nepa_noi = nepa_ea = nepa_eis = nepa_fonsi = False
if nepa_section:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        nepa_noi = st.checkbox("NOI", value=preset_bool(preset, "nepa_noi", False), key="nepa_noi")
    with col2:
        nepa_ea = st.checkbox("EA", value=preset_bool(preset, "nepa_ea", False), key="nepa_ea")
    with col3:
        nepa_eis = st.checkbox("Draft EIS", value=preset_bool(preset, "nepa_eis", False), key="nepa_eis")
    with col4:
        nepa_fonsi = st.checkbox("FONSI", value=preset_bool(preset, "nepa_fonsi", False), key="nepa_fonsi")

# -- Other document type (collapsed behind a checkbox) ------------------------
st.markdown("**Other**")
other_section = st.checkbox("Other document type included", value=preset_bool(preset, "other_section", False), key="other_section")

other_joint = other_final = other_custom_check = False
other_custom_text = ""
if other_section:
    col1, col2, col3 = st.columns(3)
    with col1:
        other_joint = st.checkbox("Joint Document", value=preset_bool(preset, "other_joint", False), key="other_joint")
    with col2:
        other_final = st.checkbox("Final Document", value=preset_bool(preset, "other_final", False), key="other_final")
    with col3:
        other_custom_check = st.checkbox("Other", value=preset_bool(preset, "other_custom_check", False), key="other_custom_check")
    if other_custom_check:
        other_custom_text = st.text_input("Other document type (please specify)", placeholder="Describe document type", value=preset_val(preset, "other_custom_text"), key="other_custom_text")

st.divider()

# ── SECTION: Local Action Type ────────────────────────────────────────────────

st.subheader("Local Action Type")

col1, col2, col3 = st.columns(3)
with col1:
    lat_gpu = st.checkbox("General Plan Update", value=preset_bool(preset, "lat_gpu", False), key="lat_gpu")
    lat_gpa = st.checkbox("General Plan Amendment", value=preset_bool(preset, "lat_gpa", False), key="lat_gpa")
    lat_gpe = st.checkbox("General Plan Element", value=preset_bool(preset, "lat_gpe", False), key="lat_gpe")
    lat_cp = st.checkbox("Community Plan", value=preset_bool(preset, "lat_cp", False), key="lat_cp")
    lat_sp = st.checkbox("Specific Plan", value=preset_bool(preset, "lat_sp", False), key="lat_sp")
with col2:
    lat_mp = st.checkbox("Master Plan", value=preset_bool(preset, "lat_mp", False), key="lat_mp")
    lat_pud = st.checkbox("Planned Unit Development", value=preset_bool(preset, "lat_pud", False), key="lat_pud")
    lat_rezone = st.checkbox("Rezone", value=preset_bool(preset, "lat_rezone", False), key="lat_rezone")
    lat_prezone = st.checkbox("Prezone", value=preset_bool(preset, "lat_prezone", False), key="lat_prezone")
    lat_annex = st.checkbox("Annexation", value=preset_bool(preset, "lat_annex", False), key="lat_annex")
with col3:
    lat_redevel = st.checkbox("Redevelopment", value=preset_bool(preset, "lat_redevel", False), key="lat_redevel")
    lat_use = st.checkbox("Use Permit", value=preset_bool(preset, "lat_use", False), key="lat_use")
    lat_coastal = st.checkbox("Coastal Permit", value=preset_bool(preset, "lat_coastal", False), key="lat_coastal")
    lat_site = st.checkbox("Site Plan", value=preset_bool(preset, "lat_site", False), key="lat_site")
    lat_land_div = st.checkbox("Land Division (Subdivision, etc.)", value=preset_bool(preset, "lat_land_div", False), key="lat_land_div")
    lat_other_check = st.checkbox("Other (Local Action)", value=preset_bool(preset, "lat_other_check", False), key="lat_other_check")

lat_other_text = ""
if lat_other_check:
    lat_other_text = st.text_input("Local Action Type — Other (please specify)", placeholder="Describe other local action type", value=preset_val(preset, "lat_other_text"), key="lat_other_text")

st.divider()

# ── SECTION: Development Type ─────────────────────────────────────────────────

st.subheader("Development Type")

# ── Power ──
dev_power = st.checkbox("Power", value=preset_bool(preset, "dev_power", True), key="dev_power")
dev_power_wind = dev_power_solar = dev_power_bess = dev_power_other = False
dev_power_other_text = ""
dev_power_wind_mw = dev_power_solar_mw = dev_power_bess_mw = dev_power_other_mw = ""
if dev_power:
    with st.container():
        st.markdown("<div style='margin-left:20px'>", unsafe_allow_html=True)
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            dev_power_wind = st.checkbox("Wind", value=preset_bool(preset, "dev_power_wind", False), key="dev_power_wind")
            if dev_power_wind:
                dev_power_wind_mw = st.text_input("Wind — MW", placeholder="e.g. 150", value=preset_val(preset, "dev_power_wind_mw"), key="dev_power_wind_mw")
        with pc2:
            dev_power_solar = st.checkbox("Solar Photovoltaic", value=preset_bool(preset, "dev_power_solar", False), key="dev_power_solar")
            if dev_power_solar:
                dev_power_solar_mw = st.text_input("Solar — MW", placeholder="e.g. 200", value=preset_val(preset, "dev_power_solar_mw"), key="dev_power_solar_mw")
        with pc3:
            dev_power_bess = st.checkbox("Battery Energy Storage System", value=preset_bool(preset, "dev_power_bess", False), key="dev_power_bess")
            if dev_power_bess:
                dev_power_bess_mw = st.text_input("BESS — MW", placeholder="e.g. 100", value=preset_val(preset, "dev_power_bess_mw"), key="dev_power_bess_mw")
        with pc4:
            dev_power_other = st.checkbox("Other (Power)", value=preset_bool(preset, "dev_power_other", False), key="dev_power_other")
            if dev_power_other:
                dev_power_other_text = st.text_input("Other — Type", placeholder="e.g. Geothermal", value=preset_val(preset, "dev_power_other_text"), key="dev_power_other_text")
                dev_power_other_mw = st.text_input("Other — MW", placeholder="e.g. 50", value=preset_val(preset, "dev_power_other_mw"), key="dev_power_other_mw")
        st.markdown("</div>", unsafe_allow_html=True)

# ── Non-Power ──
dev_nonpower = st.checkbox("Non-Power", value=preset_bool(preset, "dev_nonpower", False), key="dev_nonpower")

# Initialize all non-power fields
dev_residential = dev_office = dev_commercial = dev_industrial = False
dev_educational = dev_recreational = dev_water = dev_transportation = False
dev_mining = dev_waste = dev_hazardous = dev_other = False
dev_residential_units = dev_residential_acres = ""
dev_office_sqft = dev_office_acres = dev_office_emp = ""
dev_commercial_sqft = dev_commercial_acres = dev_commercial_emp = ""
dev_industrial_sqft = dev_industrial_acres = dev_industrial_emp = ""
dev_educational_text = dev_recreational_text = ""
dev_water_type = dev_water_mgd = ""
dev_transportation_type = ""
dev_mining_mineral = ""
dev_waste_type = dev_waste_mgd = ""
dev_hazardous_type = ""
dev_other_text = ""

if dev_nonpower:
    with st.container():
        st.markdown("<div style='margin-left:20px'>", unsafe_allow_html=True)

        dev_residential = st.checkbox("Residential", value=preset_bool(preset, "dev_residential", False), key="dev_residential")
        if dev_residential:
            rc1, rc2 = st.columns(2)
            with rc1:
                dev_residential_units = st.text_input("Residential — Units", placeholder="e.g. 250", value=preset_val(preset, "dev_residential_units"), key="dev_residential_units")
            with rc2:
                dev_residential_acres = st.text_input("Residential — Acres", placeholder="e.g. 12.5", value=preset_val(preset, "dev_residential_acres"), key="dev_residential_acres")

        dev_office = st.checkbox("Office", value=preset_bool(preset, "dev_office", False), key="dev_office")
        if dev_office:
            oc1, oc2, oc3 = st.columns(3)
            with oc1:
                dev_office_sqft = st.text_input("Office — Sq. Ft.", placeholder="e.g. 45,000", value=preset_val(preset, "dev_office_sqft"), key="dev_office_sqft")
            with oc2:
                dev_office_acres = st.text_input("Office — Acres", placeholder="e.g. 3.2", value=preset_val(preset, "dev_office_acres"), key="dev_office_acres")
            with oc3:
                dev_office_emp = st.text_input("Office — Employees", placeholder="e.g. 180", value=preset_val(preset, "dev_office_emp"), key="dev_office_emp")

        dev_commercial = st.checkbox("Commercial", value=preset_bool(preset, "dev_commercial", False), key="dev_commercial")
        if dev_commercial:
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                dev_commercial_sqft = st.text_input("Commercial — Sq. Ft.", placeholder="e.g. 20,000", value=preset_val(preset, "dev_commercial_sqft"), key="dev_commercial_sqft")
            with cc2:
                dev_commercial_acres = st.text_input("Commercial — Acres", placeholder="e.g. 2.0", value=preset_val(preset, "dev_commercial_acres"), key="dev_commercial_acres")
            with cc3:
                dev_commercial_emp = st.text_input("Commercial — Employees", placeholder="e.g. 75", value=preset_val(preset, "dev_commercial_emp"), key="dev_commercial_emp")

        dev_industrial = st.checkbox("Industrial", value=preset_bool(preset, "dev_industrial", False), key="dev_industrial")
        if dev_industrial:
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                dev_industrial_sqft = st.text_input("Industrial — Sq. Ft.", placeholder="e.g. 100,000", value=preset_val(preset, "dev_industrial_sqft"), key="dev_industrial_sqft")
            with ic2:
                dev_industrial_acres = st.text_input("Industrial — Acres", placeholder="e.g. 8.0", value=preset_val(preset, "dev_industrial_acres"), key="dev_industrial_acres")
            with ic3:
                dev_industrial_emp = st.text_input("Industrial — Employees", placeholder="e.g. 50", value=preset_val(preset, "dev_industrial_emp"), key="dev_industrial_emp")

        dev_educational = st.checkbox("Educational", value=preset_bool(preset, "dev_educational", False), key="dev_educational")
        if dev_educational:
            dev_educational_text = st.text_input("Educational — Details", placeholder="e.g. K-12 school, 800 students", value=preset_val(preset, "dev_educational_text"), key="dev_educational_text")

        dev_recreational = st.checkbox("Recreational", value=preset_bool(preset, "dev_recreational", False), key="dev_recreational")
        if dev_recreational:
            dev_recreational_text = st.text_input("Recreational — Details", placeholder="e.g. Regional park, sports fields", value=preset_val(preset, "dev_recreational_text"), key="dev_recreational_text")

        dev_water = st.checkbox("Water Facilities", value=preset_bool(preset, "dev_water", False), key="dev_water")
        if dev_water:
            wc1, wc2 = st.columns(2)
            with wc1:
                dev_water_type = st.text_input("Water Facilities — Type", placeholder="e.g. Reservoir, Treatment Plant", value=preset_val(preset, "dev_water_type"), key="dev_water_type")
            with wc2:
                dev_water_mgd = st.text_input("Water Facilities — MGD", placeholder="e.g. 5.2", value=preset_val(preset, "dev_water_mgd"), key="dev_water_mgd")

        dev_transportation = st.checkbox("Transportation", value=preset_bool(preset, "dev_transportation", False), key="dev_transportation")
        if dev_transportation:
            dev_transportation_type = st.text_input("Transportation — Type", placeholder="e.g. Highway, Rail, Airport", value=preset_val(preset, "dev_transportation_type"), key="dev_transportation_type")

        dev_mining = st.checkbox("Mining", value=preset_bool(preset, "dev_mining", False), key="dev_mining")
        if dev_mining:
            dev_mining_mineral = st.text_input("Mining — Mineral", placeholder="e.g. Silica, Gravel", value=preset_val(preset, "dev_mining_mineral"), key="dev_mining_mineral")

        dev_waste = st.checkbox("Waste Treatment", value=preset_bool(preset, "dev_waste", False), key="dev_waste")
        if dev_waste:
            wt1, wt2 = st.columns(2)
            with wt1:
                dev_waste_type = st.text_input("Waste Treatment — Type", placeholder="e.g. Wastewater, Solid Waste", value=preset_val(preset, "dev_waste_type"), key="dev_waste_type")
            with wt2:
                dev_waste_mgd = st.text_input("Waste Treatment — MGD", placeholder="e.g. 2.0", value=preset_val(preset, "dev_waste_mgd"), key="dev_waste_mgd")

        dev_hazardous = st.checkbox("Hazardous Waste", value=preset_bool(preset, "dev_hazardous", False), key="dev_hazardous")
        if dev_hazardous:
            dev_hazardous_type = st.text_input("Hazardous Waste — Type", placeholder="e.g. Medical, Chemical", value=preset_val(preset, "dev_hazardous_type"), key="dev_hazardous_type")

        dev_other = st.checkbox("Other (Non-Power)", value=preset_bool(preset, "dev_other", False), key="dev_other")
        if dev_other:
            dev_other_text = st.text_input("Other — Details", placeholder="Describe other development type", value=preset_val(preset, "dev_other_text"), key="dev_other_text")

        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── SECTION: Project Issues ───────────────────────────────────────────────────
st.subheader("Project Issues Discussed in Document")

c1, c2, c3, c4 = st.columns(4)
with c1:
    issue_aesthetic_visual = st.checkbox("Aesthetic/Visual", value=preset_bool(preset, "issue_aesthetic_visual", True), key="issue_aesthetic_visual")
    issue_agricultural_land = st.checkbox("Agricultural Land", value=preset_bool(preset, "issue_agricultural_land", True), key="issue_agricultural_land")
    issue_air_quality = st.checkbox("Air Quality", value=preset_bool(preset, "issue_air_quality", True), key="issue_air_quality")
    issue_archeological_historical = st.checkbox("Archeological/Historical", value=preset_bool(preset, "issue_archeological_historical", True), key="issue_archeological_historical")
    issue_biological_resources = st.checkbox("Biological Resources", value=preset_bool(preset, "issue_biological_resources", True), key="issue_biological_resources")
    issue_coastal_zone = st.checkbox("Coastal Zone", value=preset_bool(preset, "issue_coastal_zone", False), key="issue_coastal_zone")
    issue_cumulative_effects = st.checkbox("Cumulative Effects", value=preset_bool(preset, "issue_cumulative_effects", True), key="issue_cumulative_effects")
    issue_drainage_absorption = st.checkbox("Drainage/Absorption", value=preset_bool(preset, "issue_drainage_absorption", True), key="issue_drainage_absorption")
    issue_economic_jobs = st.checkbox("Economic/Jobs", value=preset_bool(preset, "issue_economic_jobs", True), key="issue_economic_jobs")
with c2:
    issue_energy = st.checkbox("Energy", value=preset_bool(preset, "issue_energy", True), key="issue_energy")
    issue_fiscal = st.checkbox("Fiscal", value=preset_bool(preset, "issue_fiscal", False), key="issue_fiscal")
    issue_flood_plain_flooding = st.checkbox("Flood Plain/Flooding", value=preset_bool(preset, "issue_flood_plain_flooding", True), key="issue_flood_plain_flooding")
    issue_forest_land_fire_hazard = st.checkbox("Forest Land/Fire Hazard", value=preset_bool(preset, "issue_forest_land_fire_hazard", True), key="issue_forest_land_fire_hazard")
    issue_geologic_seismic = st.checkbox("Geologic/Seismic", value=preset_bool(preset, "issue_geologic_seismic", True), key="issue_geologic_seismic")
    issue_greenhouse_gas_emissions = st.checkbox("Greenhouse Gas Emissions", value=preset_bool(preset, "issue_greenhouse_gas_emissions", True), key="issue_greenhouse_gas_emissions")
    issue_growth_inducement = st.checkbox("Growth Inducement", value=preset_bool(preset, "issue_growth_inducement", False), key="issue_growth_inducement")
    issue_land_use = st.checkbox("Land Use", value=preset_bool(preset, "issue_land_use", True), key="issue_land_use")
    issue_minerals = st.checkbox("Minerals", value=preset_bool(preset, "issue_minerals", True), key="issue_minerals")
with c3:
    issue_noise = st.checkbox("Noise", value=preset_bool(preset, "issue_noise", True), key="issue_noise")
    issue_other = st.checkbox("Other", value=preset_bool(preset, "issue_other", False), key="issue_other")
    issue_population_housing_balance = st.checkbox("Population/Housing Balance", value=preset_bool(preset, "issue_population_housing_balance", True), key="issue_population_housing_balance")
    issue_public_services_facilities = st.checkbox("Public Services/Facilities", value=preset_bool(preset, "issue_public_services_facilities", True), key="issue_public_services_facilities")
    issue_recreation_parks = st.checkbox("Recreation/Parks", value=preset_bool(preset, "issue_recreation_parks", True), key="issue_recreation_parks")
    issue_schools_universities = st.checkbox("Schools/Universities", value=preset_bool(preset, "issue_schools_universities", False), key="issue_schools_universities")
    issue_septic_systems = st.checkbox("Septic Systems", value=preset_bool(preset, "issue_septic_systems", False), key="issue_septic_systems")
    issue_sewer_capacity = st.checkbox("Sewer Capacity", value=preset_bool(preset, "issue_sewer_capacity", False), key="issue_sewer_capacity")
    issue_soil_erosion_compaction_grading = st.checkbox("Soil Erosion/Compaction/Grading", value=preset_bool(preset, "issue_soil_erosion_compaction_grading", True), key="issue_soil_erosion_compaction_grading")
with c4:
    issue_solid_waste = st.checkbox("Solid Waste", value=preset_bool(preset, "issue_solid_waste", True), key="issue_solid_waste")
    issue_toxic_hazardous = st.checkbox("Toxic/Hazardous", value=preset_bool(preset, "issue_toxic_hazardous", True), key="issue_toxic_hazardous")
    issue_traffic_circulation = st.checkbox("Traffic/Circulation", value=preset_bool(preset, "issue_traffic_circulation", True), key="issue_traffic_circulation")
    issue_tribal_cultural_resources = st.checkbox("Tribal Cultural Resources", value=preset_bool(preset, "issue_tribal_cultural_resources", True), key="issue_tribal_cultural_resources")
    issue_vegetation = st.checkbox("Vegetation", value=preset_bool(preset, "issue_vegetation", False), key="issue_vegetation")
    issue_water_quality = st.checkbox("Water Quality", value=preset_bool(preset, "issue_water_quality", True), key="issue_water_quality")
    issue_water_supply_groundwater = st.checkbox("Water Supply/Groundwater", value=preset_bool(preset, "issue_water_supply_groundwater", True), key="issue_water_supply_groundwater")
    issue_wetland_riparian = st.checkbox("Wetland/Riparian", value=preset_bool(preset, "issue_wetland_riparian", True), key="issue_wetland_riparian")

issue_other_text = ""
if issue_other:
    issue_other_text = st.text_input("Other Issue (specify)", placeholder="Describe other issue", value=preset_val(preset, "issue_other_text"), key="issue_other_text")


st.divider()

# ── SECTION: Land Use & Description ──────────────────────────────────────────

st.subheader("Present Land Use / Zoning / GP Designation")
land_use = st.text_area("Land Use Description",
                        placeholder="e.g. Rural/Agricultural, Zoned A-1, GP designation Open Space",
                        value=preset_val(preset, "land_use"),
                        height=80,
                        key="land_use")

st.subheader("Project Description")
project_description = st.text_area("Project Description",
                                   placeholder="Describe the project in full here...",
                                   value=preset_val(preset, "project_description"),
                                   height=150,
                                   key="project_description")

st.divider()

# ── SECTION: Reviewing Agencies Checklist ────────────────────────────────────

st.subheader("Reviewing Agencies Checklist")

col_l, col_r = st.columns(2)

with col_l:
    ra_air = st.checkbox("Air Resources Board", value=preset_bool(preset, "ra_air", True), key="ra_air")
    ra_boating = st.checkbox("Boating & Waterways, Department of", value=preset_bool(preset, "ra_boating", False), key="ra_boating")
    ra_cal_ema = st.checkbox("California Emergency Management Agency", value=preset_bool(preset, "ra_cal_ema", True), key="ra_cal_ema")
    ra_chp = st.checkbox("California Highway Patrol", value=preset_bool(preset, "ra_chp", True), key="ra_chp")
    ra_caltrans_dist = st.checkbox("Caltrans District #n", value=preset_bool(preset, "ra_caltrans_dist", True), key="ra_caltrans_dist")
    ra_caltrans_dist_n = ""
    if ra_caltrans_dist:
        ra_caltrans_dist_n = st.text_input("Caltrans District Number :red[*]", placeholder="e.g. 7", value=preset_val(preset, "ra_caltrans_dist_n"), key="ra_caltrans_dist_n")
    ra_caltrans_aero = st.checkbox("Caltrans Division of Aeronautics", value=preset_bool(preset, "ra_caltrans_aero", False), key="ra_caltrans_aero")
    ra_caltrans_plan = st.checkbox("Caltrans Planning", value=preset_bool(preset, "ra_caltrans_plan", True), key="ra_caltrans_plan")
    ra_cvfpb = st.checkbox("Central Valley Flood Protection Board", value=preset_bool(preset, "ra_cvfpb", False), key="ra_cvfpb")
    ra_coachella = st.checkbox("Coachella Valley Mtns. Conservancy", value=preset_bool(preset, "ra_coachella", False), key="ra_coachella")
    ra_coastal = st.checkbox("Coastal Commission", value=preset_bool(preset, "ra_coastal", False), key="ra_coastal")
    ra_colorado = st.checkbox("Colorado River Board", value=preset_bool(preset, "ra_colorado", False), key="ra_colorado")
    ra_conservation = st.checkbox("Conservation, Department of", value=preset_bool(preset, "ra_conservation", True), key="ra_conservation")
    ra_corrections = st.checkbox("Corrections, Department of", value=preset_bool(preset, "ra_corrections", False), key="ra_corrections")
    ra_delta = st.checkbox("Delta Protection Commission", value=preset_bool(preset, "ra_delta", False), key="ra_delta")
    ra_education = st.checkbox("Education, Department of", value=preset_bool(preset, "ra_education", False), key="ra_education")
    ra_energy = st.checkbox("Energy Commission", value=preset_bool(preset, "ra_energy", True), key="ra_energy")
    ra_fish = st.checkbox("Fish & Game Region #n", value=preset_bool(preset, "ra_fish", True), key="ra_fish")
    ra_fish_n = ""
    if ra_fish:
        ra_fish_n = st.text_input("Fish & Game Region Number :red[*]", placeholder="e.g. 4", value=preset_val(preset, "ra_fish_n"), key="ra_fish_n")
    ra_food = st.checkbox("Food & Agriculture, Department of", value=preset_bool(preset, "ra_food", False), key="ra_food")
    ra_forestry = st.checkbox("Forestry and Fire Protection, Department of", value=preset_bool(preset, "ra_forestry", True), key="ra_forestry")
    ra_general_svc = st.checkbox("General Services, Department of", value=preset_bool(preset, "ra_general_svc", False), key="ra_general_svc")
    ra_health = st.checkbox("Health Services, Department of", value=preset_bool(preset, "ra_health", False), key="ra_health")
    ra_housing = st.checkbox("Housing & Community Development", value=preset_bool(preset, "ra_housing", False), key="ra_housing")
    ra_nahc = st.checkbox("Native American Heritage Commission", value=preset_bool(preset, "ra_nahc", True), key="ra_nahc")

with col_r:
    ra_ohp = st.checkbox("Office of Historic Preservation", value=preset_bool(preset, "ra_ohp", True), key="ra_ohp")
    ra_opsc = st.checkbox("Office of Public School Construction", value=preset_bool(preset, "ra_opsc", False), key="ra_opsc")
    ra_parks = st.checkbox("Parks & Recreation, Department of", value=preset_bool(preset, "ra_parks", False), key="ra_parks")
    ra_pesticide = st.checkbox("Pesticide Regulation, Department of", value=preset_bool(preset, "ra_pesticide", False), key="ra_pesticide")
    ra_puc = st.checkbox("Public Utilities Commission", value=preset_bool(preset, "ra_puc", True), key="ra_puc")
    ra_wqcb = st.checkbox("Regional WQCB #n", value=preset_bool(preset, "ra_wqcb", True), key="ra_wqcb")
    ra_wqcb_n = ""
    if ra_wqcb:
        ra_wqcb_n = st.text_input("Regional WQCB Number :red[*]", placeholder="e.g. 5", value=preset_val(preset, "ra_wqcb_n"), key="ra_wqcb_n")
    ra_resources = st.checkbox("Resources Agency", value=preset_bool(preset, "ra_resources", True), key="ra_resources")
    ra_recycling = st.checkbox("Resources Recycling and Recovery, Department of", value=preset_bool(preset, "ra_recycling", False), key="ra_recycling")
    ra_sfbay = st.checkbox("S.F. Bay Conservation & Development Comm.", value=preset_bool(preset, "ra_sfbay", False), key="ra_sfbay")
    ra_san_gabriel = st.checkbox("San Gabriel & Lower L.A. Rivers & Mtns. Conservancy", value=preset_bool(preset, "ra_san_gabriel", False), key="ra_san_gabriel")
    ra_san_joaquin = st.checkbox("San Joaquin River Conservancy", value=preset_bool(preset, "ra_san_joaquin", False), key="ra_san_joaquin")
    ra_santa_monica = st.checkbox("Santa Monica Mtns. Conservancy", value=preset_bool(preset, "ra_santa_monica", False), key="ra_santa_monica")
    ra_state_lands = st.checkbox("State Lands Commission", value=preset_bool(preset, "ra_state_lands", False), key="ra_state_lands")
    ra_swrcb_cwg = st.checkbox("SWRCB: Clean Water Grants", value=preset_bool(preset, "ra_swrcb_cwg", False), key="ra_swrcb_cwg")
    ra_swrcb_wq = st.checkbox("SWRCB: Water Quality", value=preset_bool(preset, "ra_swrcb_wq", True), key="ra_swrcb_wq")
    ra_swrcb_wr = st.checkbox("SWRCB: Water Rights", value=preset_bool(preset, "ra_swrcb_wr", True), key="ra_swrcb_wr")
    ra_tahoe = st.checkbox("Tahoe Regional Planning Agency", value=preset_bool(preset, "ra_tahoe", False), key="ra_tahoe")
    ra_toxic = st.checkbox("Toxic Substances Control, Department of", value=preset_bool(preset, "ra_toxic", True), key="ra_toxic")
    ra_water_res = st.checkbox("Water Resources, Department of", value=preset_bool(preset, "ra_water_res", True), key="ra_water_res")
    ra_other_1 = st.text_input("Other Agency 1", placeholder="e.g. County Planning Department", value=preset_val(preset, "ra_other_1"), key="ra_other_1")
    ra_other_2 = st.text_input("Other Agency 2", placeholder="e.g. Local Air District", value=preset_val(preset, "ra_other_2"), key="ra_other_2")

st.divider()

# ── SECTION: Local Public Review Period ───────────────────────────────────────

st.subheader("Local Public Review Period")

from datetime import date, timedelta, datetime

def next_business_day(d):
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d

def set_today():
    import zoneinfo
    today_pt = datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).date()
    st.session_state.date_start = today_pt

def set_plus_30():
    start = st.session_state.get("date_start")
    if start:
        raw_end = start + timedelta(days=30)
        st.session_state.date_end = next_business_day(raw_end)

if "date_start" not in st.session_state:
    st.session_state.date_start = None
if "date_end" not in st.session_state:
    st.session_state.date_end = None

col_start, col_end = st.columns(2)

with col_start:
    st.markdown("**Starting Date**")
    st.button("Today", key="btn_today", on_click=set_today)
    review_start = st.date_input(
        "Starting Date",
        value=st.session_state.date_start,
        label_visibility="collapsed",
        key="date_start",
    )

with col_end:
    st.markdown("**Ending Date**")
    st.button("+30 Days", key="btn_30", on_click=set_plus_30)
    review_end = st.date_input(
        "Ending Date",
        value=st.session_state.date_end,
        label_visibility="collapsed",
        key="date_end",
    )

st.divider()

# ── SECTION: Lead Agency ──────────────────────────────────────────────────────

st.subheader("Lead Agency")

st.markdown("**Consulting Firm**")
la_firm_name = st.text_input("Consulting Firm", placeholder="e.g. SWCA Environmental Consultants", label_visibility="collapsed", value=preset_val(preset, "la_firm_name"), key="la_firm_name")
la_firm_address = st.text_input("Address", placeholder="e.g. 1420 Harbor Bay Pkwy", value=preset_val(preset, "la_firm_address"), key="la_firm_address")
la_firm_csz = st.text_input("City / State / ZIP", placeholder="e.g. Alameda, CA 94502", value=preset_val(preset, "la_firm_csz"), key="la_firm_csz")
la_firm_contact = st.text_input("Contact", placeholder="e.g. Jane Smith", value=preset_val(preset, "la_firm_contact"), key="la_firm_contact")
la_firm_phone = st.text_input("Phone", placeholder="e.g. 510-555-0100", value=preset_val(preset, "la_firm_phone"), key="la_firm_phone")

st.markdown("**Applicant**")
la_app_name = st.text_input("Applicant", placeholder="e.g. Pacific Solar LLC", label_visibility="collapsed", value=preset_val(preset, "la_app_name"), key="la_app_name")
la_app_address = st.text_input("Address", placeholder="e.g. 350 Market St", value=preset_val(preset, "la_app_address"), key="la_app_address")
la_app_csz = st.text_input("City / State / ZIP", placeholder="e.g. San Francisco, CA 94105", value=preset_val(preset, "la_app_csz"), key="la_app_csz")
la_app_phone = st.text_input("Phone", placeholder="e.g. 415-555-0200", value=preset_val(preset, "la_app_phone"), key="la_app_phone")

st.divider()

# ── SECTION: Signature ────────────────────────────────────────────────────────

st.subheader("Signature of Lead Agency Representative")
st.caption("A signature field will appear in the generated PDF for signing in Adobe Acrobat.")
sig_date = ""

st.divider()

# ── Helpers ───────────────────────────────────────────────────────────────────

def field(label, value):
    return value.strip() if value and value.strip() else f"[{label} not provided]"

def checked_list(options_dict):
    selected = [label for label, checked in options_dict.items() if checked]
    return ", ".join(selected) if selected else None

# ── PDF generation ────────────────────────────────────────────────────────────

def generate_pdf():
    buffer = io.BytesIO()

    PDF_TITLE = "Notice of Completion & Environmental Document Transmittal"

    styles = getSampleStyleSheet()

    # H1 — document title
    title_style = ParagraphStyle(
        "FormTitle",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=4,
        textColor=colors.HexColor("#003366"),
        outlineLevel=0,
    )
    # H2 — section headings (explicit PDF structure tag via bulletText trick)
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=14,
        spaceAfter=4,
        textColor=colors.HexColor("#003366"),
        outlineLevel=1,
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey, spaceAfter=1,
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=10, spaceAfter=6,
    )

    def add_field(story, label, value):
        story.append(Paragraph(label, label_style))
        story.append(Paragraph(value, value_style))

    def add_heading(story, text, level="h2"):
        """Add a heading — outlineLevel in the style handles bookmark structure."""
        style = title_style if level == "h1" else heading_style
        story.append(Paragraph(text, style))

    def add_checked(story, label, options_dict):
        result = checked_list(options_dict)
        if result:
            story.append(Paragraph(label, label_style))
            story.append(Paragraph(result, value_style))

    story = []

    # Header — H1 title block
    title_block = [
        Paragraph("California Energy Commission", label_style),
        Paragraph("Notice of Completion &amp; Environmental Document Transmittal", title_style),
    ]
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=0.85*inch, height=0.85*inch)
        header_table = Table([[title_block, logo]], colWidths=[5.5*inch, 1.0*inch])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",  (1, 0), (1, 0),   "RIGHT"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
    else:
        for p in title_block:
            story.append(p)

    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#003366")))
    story.append(Spacer(1, 8))

    add_field(story, "SCH Number", field("SCH Number", sch_number))

    # Overview
    add_heading(story, "Overview")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "Project Title",    field("Project Title", project_title))
    add_field(story, "Lead Agency",      "California Energy Commission")
    add_field(story, "Project Manager",  field("Contact Person", contact_name))
    add_field(story, "Mailing Address",  "715 P St, MS 40")
    add_field(story, "Phone",            field("Phone", phone_number))
    add_field(story, "City",             "Sacramento")
    add_field(story, "ZIP",              "95814")
    add_field(story, "County",           "Sacramento")

    # Project Location
    add_heading(story, "Project Location")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "County",                  field("County", project_county))
    add_field(story, "City / Nearest Community", field("City/Nearest Community", project_city))
    add_field(story, "Cross Streets",            field("Cross Streets", cross_streets))
    add_field(story, "ZIP Code",                 field("ZIP Code", project_zip))
    lat_long = (f"{latitude.strip()} / {longitude.strip()}"
                if latitude.strip() and longitude.strip()
                else "[Coordinates not provided]")
    add_field(story, "Longitude / Latitude", lat_long)
    add_field(story, "Total Acres",          field("Total Acres", total_acres))
    def val_or_na(v):
        return v.strip() if v and v.strip() else "N/A"

    add_field(story, "Assessor Parcel No.",  val_or_na(assessor_parcel))

    sec_str = f"Section: {val_or_na(section)}  |  Township: {val_or_na(township)}  |  Range: {val_or_na(range_)}"
    add_field(story, "Survey Info", sec_str)

    add_field(story, "State Highways (within 2 miles)", val_or_na(state_highways))
    add_field(story, "Airports",  val_or_na(airports))
    add_field(story, "Railways",  val_or_na(railways))
    add_field(story, "Schools",   val_or_na(schools))

    # Document Type
    ceqa_items = {
        "NOP":                      ceqa_nop,
        "Early Cons":               ceqa_early_cons,
        "Neg Dec":                  ceqa_neg_dec,
        "Mit Neg Dec":              ceqa_mit_neg,
        "Draft EIR":                ceqa_draft_eir,
        "Supplement/Subsequent EIR": ceqa_sub_eir,
    }
    if ceqa_other_check and ceqa_other_text.strip():
        ceqa_items[f"Other: {ceqa_other_text.strip()}"] = True

    nepa_items = {
        "NOI": nepa_noi, "EA": nepa_ea,
        "Draft EIS": nepa_eis, "FONSI": nepa_fonsi,
    }

    other_items = {"Joint Document": other_joint, "Final Document": other_final}
    if other_custom_check and other_custom_text.strip():
        other_items[f"Other: {other_custom_text.strip()}"] = True

    has_doc_type = (any(ceqa_items.values()) or
                    (nepa_section and any(nepa_items.values())) or
                    (other_section and any(other_items.values())))

    if has_doc_type:
        add_heading(story, "Document Type")
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))
        add_checked(story, "CEQA", ceqa_items)
        if ceqa_sub_eir and ceqa_prior_sch.strip():
            add_field(story, "Prior SCH No.", ceqa_prior_sch.strip())
        if nepa_section:
            add_checked(story, "NEPA", nepa_items)
        if other_section:
            add_checked(story, "Other", other_items)

    # Local Action Type
    lat_items = {
        "General Plan Update":              lat_gpu,
        "General Plan Amendment":           lat_gpa,
        "General Plan Element":             lat_gpe,
        "Community Plan":                   lat_cp,
        "Specific Plan":                    lat_sp,
        "Master Plan":                      lat_mp,
        "Planned Unit Development":         lat_pud,
        "Rezone":                           lat_rezone,
        "Prezone":                          lat_prezone,
        "Annexation":                       lat_annex,
        "Redevelopment":                    lat_redevel,
        "Use Permit":                       lat_use,
        "Coastal Permit":                   lat_coastal,
        "Site Plan":                        lat_site,
        "Land Division (Subdivision, etc.)": lat_land_div,
    }
    if lat_other_check and lat_other_text.strip():
        lat_items[f"Other: {lat_other_text.strip()}"] = True

    if any(lat_items.values()):
        add_heading(story, "Local Action Type")
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))
        add_checked(story, "Local Action Type", lat_items)

    # Development Type
    has_dev = (dev_power or dev_nonpower)
    if has_dev:
        add_heading(story, "Development Type")
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))

    if dev_power:
        def mw(val):
            return f" ({val.strip()} MW)" if val and val.strip() else ""
        power_lines = []
        if dev_power_wind:
            power_lines.append(f"Wind{mw(dev_power_wind_mw)}")
        if dev_power_solar:
            power_lines.append(f"Solar Photovoltaic{mw(dev_power_solar_mw)}")
        if dev_power_bess:
            power_lines.append(f"Battery Energy Storage System{mw(dev_power_bess_mw)}")
        if dev_power_other and dev_power_other_text.strip():
            power_lines.append(f"Other: {dev_power_other_text.strip()}{mw(dev_power_other_mw)}")
        add_field(story, "Power", ", ".join(power_lines) if power_lines else "—")

    if dev_nonpower:
        if dev_residential:
            add_field(story, "Residential",
                      f"Units: {dev_residential_units or '—'} | Acres: {dev_residential_acres or '—'}")
        if dev_office:
            add_field(story, "Office",
                      f"Sq. Ft.: {dev_office_sqft or '—'} | Acres: {dev_office_acres or '—'} | Employees: {dev_office_emp or '—'}")
        if dev_commercial:
            add_field(story, "Commercial",
                      f"Sq. Ft.: {dev_commercial_sqft or '—'} | Acres: {dev_commercial_acres or '—'} | Employees: {dev_commercial_emp or '—'}")
        if dev_industrial:
            add_field(story, "Industrial",
                      f"Sq. Ft.: {dev_industrial_sqft or '—'} | Acres: {dev_industrial_acres or '—'} | Employees: {dev_industrial_emp or '—'}")
        if dev_educational:
            add_field(story, "Educational", dev_educational_text or "—")
        if dev_recreational:
            add_field(story, "Recreational", dev_recreational_text or "—")
        if dev_water:
            add_field(story, "Water Facilities",
                      f"Type: {dev_water_type or '—'} | MGD: {dev_water_mgd or '—'}")
        if dev_transportation:
            add_field(story, "Transportation", f"Type: {dev_transportation_type or '—'}")
        if dev_mining:
            add_field(story, "Mining", f"Mineral: {dev_mining_mineral or '—'}")
        if dev_waste:
            add_field(story, "Waste Treatment",
                      f"Type: {dev_waste_type or '—'} | MGD: {dev_waste_mgd or '—'}")
        if dev_hazardous:
            add_field(story, "Hazardous Waste", f"Type: {dev_hazardous_type or '—'}")
        if dev_other and dev_other_text.strip():
            add_field(story, "Other", dev_other_text.strip())

    # Project Issues
    issues_checked = {
        "Aesthetic/Visual": issue_aesthetic_visual,
        "Agricultural Land": issue_agricultural_land,
        "Air Quality": issue_air_quality,
        "Archeological/Historical": issue_archeological_historical,
        "Biological Resources": issue_biological_resources,
        "Coastal Zone": issue_coastal_zone,
        "Cumulative Effects": issue_cumulative_effects,
        "Drainage/Absorption": issue_drainage_absorption,
        "Economic/Jobs": issue_economic_jobs,
        "Energy": issue_energy,
        "Fiscal": issue_fiscal,
        "Flood Plain/Flooding": issue_flood_plain_flooding,
        "Forest Land/Fire Hazard": issue_forest_land_fire_hazard,
        "Geologic/Seismic": issue_geologic_seismic,
        "Greenhouse Gas Emissions": issue_greenhouse_gas_emissions,
        "Growth Inducement": issue_growth_inducement,
        "Land Use": issue_land_use,
        "Minerals": issue_minerals,
        "Noise": issue_noise,
        "Population/Housing Balance": issue_population_housing_balance,
        "Public Services/Facilities": issue_public_services_facilities,
        "Recreation/Parks": issue_recreation_parks,
        "Schools/Universities": issue_schools_universities,
        "Septic Systems": issue_septic_systems,
        "Sewer Capacity": issue_sewer_capacity,
        "Soil Erosion/Compaction/Grading": issue_soil_erosion_compaction_grading,
        "Solid Waste": issue_solid_waste,
        "Toxic/Hazardous": issue_toxic_hazardous,
        "Traffic/Circulation": issue_traffic_circulation,
        "Tribal Cultural Resources": issue_tribal_cultural_resources,
        "Vegetation": issue_vegetation,
        "Water Quality": issue_water_quality,
        "Water Supply/Groundwater": issue_water_supply_groundwater,
        "Wetland/Riparian": issue_wetland_riparian,
    }
    if issue_other and issue_other_text.strip():
        issues_checked[f"Other: {issue_other_text.strip()}"] = True
    if any(issues_checked.values()):
        add_heading(story, "Project Issues Discussed in Document")
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))
        add_checked(story, "Issues", issues_checked)

    # Land Use & Description
    add_heading(story, "Present Land Use / Zoning / GP Designation")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "Land Use / Zoning / GP Designation", field("Land Use", land_use))

    add_heading(story, "Project Description")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "Description", field("Project Description", project_description))

    # Reviewing Agencies Checklist
    add_heading(story, "Reviewing Agencies Checklist")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))

    agency_map = {
        "Air Resources Board":                                    ra_air,
        "Boating & Waterways, Department of":                     ra_boating,
        "California Emergency Management Agency":                 ra_cal_ema,
        "California Highway Patrol":                              ra_chp,
        f"Caltrans District #{ra_caltrans_dist_n or 'n'}" if ra_caltrans_dist else "Caltrans District #n": ra_caltrans_dist,
        "Caltrans Division of Aeronautics":                       ra_caltrans_aero,
        "Caltrans Planning":                                      ra_caltrans_plan,
        "Central Valley Flood Protection Board":                  ra_cvfpb,
        "Coachella Valley Mtns. Conservancy":                     ra_coachella,
        "Coastal Commission":                                      ra_coastal,
        "Colorado River Board":                                   ra_colorado,
        "Conservation, Department of":                            ra_conservation,
        "Corrections, Department of":                             ra_corrections,
        "Delta Protection Commission":                            ra_delta,
        "Education, Department of":                               ra_education,
        "[S] Energy Commission":                                  ra_energy,
        f"Fish & Game Region #{ra_fish_n or 'n'}" if ra_fish else "Fish & Game Region #n": ra_fish,
        "Food & Agriculture, Department of":                      ra_food,
        "Forestry and Fire Protection, Department of":            ra_forestry,
        "General Services, Department of":                        ra_general_svc,
        "Health Services, Department of":                         ra_health,
        "Housing & Community Development":                        ra_housing,
        "Native American Heritage Commission":                    ra_nahc,
        "Office of Historic Preservation":                        ra_ohp,
        "Office of Public School Construction":                   ra_opsc,
        "Parks & Recreation, Department of":                      ra_parks,
        "Pesticide Regulation, Department of":                    ra_pesticide,
        "Public Utilities Commission":                            ra_puc,
        f"Regional WQCB #{ra_wqcb_n or 'n'}" if ra_wqcb else "Regional WQCB #n": ra_wqcb,
        "Resources Agency":                                       ra_resources,
        "Resources Recycling and Recovery, Department of":        ra_recycling,
        "S.F. Bay Conservation & Development Comm.":              ra_sfbay,
        "San Gabriel & Lower L.A. Rivers & Mtns. Conservancy":   ra_san_gabriel,
        "San Joaquin River Conservancy":                          ra_san_joaquin,
        "Santa Monica Mtns. Conservancy":                         ra_santa_monica,
        "State Lands Commission":                                 ra_state_lands,
        "SWRCB: Clean Water Grants":                              ra_swrcb_cwg,
        "SWRCB: Water Quality":                                   ra_swrcb_wq,
        "SWRCB: Water Rights":                                    ra_swrcb_wr,
        "Tahoe Regional Planning Agency":                         ra_tahoe,
        "Toxic Substances Control, Department of":                ra_toxic,
        "Water Resources, Department of":                         ra_water_res,
    }
    if ra_other_1.strip():
        agency_map[ra_other_1.strip()] = True
    if ra_other_2.strip():
        agency_map[ra_other_2.strip()] = True

    checked_agencies = [name for name, checked in agency_map.items() if checked]
    if checked_agencies:
        story.append(Paragraph("Selected Reviewing Agencies:", label_style))
        story.append(Spacer(1, 4))
        for agency in checked_agencies:
            if agency.startswith("[S] "):
                story.append(Paragraph(f"[S] {agency[4:]}", value_style))
            else:
                story.append(Paragraph(f"[X] {agency}", value_style))
    else:
        story.append(Paragraph("[No reviewing agencies selected]", value_style))

    # Local Public Review Period
    add_heading(story, "Local Public Review Period")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    start_str = review_start.strftime("%B %d, %Y") if review_start else "[Not provided]"
    end_str   = review_end.strftime("%B %d, %Y")   if review_end   else "[Not provided]"
    add_field(story, "Starting Date", start_str)
    add_field(story, "Ending Date",   end_str)

    # Lead Agency
    add_heading(story, "Lead Agency")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Consulting Firm", heading_style))
    add_field(story, "Firm Name",       field("Consulting Firm", la_firm_name))
    add_field(story, "Address",         field("Address", la_firm_address))
    add_field(story, "City / State / ZIP", field("City/State/ZIP", la_firm_csz))
    add_field(story, "Contact",         field("Contact", la_firm_contact))
    add_field(story, "Phone",           field("Phone", la_firm_phone))

    story.append(Paragraph("Applicant", heading_style))
    add_field(story, "Applicant Name",  field("Applicant", la_app_name))
    add_field(story, "Address",         field("Address", la_app_address))
    add_field(story, "City / State / ZIP", field("City/State/ZIP", la_app_csz))
    add_field(story, "Phone",           field("Phone", la_app_phone))

    # Signature block — use afterFlowable callback to capture heading position
    sig_position = {}

    class SigDocTemplate(SimpleDocTemplate):
        def afterFlowable(self, flowable):
            if getattr(flowable, "_sig_anchor", False):
                sig_position["page"] = self.page
                sig_position["y"]    = self.frame._y
                sig_position["h"]    = self.frame._height

    sig_doc = SigDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch, leftMargin=inch,
        topMargin=inch, bottomMargin=inch,
        title="Notice of Completion & Environmental Document Transmittal",
        author="California Energy Commission",
        subject="CEQA/NEPA Environmental Document Transmittal",
        creator="California Energy Commission NOC Generator",
    )

    add_heading(story, "Signature of Lead Agency Representative")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))

    # Invisible zero-height spacer tagged as our anchor
    anchor = Spacer(0, 8)
    anchor._sig_anchor = True
    story.append(anchor)

    sig_doc.build(story)
    buffer.seek(0)

    # ── Inject AcroForm signature field via pypdf ─────────────────────────────
    reader = PdfReader(buffer)
    writer = PdfWriter()
    writer.append(reader)

    sig_page_num = sig_position.get("page", len(writer.pages))
    sig_y        = sig_position.get("y", 200)

    target_page = writer.pages[sig_page_num - 1]

    box_left   = 72
    box_right  = 324
    box_top    = sig_y - 2
    box_bottom = box_top - 36

    sig_rect = [box_left, box_bottom, box_right, box_top]

    sig_field = DictionaryObject({
        NameObject("/Type"):    NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Widget"),
        NameObject("/FT"):      NameObject("/Sig"),
        NameObject("/T"):       TextStringObject("Signature1"),
        NameObject("/TU"):      TextStringObject("Signature of Lead Agency Representative"),
        NameObject("/Rect"):    ArrayObject([NumberObject(x) for x in sig_rect]),
        NameObject("/F"):       NumberObject(4),
        NameObject("/P"):       target_page.indirect_reference,
    })

    sig_obj = writer._add_object(sig_field)

    if "/Annots" not in target_page:
        target_page[NameObject("/Annots")] = ArrayObject()
    target_page["/Annots"].append(sig_obj)

    acroform = DictionaryObject({
        NameObject("/Fields"):   ArrayObject([sig_obj]),
        NameObject("/SigFlags"): NumberObject(3),
    })
    writer._root_object[NameObject("/AcroForm")] = acroform

    signed_buffer = io.BytesIO()
    writer.write(signed_buffer)
    signed_buffer.seek(0)
    return signed_buffer

# ── Generate button ───────────────────────────────────────────────────────────

if st.button("Generate PDF", type="primary", use_container_width=True):
    validation_errors = []
    if ra_caltrans_dist and not ra_caltrans_dist_n.strip():
        validation_errors.append("**Caltrans District #n** — District Number is required.")
    if ra_fish and not ra_fish_n.strip():
        validation_errors.append("**Fish & Game Region #n** — Region Number is required.")
    if ra_wqcb and not ra_wqcb_n.strip():
        validation_errors.append("**Regional WQCB #n** — WQCB Number is required.")
    if validation_errors:
        for msg in validation_errors:
            st.error(f"⚠️ {msg}")
    else:
        pdf_buffer = generate_pdf()
        st.success("PDF generated — only checked items will appear in the document.")
        st.download_button(
            label="Download Notice of Completion PDF",
            data=pdf_buffer,
            file_name="notice_of_completion.pdf",
            mime="application/pdf",
            use_container_width=True,
        )