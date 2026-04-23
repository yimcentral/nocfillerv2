"""
Notice of Completion & Environmental Document Transmittal
Streamlit Generator - Full Form

To run:
    pip install streamlit reportlab
    streamlit run nocav3.py
"""

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

@st.cache_data
def load_presets():
    import pandas as pd
    ods_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_data.ods")
    if not os.path.exists(ods_path):
        st.warning(f"project_data.ods not found at: {ods_path}")
        return {}
    try:
        df = pd.read_excel(ods_path, engine="odf", dtype=str)
        df = df.fillna("")
        presets = {}
        for _, row in df.iterrows():
            title = row.get("project_title", "").strip()
            if title:
                presets[title] = row.to_dict()
        return presets
    except Exception as e:
        st.error(f"Failed to load project_data.ods: {e}")
        return {}

PRESETS = load_presets()
PROJECT_TITLES = list(PRESETS.keys()) if PRESETS else []

def preset_val(preset, key, fallback=""):
    if not preset:
        return fallback
    v = preset.get(key, fallback)
    return str(v).strip() if v and str(v).strip() not in ("nan", "None") else fallback

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

project_title = st.selectbox("Project Title", options=[""] + PROJECT_TITLES)
preset = PRESETS.get(project_title, {})

preset_contact = preset_val(preset, "contact_name")
contact_options = [""] + list(CONTACTS.keys())
contact_index = contact_options.index(preset_contact) if preset_contact in contact_options else 0
contact_name = st.selectbox("Contact Person", options=contact_options, index=contact_index)

preset_phone = preset_val(preset, "phone") or CONTACTS.get(contact_name, "")
st.text_input("Phone", value=preset_phone, disabled=True, help="Auto-filled based on contact or project selection")

preset_sch = preset_val(preset, "sch_number")
sch_number = st.text_input("SCH Number", value=preset_sch, placeholder="e.g. 2024010001")

st.divider()

# ── SECTION: Project Location ─────────────────────────────────────────────────

st.subheader("Project Location")

col1, col2 = st.columns(2)
with col1:
    project_county = st.text_input("County", placeholder="e.g. Kern")
    cross_streets = st.text_input("Cross Streets", placeholder="e.g. Hwy 58 & Wind Farm Rd")
    latitude = st.text_input("Latitude", placeholder="e.g. 35° 21' 14\" N")
with col2:
    project_city = st.text_input("City / Nearest Community", placeholder="e.g. Mojave")
    project_zip = st.text_input("ZIP Code", placeholder="e.g. 93501")
    longitude = st.text_input("Longitude", placeholder="e.g. 118° 09' 22\" W")

total_acres = st.text_input("Total Acres", placeholder="e.g. 4,200")

st.divider()

# ── SECTION: Document Type ────────────────────────────────────────────────────

st.subheader("Document Type")

# -- CEQA (always expanded) ---------------------------------------------------
st.markdown("**CEQA**")

col1, col2, col3 = st.columns(3)
with col1:
    ceqa_nop       = st.checkbox("NOP")
    ceqa_neg_dec   = st.checkbox("Neg Dec")
    ceqa_draft_eir = st.checkbox("Draft EIR")
with col2:
    ceqa_early_cons = st.checkbox("Early Cons")
    ceqa_mit_neg    = st.checkbox("Mit Neg Dec")
    ceqa_sub_eir    = st.checkbox("Supplement/Subsequent EIR")
with col3:
    ceqa_other_check = st.checkbox("Other (CEQA)")

# Supplement/Subsequent EIR → prompt for Prior SCH No.
ceqa_prior_sch = ""
if ceqa_sub_eir:
    ceqa_prior_sch = st.text_input("Prior SCH No. (required for Supplement/Subsequent EIR)",
                                   placeholder="e.g. 2019010001")

# CEQA Other free-text
ceqa_other_text = ""
if ceqa_other_check:
    ceqa_other_text = st.text_input("CEQA — Other (please specify)", placeholder="Describe other CEQA document type")

