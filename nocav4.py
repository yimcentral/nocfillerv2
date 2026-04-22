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

col1, col2, col3 = st.columns(3)
with col1:
    dev_power = st.checkbox("Power")
with col2:
    dev_residential = st.checkbox("Residential")
with col3:
    dev_commercial = st.checkbox("Commercial")

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

# ── Helpers ───────────────────────────────────────────────────────────────────

def field(label, value):
    return value.strip() if value and value.strip() else f"[{label} not provided]"

def checked_list(options_dict):
    selected = [label for label, checked in options_dict.items() if checked]
    return ", ".join(selected) if selected else None

# ── PDF generation ────────────────────────────────────────────────────────────

def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title="Notice of Completion & Environmental Document Transmittal",
        author="California Energy Commission",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "FormTitle", parent=styles["Heading1"],
        fontSize=14, spaceAfter=4,
        textColor=colors.HexColor("#003366"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"],
        fontSize=11, spaceBefore=14, spaceAfter=4,
        textColor=colors.HexColor("#003366"),
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

    def add_checked(story, label, options_dict):
        result = checked_list(options_dict)
        if result:
            story.append(Paragraph(label, label_style))
            story.append(Paragraph(result, value_style))

    story = []

    # Header
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
    story.append(Paragraph("Overview", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "Project Title",    field("Project Title", project_title))
    add_field(story, "Lead Agency",      "California Energy Commission")
    add_field(story, "Project Manager",  field("Contact Person", contact_name))
    add_field(story, "Mailing Address",  "715 P St, MS 40")
    add_field(story, "Phone",            field("Phone", phone))
    add_field(story, "City",             "Sacramento")
    add_field(story, "ZIP",              "95814")
    add_field(story, "County",           "Sacramento")

    # Project Location
    story.append(Paragraph("Project Location", heading_style))
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
        story.append(Paragraph("Document Type", heading_style))
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
        story.append(Paragraph("Local Action Type", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))
        add_checked(story, "Local Action Type", lat_items)

    # Development Type
    dev_checked = {"Power": dev_power, "Residential": dev_residential, "Commercial": dev_commercial}
    if any(dev_checked.values()):
        story.append(Paragraph("Development Type", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))
        add_checked(story, "Development Type", dev_checked)

    # Project Issues
    issues_checked = {
        "Air Quality": issue_air, "Traffic": issue_traffic,
        "Land Use": issue_land, "Tribal Cultural Resources": issue_tribal,
    }
    if any(issues_checked.values()):
        story.append(Paragraph("Project Issues Discussed in Document", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 4))
        add_checked(story, "Issues", issues_checked)

    # Land Use & Description
    story.append(Paragraph("Present Land Use / Zoning / GP Designation", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "Land Use / Zoning / GP Designation", field("Land Use", land_use))

    story.append(Paragraph("Project Description", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    add_field(story, "Description", field("Project Description", project_description))

    doc.build(story)
    buffer.seek(0)
    return buffer

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