# -- NEPA (collapsed behind a checkbox) ---------------------------------------
st.markdown("**NEPA**")
nepa_section = st.checkbox("NEPA document included")

nepa_noi = nepa_ea = nepa_eis = nepa_fonsi = False
if nepa_section:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        nepa_noi = st.checkbox("NOI")
    with col2:
        nepa_ea = st.checkbox("EA")
    with col3:
        nepa_eis = st.checkbox("Draft EIS")
    with col4:
        nepa_fonsi = st.checkbox("FONSI")

# -- Other document type (collapsed behind a checkbox) ------------------------
st.markdown("**Other**")
other_section = st.checkbox("Other document type included")

other_joint = other_final = other_custom_check = False
other_custom_text = ""
if other_section:
    col1, col2, col3 = st.columns(3)
    with col1:
        other_joint = st.checkbox("Joint Document")
    with col2:
        other_final = st.checkbox("Final Document")
    with col3:
        other_custom_check = st.checkbox("Other")
    if other_custom_check:
        other_custom_text = st.text_input("Other document type (please specify)", placeholder="Describe document type")

st.divider()

# ── SECTION: Local Action Type ────────────────────────────────────────────────

st.subheader("Local Action Type")

col1, col2, col3 = st.columns(3)
with col1:
    lat_gpu      = st.checkbox("General Plan Update")
    lat_gpa      = st.checkbox("General Plan Amendment")
    lat_gpe      = st.checkbox("General Plan Element")
    lat_cp       = st.checkbox("Community Plan")
    lat_sp       = st.checkbox("Specific Plan")
with col2:
    lat_mp       = st.checkbox("Master Plan")
    lat_pud      = st.checkbox("Planned Unit Development")
    lat_rezone   = st.checkbox("Rezone")
    lat_prezone  = st.checkbox("Prezone")
    lat_annex    = st.checkbox("Annexation")
with col3:
    lat_redevel  = st.checkbox("Redevelopment")
    lat_use      = st.checkbox("Use Permit")
    lat_coastal  = st.checkbox("Coastal Permit")
    lat_site     = st.checkbox("Site Plan")
    lat_land_div = st.checkbox("Land Division (Subdivision, etc.)")
    lat_other_check = st.checkbox("Other (Local Action)")

lat_other_text = ""
if lat_other_check:
    lat_other_text = st.text_input("Local Action Type — Other (please specify)", placeholder="Describe other local action type")

st.divider()

# ── SECTION: Development Type ─────────────────────────────────────────────────

st.subheader("Development Type")

# ── Power ──
dev_power = st.checkbox("Power", value=True)
dev_power_wind = dev_power_solar = dev_power_bess = dev_power_other = False
dev_power_other_text = ""
if dev_power:
    with st.container():
        st.markdown("<div style='margin-left:20px'>", unsafe_allow_html=True)
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            dev_power_wind  = st.checkbox("Wind")
        with pc2:
            dev_power_solar = st.checkbox("Solar Photovoltaic")
        with pc3:
            dev_power_bess  = st.checkbox("Battery Energy Storage System")
        with pc4:
            dev_power_other = st.checkbox("Other (Power)")
        if dev_power_other:
            dev_power_other_text = st.text_input("Power — Other (specify)", placeholder="e.g. Geothermal")
        st.markdown("</div>", unsafe_allow_html=True)

# ── Non-Power ──
dev_nonpower = st.checkbox("Non-Power")

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

        dev_residential = st.checkbox("Residential")
        if dev_residential:
            rc1, rc2 = st.columns(2)
            with rc1:
                dev_residential_units = st.text_input("Residential — Units", placeholder="e.g. 250")
            with rc2:
                dev_residential_acres = st.text_input("Residential — Acres", placeholder="e.g. 12.5")

        dev_office = st.checkbox("Office")
        if dev_office:
            oc1, oc2, oc3 = st.columns(3)
            with oc1:
                dev_office_sqft  = st.text_input("Office — Sq. Ft.", placeholder="e.g. 45,000")
            with oc2:
                dev_office_acres = st.text_input("Office — Acres", placeholder="e.g. 3.2")
            with oc3:
                dev_office_emp   = st.text_input("Office — Employees", placeholder="e.g. 180")

        dev_commercial = st.checkbox("Commercial")
        if dev_commercial:
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                dev_commercial_sqft  = st.text_input("Commercial — Sq. Ft.", placeholder="e.g. 20,000")
            with cc2:
                dev_commercial_acres = st.text_input("Commercial — Acres", placeholder="e.g. 2.0")
            with cc3:
                dev_commercial_emp   = st.text_input("Commercial — Employees", placeholder="e.g. 75")

        dev_industrial = st.checkbox("Industrial")
        if dev_industrial:
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                dev_industrial_sqft  = st.text_input("Industrial — Sq. Ft.", placeholder="e.g. 100,000")
            with ic2:
                dev_industrial_acres = st.text_input("Industrial — Acres", placeholder="e.g. 8.0")
            with ic3:
                dev_industrial_emp   = st.text_input("Industrial — Employees", placeholder="e.g. 50")

        dev_educational = st.checkbox("Educational")
        if dev_educational:
            dev_educational_text = st.text_input("Educational — Details", placeholder="e.g. K-12 school, 800 students")

        dev_recreational = st.checkbox("Recreational")
        if dev_recreational:
            dev_recreational_text = st.text_input("Recreational — Details", placeholder="e.g. Regional park, sports fields")

        dev_water = st.checkbox("Water Facilities")
        if dev_water:
            wc1, wc2 = st.columns(2)
            with wc1:
                dev_water_type = st.text_input("Water Facilities — Type", placeholder="e.g. Reservoir, Treatment Plant")
            with wc2:
                dev_water_mgd  = st.text_input("Water Facilities — MGD", placeholder="e.g. 5.2")

        dev_transportation = st.checkbox("Transportation")
        if dev_transportation:
            dev_transportation_type = st.text_input("Transportation — Type", placeholder="e.g. Highway, Rail, Airport")

        dev_mining = st.checkbox("Mining")
        if dev_mining:
            dev_mining_mineral = st.text_input("Mining — Mineral", placeholder="e.g. Silica, Gravel")

        dev_waste = st.checkbox("Waste Treatment")
        if dev_waste:
            wt1, wt2 = st.columns(2)
            with wt1:
                dev_waste_type = st.text_input("Waste Treatment — Type", placeholder="e.g. Wastewater, Solid Waste")
            with wt2:
                dev_waste_mgd  = st.text_input("Waste Treatment — MGD", placeholder="e.g. 2.0")

        dev_hazardous = st.checkbox("Hazardous Waste")
        if dev_hazardous:
            dev_hazardous_type = st.text_input("Hazardous Waste — Type", placeholder="e.g. Medical, Chemical")

        dev_other = st.checkbox("Other (Non-Power)")
        if dev_other:
            dev_other_text = st.text_input("Other — Details", placeholder="Describe other development type")

        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── SECTION: Project Issues ───────────────────────────────────────────────────

st.subheader("Project Issues Discussed in Document")

col1, col2 = st.columns(2)
with col1:
    issue_air  = st.checkbox("Air Quality")
    issue_land = st.checkbox("Land Use")
with col2:
    issue_traffic = st.checkbox("Traffic")
    issue_tribal  = st.checkbox("Tribal Cultural Resources")

st.divider()

# ── SECTION: Land Use & Description ──────────────────────────────────────────

st.subheader("Present Land Use / Zoning / GP Designation")
land_use = st.text_area("Land Use Description",
                        placeholder="e.g. Rural/Agricultural, Zoned A-1, GP designation Open Space",
                        height=80)

st.subheader("Project Description")
project_description = st.text_area("Project Description",
                                   placeholder="Describe the project in full here...",
                                   height=150)

st.divider()

# ── SECTION: Reviewing Agencies Checklist ────────────────────────────────────

st.subheader("Reviewing Agencies Checklist")

col_l, col_r = st.columns(2)

with col_l:
    ra_air             = st.checkbox("Air Resources Board", value=True)
    ra_boating         = st.checkbox("Boating & Waterways, Department of", value=False)
    ra_cal_ema         = st.checkbox("California Emergency Management Agency", value=True)
    ra_chp             = st.checkbox("California Highway Patrol", value=True)
    ra_caltrans_dist   = st.checkbox("Caltrans District #n", value=True)
    ra_caltrans_dist_n = ""
    if ra_caltrans_dist:
        ra_caltrans_dist_n = st.text_input("Caltrans District Number", placeholder="e.g. 7")
    ra_caltrans_aero   = st.checkbox("Caltrans Division of Aeronautics", value=False)
    ra_caltrans_plan   = st.checkbox("Caltrans Planning", value=True)
    ra_cvfpb           = st.checkbox("Central Valley Flood Protection Board", value=False)
    ra_coachella       = st.checkbox("Coachella Valley Mtns. Conservancy", value=False)
    ra_coastal         = st.checkbox("Coastal Commission", value=False)
    ra_colorado        = st.checkbox("Colorado River Board", value=False)
    ra_conservation    = st.checkbox("Conservation, Department of", value=True)
    ra_corrections     = st.checkbox("Corrections, Department of", value=False)
    ra_delta           = st.checkbox("Delta Protection Commission", value=False)
    ra_education       = st.checkbox("Education, Department of", value=False)
    ra_energy          = st.checkbox("Energy Commission", value=True)
    ra_fish            = st.checkbox("Fish & Game Region #n", value=True)
    ra_fish_n = ""
    if ra_fish:
        ra_fish_n = st.text_input("Fish & Game Region Number", placeholder="e.g. 4")
    ra_food            = st.checkbox("Food & Agriculture, Department of", value=False)
    ra_forestry        = st.checkbox("Forestry and Fire Protection, Department of", value=True)
    ra_general_svc     = st.checkbox("General Services, Department of", value=False)
    ra_health          = st.checkbox("Health Services, Department of", value=False)
    ra_housing         = st.checkbox("Housing & Community Development", value=False)
    ra_nahc            = st.checkbox("Native American Heritage Commission", value=True)

with col_r:
    ra_ohp             = st.checkbox("Office of Historic Preservation", value=True)
    ra_opsc            = st.checkbox("Office of Public School Construction", value=False)
    ra_parks           = st.checkbox("Parks & Recreation, Department of", value=False)
    ra_pesticide       = st.checkbox("Pesticide Regulation, Department of", value=False)
    ra_puc             = st.checkbox("Public Utilities Commission", value=True)
    ra_wqcb            = st.checkbox("Regional WQCB #n", value=True)
    ra_wqcb_n = ""
    if ra_wqcb:
        ra_wqcb_n = st.text_input("Regional WQCB Number", placeholder="e.g. 5")
    ra_resources       = st.checkbox("Resources Agency", value=True)
    ra_recycling       = st.checkbox("Resources Recycling and Recovery, Department of", value=False)
    ra_sfbay           = st.checkbox("S.F. Bay Conservation & Development Comm.", value=False)
    ra_san_gabriel     = st.checkbox("San Gabriel & Lower L.A. Rivers & Mtns. Conservancy", value=False)
    ra_san_joaquin     = st.checkbox("San Joaquin River Conservancy", value=False)
    ra_santa_monica    = st.checkbox("Santa Monica Mtns. Conservancy", value=False)
    ra_state_lands     = st.checkbox("State Lands Commission", value=False)
    ra_swrcb_cwg       = st.checkbox("SWRCB: Clean Water Grants", value=False)
    ra_swrcb_wq        = st.checkbox("SWRCB: Water Quality", value=True)
    ra_swrcb_wr        = st.checkbox("SWRCB: Water Rights", value=True)
    ra_tahoe           = st.checkbox("Tahoe Regional Planning Agency", value=False)
    ra_toxic           = st.checkbox("Toxic Substances Control, Department of", value=True)
    ra_water_res       = st.checkbox("Water Resources, Department of", value=True)
    ra_other_1         = st.text_input("Other Agency 1", placeholder="e.g. County Planning Department")
    ra_other_2         = st.text_input("Other Agency 2", placeholder="e.g. Local Air District")

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
la_firm_name    = st.text_input("Consulting Firm", placeholder="e.g. SWCA Environmental Consultants", label_visibility="collapsed")
la_firm_address = st.text_input("Address", placeholder="e.g. 1420 Harbor Bay Pkwy", key="la_firm_address")
la_firm_csz     = st.text_input("City / State / ZIP", placeholder="e.g. Alameda, CA 94502", key="la_firm_csz")
la_firm_contact = st.text_input("Contact", placeholder="e.g. Jane Smith", key="la_firm_contact")
la_firm_phone   = st.text_input("Phone", placeholder="e.g. 510-555-0100", key="la_firm_phone")

st.markdown("**Applicant**")
la_app_name     = st.text_input("Applicant", placeholder="e.g. Pacific Solar LLC", label_visibility="collapsed")
la_app_address  = st.text_input("Address", placeholder="e.g. 350 Market St", key="la_app_address")
la_app_csz      = st.text_input("City / State / ZIP", placeholder="e.g. San Francisco, CA 94105", key="la_app_csz")
la_app_phone    = st.text_input("Phone", placeholder="e.g. 415-555-0200", key="la_app_phone")

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

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title=PDF_TITLE,
        author="California Energy Commission",
        subject="CEQA/NEPA Environmental Document Transmittal",
        creator="California Energy Commission NOC Generator",
    )

    styles = getSampleStyleSheet()

    # H1 — document title (used once, sets PDF heading structure)
    title_style = ParagraphStyle(
        "FormTitle",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=4,
        textColor=colors.HexColor("#003366"),
        # outlineLevel=0 marks this as H1 in the PDF tag tree
        outlineLevel=0,
    )
    # H2 — section headings
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
        """Add a semantically tagged heading and a visual rule."""
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
    add_field(story, "Phone",            field("Phone", preset_phone))
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
        power_subs = {"Wind": dev_power_wind, "Solar Photovoltaic": dev_power_solar,
                      "Battery Energy Storage System": dev_power_bess}
        if dev_power_other and dev_power_other_text.strip():
            power_subs[f"Other: {dev_power_other_text.strip()}"] = True
        sub_str = checked_list(power_subs) or "—"
        add_field(story, "Power", sub_str)

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
        "Air Quality": issue_air, "Traffic": issue_traffic,
        "Land Use": issue_land, "Tribal Cultural Resources": issue_tribal,
    }
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

    # Signature block
    add_heading(story, "Signature of Lead Agency Representative")
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 60))

    doc.build(story)
    buffer.seek(0)

    # ── Inject AcroForm signature field via pypdf ─────────────────────────────
    reader = PdfReader(buffer)
    writer = PdfWriter()
    writer.append(reader)

    last_page = writer.pages[-1]
    page_height = float(last_page.mediabox.height)

    # Small signature box: 2.5in wide x 0.5in tall, top-left of signature area
    # Placed 1in from left, 1.5in from bottom
    sig_rect = [72, 108, 252, 144]

    sig_field = DictionaryObject({
        NameObject("/Type"):    NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Widget"),
        NameObject("/FT"):      NameObject("/Sig"),
        NameObject("/T"):       TextStringObject("Signature1"),
        NameObject("/TU"):      TextStringObject("Signature of Lead Agency Representative"),
        NameObject("/Rect"):    ArrayObject([NumberObject(x) for x in sig_rect]),
        NameObject("/F"):       NumberObject(4),
        NameObject("/P"):       last_page.indirect_reference,
    })

    sig_obj = writer._add_object(sig_field)

    if "/Annots" not in last_page:
        last_page[NameObject("/Annots")] = ArrayObject()
    last_page["/Annots"].append(sig_obj)

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
    pdf_buffer = generate_pdf()
    st.success("PDF generated — only checked items will appear in the document.")
    st.download_button(
        label="Download Notice of Completion PDF",
        data=pdf_buffer,
        file_name="notice_of_completion.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
