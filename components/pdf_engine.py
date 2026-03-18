"""
OSIM PDF GENERATION ENGINE
==============================================================================
Locks down the Cover Page grey-box layout, aligns the Cost grid, moves BCI to Page 2,
replicates the underlined MTO forms for Inventory/Inspection, and aligns cover photo.
"""

import os
import tempfile
import streamlit as st
from fpdf import FPDF
from datetime import datetime, date

# --- 1. SECURE DATA FETCHING & SANITIZATION ---
def sanitize_text(text):
    if not isinstance(text, str): return str(text)
    replacements = {"•": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "--", "°": " deg", "²": "^2", "³": "^3", "\n": " "}
    for bad, good in replacements.items(): text = text.replace(bad, good)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def safe_float(val):
    try: return float(val) if val is not None else 0.0
    except (ValueError, TypeError): return 0.0

def fetch(key, default=""):
    val = st.session_state.get(key, default)
    if val is None or val == "": return default
    if isinstance(val, (datetime, date)): return val.strftime("%d-%b-%Y")
    if isinstance(val, list): return sanitize_text(", ".join(val))
    return sanitize_text(str(val))

def fetch_multiline(key, default=""):
    val = st.session_state.get(key, default)
    if val is None or val == "": return default
    text = str(val)
    replacements = {"•": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "--", "°": " deg", "²": "^2", "³": "^3"}
    for bad, good in replacements.items(): text = text.replace(bad, good)
    return text.encode('latin-1', 'ignore').decode('latin-1')

# --- 2. CUSTOM PDF CLASS ---
class OSIMReport(FPDF):
    def header(self):
        if self.page_no() > 2:
            self.set_font("helvetica", "B", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, "MUNICIPAL STRUCTURE INSPECTION FORM", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
            self.ln(2)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("helvetica", "B", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f"Page {self.page_no()-1}", align="R")
            self.set_text_color(0, 0, 0)

    def cell_pair(self, x, y, label, value, label_w=28, val_w=40):
        self.set_xy(x, y)
        self.set_font("helvetica", "B", 7)
        self.cell(label_w, 4, label, border=0)
        self.set_xy(x + label_w, y)
        self.set_font("helvetica", "", 7)
        self.cell(val_w, 4, str(value), border=0)

    def full_width_box(self, y, label, value, height=12, label_w=55, val_w=140):
        self.set_fill_color(230, 230, 230)
        self.rect(10, y, label_w, height, style='FD') 
        self.rect(10 + label_w, y, val_w, height, style='D') 
        self.set_xy(11, y + 1)
        self.set_font("helvetica", "B", 8)
        self.multi_cell(label_w - 2, 4, label, border=0, align="L")
        self.set_xy(10 + label_w + 1, y + 1)
        self.set_font("helvetica", "", 8)
        self.multi_cell(val_w - 2, 4, str(value)[:300], border=0, align="L")

    def form_line(self, x, y, label, value, label_w, line_w, align="L"):
        self.set_xy(x, y)
        self.set_font("helvetica", "", 8)
        self.cell(label_w, 5, label, border=0)
        self.set_xy(x + label_w, y)
        self.set_font("helvetica", "B", 8)
        self.cell(line_w, 5, str(value)[:35], border='B', align=align)

    def draw_checkbox(self, x, y, label, is_checked):
        self.set_font("helvetica", "", 8)
        self.set_xy(x, y)
        self.rect(x, y+1, 3, 3)
        if is_checked:
            self.set_font("helvetica", "B", 7)
            self.set_xy(x, y+0.5)
            self.cell(3, 4, "X", align="C")
        self.set_font("helvetica", "", 8)
        self.set_xy(x + 4, y)
        self.cell(25, 5, label)

# --- 3. MAIN COMPILER FUNCTION ---
def create_pdf(filename):
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    pdf = OSIMReport(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=False)
    fid = st.session_state.get('form_id', 'init')

    # ==========================================
    # PAGE 1: EXACT COVER PAGE
    # ==========================================
    pdf.add_page()
    
    # Header
    pdf.set_xy(10, 10)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(80, 8, "STRUCTURE SUMMARY", border=0)

    # Image - Pushed down to y=20 to align with Structure Name
    cover_photo = st.session_state.get("cp_image_upload")
    photo_x, photo_y, photo_w, photo_h = 105, 20, 100, 70
    if cover_photo is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(cover_photo.getvalue())
                tmp_path = tmp_file.name
            pdf.image(tmp_path, x=photo_x, y=photo_y, w=photo_w, h=photo_h)
            pdf.rect(photo_x, photo_y, photo_w, photo_h, 'D') 
            os.remove(tmp_path)
        except Exception as e:
            pdf.set_xy(photo_x, photo_y)
            pdf.cell(photo_w, photo_h, f"[Image Error: {e}]", border=1, align="C")
    else:
        pdf.set_xy(photo_x, photo_y)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(photo_w, photo_h, "[No Photo Uploaded]", border=1, align="C")

    # Info Grids (Grey Labels, White Values)
    pdf.set_fill_color(230, 230, 230)
    
    def grid_row(y, l1, v1, lw1=28, vw1=62, h=5):
        pdf.set_xy(10, y)
        pdf.set_font("helvetica", "B", 8); pdf.cell(lw1, h, l1, border=1, fill=True)
        pdf.set_font("helvetica", "", 8); pdf.cell(vw1, h, str(v1)[:40], border=1)

    def grid_row_2(y, l1, v1, l2, v2, lw1=20, vw1=25, lw2=20, vw2=25, h=5):
        pdf.set_xy(10, y)
        pdf.set_font("helvetica", "B", 8); pdf.cell(lw1, h, l1, border=1, fill=True)
        pdf.set_font("helvetica", "", 8); pdf.cell(vw1, h, str(v1)[:20], border=1)
        pdf.set_font("helvetica", "B", 8); pdf.cell(lw2, h, l2, border=1, fill=True)
        pdf.set_font("helvetica", "", 8); pdf.cell(vw2, h, str(v2)[:20], border=1)

    y = 20
    grid_row(y, "Structure Name:", fetch(f'p1_str_name_{fid}')); y+=5
    grid_row(y, "Road Name:", fetch(f'p1_road_name_{fid}')); y+=5
    grid_row(y, "Bridge/Culvert:", fetch('p1_class_sel', 'Bridge').upper()); y+=5
    grid_row(y, "Site ID:", fetch(f'p1_site_no_{fid}')); y+=5
    grid_row(y, "Structure Type:", fetch(f'p1_type_{fid}')); y+=5
    grid_row(y, "Owner:", fetch(f'p1_owner_{fid}')); y+=5
    grid_row(y, "Location:", fetch(f'p1_location_{fid}')); y+=8

    grid_row_2(y, "Year Built:", fetch(f'p1_yr_built_{fid}'), "AADT:", fetch(f'p1_aadt_{fid}')); y+=5
    grid_row_2(y, "Latitude:", fetch(f'p1_lat_{fid}'), "Length (m):", fetch(f'p1_deck_len_{fid}')); y+=5
    grid_row_2(y, "No. of Lanes:", fetch(f'p1_lanes_{fid}'), "Longitude:", fetch(f'p1_lon_{fid}')); y+=5
    grid_row_2(y, "Width (m):", fetch(f'p1_str_width_{fid}'), "Posted Speed:", fetch(f'p1_speed_{fid}', "0") + " km/h"); y+=5
    grid_row_2(y, "Orientation:", fetch('p1_dir_sel'), "Road Width:", fetch(f'p1_road_width_{fid}')); y+=5
    grid_row_2(y, "% Trucks:", fetch(f'p1_trucks_{fid}'), "No. Spans:", fetch(f'p1_spans_{fid}')); y+=5
    grid_row_2(y, "Skew Angle:", fetch(f'p1_skew_{fid}'), "Load Posting:", fetch(f'p1_load_limit_{fid}')); y+=8

    grid_row(y, "Inspection Date:", fetch(f'p2_date_{fid}')); y+=5
    grid_row(y, "Inspector(s):", fetch(f'p2_inspector_{fid}')); y+=5
    grid_row(y, "Type of Insp:", fetch(f'p2_insp_type_{fid}')); y+=8

    # BCI Mini Grid
    pdf.set_xy(10, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(35, 6, "Bridge Condition Index", border=1, fill=True, align="C")
    bci_val = fetch('cp_bci_score', '0')
    pdf.cell(15, 6, bci_val if bci_val != '0' else 'TBD', border=1, align="C")
    
    pdf.set_xy(65, y)
    pdf.cell(30, 6, "Condition Rating", border=1, fill=True, align="C")
    cond_rating = "TBD"
    bci_num = safe_float(bci_val)
    if bci_num >= 70: cond_rating = "GOOD"
    elif bci_num >= 60: cond_rating = "FAIR"
    elif bci_num > 0: cond_rating = "POOR"
    pdf.cell(25, 6, cond_rating, border=1, align="C")

    # Bottom Boxes
    y_box = y + 10
    pdf.full_width_box(y_box, "Significant Findings:", fetch_multiline(f'p2_overall_comm_{fid}', 'None noted.'), 18); y_box += 18
    pdf.full_width_box(y_box, "Immediate Intervention\nRequired:", fetch('rep_p5_imm_interv_dd_sel', 'None'), 12); y_box += 12
    pdf.full_width_box(y_box, "Additional Investigations:\nInvestigation Notes:", fetch('rep_inv_sel_1', 'None'), 14); y_box += 14
    pdf.full_width_box(y_box, "Recommended Work:", fetch('rep_p5_overall_rw_sel', 'None'), 12); y_box += 12

    # Fixed Cost Box Alignment (Total 195 width aligned with label_w=55)
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(10, y_box, 55, 12, 'FD')
    pdf.rect(65, y_box, 42.5, 12, 'D')
    pdf.rect(107.5, y_box, 55, 12, 'FD')
    pdf.rect(162.5, y_box, 42.5, 12, 'D')
    
    pdf.set_xy(10, y_box + 2)
    pdf.set_font("helvetica", "B", 8)
    pdf.multi_cell(55, 4, "Estimated Replacement\nCosts", align="C")
    pdf.set_xy(65, y_box + 4)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(42.5, 4, f"$ {fetch('rep_est_replacement', '0.00')}", align="C")
    
    pdf.set_xy(107.5, y_box + 2)
    pdf.set_font("helvetica", "B", 8)
    pdf.multi_cell(55, 4, "Estimate of\nRecommended Work Costs", align="C")
    pdf.set_xy(162.5, y_box + 4)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(42.5, 4, f"$ {fetch('rep_est_rec_work', '0.00')}", align="C")
    y_box += 12

    pdf.full_width_box(y_box, "Principal Maintenance\nNeeds:", fetch('rep_pm_sel_1', 'None'), 12); y_box += 12
    pdf.full_width_box(y_box, "Common Deficiencies\nWarranting Short Term\nIntervention:", fetch('rep_cd_sel_1', 'None'), 16); y_box += 16
    pdf.full_width_box(y_box, "Approach/Bridge Barriers:\nBarrier Notes:", fetch('rep_bar_sel_1', 'None'), 14)


    # ==========================================
    # PAGE 2: BCI CONDITION SUMMARY TABLE
    # ==========================================
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page(orientation="L") 
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Structure Condition Summary Form", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("helvetica", "B", 6)
    pdf.set_text_color(0, 51, 102) 
    
    headers = [
        "Element Group", "Element Name", "Unit\n(Qty.)", "Unit Price\n(MTO)", 
        "Total\nElement\nQuantity", "Element\nQty. in\nExcellent\nCondition\n(1.00)",
        "Element\nQuantity in\nGood\nCondition\n(0.75)", "Element\nQuantity in\nFair\nCondition\n(0.4)",
        "Element\nQuantity in\nPoor\nCondition\n(0)", "Total\nReplacement\nValue (TRV)",
        "Current\nElement\nValue\n(CEV)", "Element\nCondition\nIndex", 
        "Performance\nDeficiency", "Maintenance\nNeed"
    ]
    widths = [25, 35, 10, 15, 15, 15, 15, 15, 15, 20, 20, 15, 22, 22]
    
    start_x, start_y, max_h = pdf.get_x(), pdf.get_y(), 24
    for i, head in enumerate(headers):
        pdf.set_xy(start_x, start_y)
        pdf.multi_cell(widths[i], 4, head, border=0, align="C")
        pdf.rect(start_x, start_y, widths[i], max_h, 'D')
        start_x += widths[i]
        
    pdf.set_y(start_y + max_h)
    pdf.set_text_color(0, 0, 0) 

    elements = st.session_state.get('report_elements', [])
    pdf.set_font("helvetica", "", 6)
    for el in elements:
        pdf.cell(widths[0], 6, sanitize_text(el.get('group', ''))[:20], border=1)
        pdf.cell(widths[1], 6, sanitize_text(el.get('name', ''))[:30], border=1)
        pdf.cell(widths[2], 6, sanitize_text(el.get('unit', '')), border=1, align="C")
        pdf.cell(widths[3], 6, "$0.00", border=1, align="C") 
        pdf.cell(widths[4], 6, f"{safe_float(el.get('Total')):,.2f}", border=1, align="C")
        pdf.cell(widths[5], 6, f"{safe_float(el.get('exc')):,.2f}", border=1, align="C")
        pdf.cell(widths[6], 6, f"{safe_float(el.get('good')):,.2f}", border=1, align="C")
        pdf.cell(widths[7], 6, f"{safe_float(el.get('fair')):,.2f}", border=1, align="C")
        pdf.cell(widths[8], 6, f"{safe_float(el.get('poor')):,.2f}", border=1, align="C")
        pdf.cell(widths[9], 6, "$0", border=1, align="C")
        pdf.cell(widths[10], 6, "$0", border=1, align="C")
        pdf.cell(widths[11], 6, "-", border=1, align="C")
        pd_val = sanitize_text(el.get('perf_def', '00'))[:2]
        mn_val = sanitize_text(el.get('maint_need', '00'))[:2]
        pdf.cell(widths[12], 6, pd_val, border=1, align="C")
        pdf.cell(widths[13], 6, mn_val, border=1, align="C")
        pdf.ln(6)


    # ==========================================
    # PAGE 3: EXACT INVENTORY REPLICA
    # ==========================================
    pdf.set_auto_page_break(auto=False)
    pdf.add_page(orientation="P")
    
    pdf.set_font("helvetica", "", 9)
    str_class = fetch('p1_class_sel', 'BRIDGE').upper()
    pdf.cell(100, 6, str_class, border=0, align="L")
    pdf.cell(95, 6, f"Site No.: {fetch(f'p1_site_no_{fid}')}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_fill_color(230, 230, 230)
    pdf.rect(10, 30, 195, 125, 'D')
    pdf.rect(10, 30, 195, 8, 'FD')
    pdf.set_xy(12, 32)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(100, 4, "INVENTORY DATA:", border=0)

    y = 42
    pdf.form_line(15, y, "Structure Name", fetch(f'p1_str_name_{fid}'), 30, 65)
    y += 9
    pdf.form_line(15, y, "Main Hwy/Road #", fetch(f'p1_hwy_{fid}'), 30, 65)
    
    under = fetch(f'p1_under_{fid}')
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(115, y-4); pdf.cell(20, 4, "Under")
    pdf.set_xy(115, y); pdf.cell(20, 4, "Structure:")
    pdf.draw_checkbox(135, y-4, "Navigable Water", "Navigable Water" in under)
    pdf.draw_checkbox(165, y-4, "Non-Navigable", "Non-Navigable" in under)
    pdf.draw_checkbox(135, y, "Rail", "Rail" in under)
    pdf.draw_checkbox(150, y, "Road", "Road" in under)
    pdf.draw_checkbox(165, y, "Ped.", "Pedestrian" in under)
    pdf.draw_checkbox(185, y, "Other", "Other" in under)
    
    y += 9
    pdf.form_line(15, y, "Road Name", fetch(f'p1_road_name_{fid}'), 30, 65)
    on_str = fetch(f'p1_on_{fid}')
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(115, y-2); pdf.cell(20, 4, "On")
    pdf.set_xy(115, y+2); pdf.cell(20, 4, "Structure:")
    pdf.draw_checkbox(135, y, "Rail", "Rail" in on_str)
    pdf.draw_checkbox(150, y, "Road", "Road" in on_str)
    pdf.draw_checkbox(165, y, "Ped.", "Pedestrian" in on_str)
    pdf.draw_checkbox(185, y, "Other", "Other" in on_str)
    
    y += 9
    pdf.form_line(15, y, "Structure Location", fetch(f'p1_location_{fid}'), 30, 160)
    y += 9
    pdf.form_line(15, y, "Latitude", fetch(f'p1_lat_{fid}'), 30, 65, "C")
    pdf.form_line(115, y, "Longitude", fetch(f'p1_lon_{fid}'), 20, 60, "C")
    
    y += 9
    pdf.form_line(15, y, "Owner(s)", fetch(f'p1_owner_{fid}'), 30, 65)
    pdf.set_font("helvetica", "", 8)
    pdf.set_xy(115, y-2); pdf.cell(20, 4, "Heritage")
    pdf.set_xy(115, y+2); pdf.cell(20, 4, "Designation")
    hd = fetch(f'p1_heritage_{fid}')
    pdf.draw_checkbox(135, y-2, "Not Cons.", "Not Cons." in hd)
    pdf.draw_checkbox(155, y-2, "Cons./Not App.", "Cons./Not App." in hd)
    pdf.draw_checkbox(180, y-2, "List", "List/Not Desig." in hd)
    pdf.draw_checkbox(135, y+2, "Desig./not List", "Desig./not List" in hd)
    pdf.draw_checkbox(165, y+2, "Desig. & List", "Desig. & List" in hd)

    y += 9
    pdf.form_line(15, y, "MTO Region", fetch(f'p1_region_{fid}'), 30, 65)
    pdf.set_font("helvetica", "", 8)
    pdf.set_xy(115, y); pdf.cell(20, 4, "Road Class:")
    rc = fetch(f'p1_road_class_{fid}')
    pdf.draw_checkbox(135, y, "Freeway", "Freeway" in rc)
    pdf.draw_checkbox(150, y, "Arterial", "Arterial" in rc)
    pdf.draw_checkbox(165, y, "Collector", "Collector" in rc)
    pdf.draw_checkbox(185, y, "Local", "Local" in rc)

    y += 9
    pdf.form_line(15, y, "MTO District", fetch(f'p1_district_{fid}'), 30, 65)
    pdf.form_line(115, y, "Posted Speed", fetch(f'p1_speed_{fid}'), 20, 25, "C")
    pdf.form_line(165, y, "No. of Lanes", fetch(f'p1_lanes_{fid}'), 25, 10, "C")
    
    y += 9
    pdf.form_line(15, y, "Old County", fetch(f'p1_county_{fid}'), 30, 65)
    pdf.form_line(115, y, "AADT", fetch(f'p1_aadt_{fid}'), 20, 25, "C")
    pdf.form_line(165, y, "% Trucks", fetch(f'p1_trucks_{fid}'), 25, 10, "C")

    y += 9
    pdf.form_line(15, y, "Geographic Twp.", fetch(f'p1_twp_{fid}'), 30, 65)
    pdf.set_font("helvetica", "", 8)
    pdf.set_xy(115, y); pdf.cell(20, 4, "Special Routes:")
    sr = fetch(f'p1_routes_{fid}')
    pdf.draw_checkbox(135, y, "Transit", "Transit" in sr)
    pdf.draw_checkbox(150, y, "Truck", "Truck" in sr)
    pdf.draw_checkbox(165, y, "School", "School" in sr)
    pdf.draw_checkbox(185, y, "Bicycle", "Bicycle" in sr)

    y += 9
    pdf.form_line(15, y, "Structure Type", fetch(f'p1_type_{fid}'), 30, 65, "C")
    pdf.set_font("helvetica", "", 8)
    pdf.set_xy(115, y); pdf.cell(40, 4, "Detour Length Around")
    pdf.set_xy(115, y+4); pdf.cell(40, 4, "Structure")
    pdf.set_xy(155, y+4)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(30, 4, fetch(f'p1_detour_{fid}'), border='B', align="C")
    pdf.set_font("helvetica", "", 8)
    pdf.cell(10, 4, "(km)", border=0)

    y += 10
    pdf.form_line(15, y, "Total Deck Length", fetch(f'p1_deck_len_{fid}'), 30, 25, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(72, y); pdf.cell(10, 5, "(m)")
    pdf.form_line(115, y, "Fill on Structure", fetch(f'p1_fill_{fid}'), 30, 35, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(182, y); pdf.cell(10, 5, "(m)")

    y += 8
    pdf.form_line(15, y, "Overall Str. Width", fetch(f'p1_str_width_{fid}'), 30, 25, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(72, y); pdf.cell(10, 5, "(m)")
    pdf.form_line(115, y, "Skew Angle", fetch(f'p1_skew_{fid}'), 30, 35, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(182, y); pdf.cell(15, 5, "(Deg.)")

    y += 8
    pdf.form_line(15, y, "Total Deck Area", fetch(f'p1_deck_area_{fid}'), 30, 25, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(72, y); pdf.cell(10, 5, "(m2)")
    pdf.form_line(115, y, "Direction", fetch('p1_dir_sel'), 30, 35, "C")

    y += 8
    pdf.form_line(15, y, "Roadway Width", fetch(f'p1_road_width_{fid}'), 30, 25, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(72, y); pdf.cell(10, 5, "(m)")
    pdf.form_line(115, y, "No. of Spans", fetch(f'p1_spans_{fid}'), 30, 35, "C")

    # Historical Data Box
    pdf.rect(10, 160, 195, 80, 'D')
    pdf.rect(10, 160, 195, 8, 'FD')
    pdf.set_xy(12, 162)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(100, 4, "HISTORICAL DATA", border=0)

    y = 173
    pdf.form_line(15, y, "Year Built", fetch(f'p1_yr_built_{fid}'), 35, 35, "C")
    pdf.form_line(110, y, "Last OSIM Insp.", fetch(f'p1_last_osim_{fid}'), 40, 45, "C")
    y += 8
    pdf.form_line(15, y, "Last Major Rehab.", fetch(f'p1_yr_rehab_{fid}'), 35, 35, "C")
    pdf.form_line(110, y, "Last Enh. OSIM", fetch(f'p1_last_eosim_{fid}'), 40, 45, "C")
    y += 8
    pdf.form_line(15, y, "Current Load Limit", fetch(f'p1_load_limit_{fid}'), 35, 35, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(87, y); pdf.cell(10, 5, "(tonnes)")
    pdf.form_line(110, y, "Last Bridge Master", fetch(f'p1_last_bmaster_{fid}'), 40, 45, "C")
    y += 8
    pdf.form_line(15, y, "Load Limit By-Law #", fetch(f'p1_bylaw_num_{fid}'), 35, 35, "C")
    pdf.form_line(110, y, "Last Evaluation", fetch(f'p1_last_eval_{fid}'), 40, 45, "C")
    y += 8
    pdf.form_line(15, y, "By-Law Expiry", fetch(f'p1_bylaw_exp_{fid}'), 35, 35, "C")
    pdf.form_line(110, y, "Last Underwater", fetch(f'p1_last_under_{fid}'), 40, 45, "C")
    y += 8
    pdf.form_line(15, y, "Min. Vert. Clearance", fetch(f'p1_vert_clear_{fid}'), 35, 35, "C")
    pdf.set_font("helvetica", "", 8); pdf.set_xy(87, y); pdf.cell(10, 5, "(m)")
    pdf.form_line(110, y, "Last Condition Survey", fetch(f'p1_last_cond_{fid}'), 40, 45, "C")
    
    pdf.line(10, y+8, 205, y+8)
    pdf.set_xy(12, y+10)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(100, 4, "Rehabilitation History: (Date / Description)", border=0)
    pdf.set_xy(12, y+15)
    pdf.set_font("helvetica", "", 8)
    pdf.multi_cell(190, 4, fetch_multiline(f'p1_rehab_hist_{fid}', ''), border=0)


    # ==========================================
    # PAGE 4: EXACT FIELD INSPECTION REPLICA
    # ==========================================
    pdf.add_page(orientation="P")
    
    pdf.set_font("helvetica", "", 9)
    pdf.cell(100, 6, str_class, border=0, align="L")
    pdf.cell(95, 6, f"Site No.: {fetch(f'p1_site_no_{fid}')}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_fill_color(220, 220, 220)
    pdf.rect(10, 20, 195, 40, 'D')
    pdf.rect(10, 20, 195, 8, 'FD')
    pdf.set_xy(12, 22)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(100, 4, "FIELD INSPECTION INFORMATION", border=0)

    y = 30
    pdf.form_line(15, y, "Date of Inspection:", fetch(f'p2_date_{fid}'), 35, 65)
    pdf.set_xy(118, y)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(25, 5, "Type of Inspection:")
    insp_t = fetch(f'p2_insp_type_{fid}')
    pdf.draw_checkbox(145, y+1, "OSIM", "OSIM" in insp_t and "Enhanced" not in insp_t)
    pdf.draw_checkbox(160, y+1, "Enhanced OSIM", "Enhanced" in insp_t)
    
    y += 7
    pdf.form_line(15, y, "Inspector:", fetch(f'p2_inspector_{fid}'), 35, 140)
    y += 7
    pdf.form_line(15, y, "Others in Party:", fetch(f'p2_others_{fid}'), 35, 140)
    y += 7
    pdf.form_line(15, y, "Access Equipment:", fetch('p2_equip_sel'), 35, 140)
    y += 7
    pdf.form_line(15, y, "Weather:", fetch('p2_weather_sel'), 35, 140)
    y += 7
    pdf.form_line(15, y, "Temperature:", fetch(f'p2_temp_{fid}', "") + "°C", 35, 140)

    y = 65
    pdf.rect(10, y, 195, 105, 'D')
    pdf.rect(10, y, 140, 10, 'FD')
    pdf.set_xy(12, y+3)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(100, 4, "ADDITIONAL INVESTIGATION REQUIRED", border=0)
    
    pdf.set_font("helvetica", "", 8)
    pdf.line(150, y, 150, y+105) 
    pdf.line(180, y, 180, y+105) 
    pdf.line(150, y+5, 180, y+5) 
    
    pdf.set_xy(150, y+1); pdf.cell(30, 4, "Priority", align="C")
    pdf.set_xy(150, y+6); pdf.cell(10, 4, "None", border=1, align="C")
    pdf.set_xy(160, y+6); pdf.cell(10, 4, "Normal", border=1, align="C")
    pdf.set_xy(170, y+6); pdf.cell(10, 4, "Urgent", border=1, align="C")
    pdf.set_xy(180, y+3); pdf.cell(25, 4, "Estimated Cost", align="C")
    
    inv_labels = [
        "Rehabilitation/Replacement Study:", "Material Condition Survey", 
        "   Detailed Deck Condition Survey:", "   Non-destructive Delamination Survey:",
        "   Concrete Substructure Condition Survey:", "   Detailed Coating Condition Survey:",
        "   Detailed Timber Investigation:", "Underwater Investigation:", "Fatigue Investigation:",
        "Seismic Investigation:", "Structure Evaluation:", "Monitoring",
        "   Monitoring of Deformations/Movement:", "   Monitoring Crack Widths:"
    ]
    
    curr_y = y + 10
    pdf.set_font("helvetica", "", 8)
    for idx, label in enumerate(inv_labels):
        pdf.set_xy(10, curr_y)
        pdf.cell(140, 6, label, border=1)
        prio = fetch(f'inv_prio_{idx}_{fid}', 'None')
        n_x = "X" if prio == "None" else ""
        nor_x = "X" if prio == "Normal" else ""
        u_x = "X" if prio == "Urgent" else ""
        
        if "Survey" in label and ":" not in label or label == "Monitoring":
            n_x, nor_x, u_x = "", "", ""
            
        pdf.set_xy(150, curr_y); pdf.cell(10, 6, n_x, border=1, align="C")
        pdf.set_xy(160, curr_y); pdf.cell(10, 6, nor_x, border=1, align="C")
        pdf.set_xy(170, curr_y); pdf.cell(10, 6, u_x, border=1, align="C")
        
        cost = fetch(f'inv_cost_{idx}_{fid}', '0.00')
        cost_str = f"$ {cost}" if float(safe_float(cost)) > 0 else "$ -"
        if "Survey" in label and ":" not in label or label == "Monitoring": cost_str = ""
        
        pdf.set_xy(180, curr_y); pdf.cell(25, 6, cost_str, border=1, align="R")
        curr_y += 6

    pdf.set_xy(10, curr_y)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(140, 6, "Load Posting - Estimated Load Limit", border=1)
    pdf.cell(30, 6, "Total Cost", border=1, align="R")
    pdf.cell(25, 6, f"$ {fetch('total_inv_cost', '0.00')}", border=1, align="R")
    
    curr_y += 6
    pdf.set_xy(10, curr_y)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(30, 5, "Investigation Notes:", border=0)
    pdf.set_font("helvetica", "", 8)
    pdf.set_xy(40, curr_y)
    pdf.multi_cell(160, 5, fetch_multiline(f'p2_inv_notes_area_{fid}', ''), border=0)

    curr_y += 15
    pdf.rect(10, curr_y, 195, 60, 'D')
    pdf.rect(10, curr_y, 195, 8, 'FD')
    pdf.set_xy(12, curr_y+2)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(100, 4, "OVERALL STRUCTURAL NOTES:", border=0)
    
    curr_y += 8
    pdf.set_xy(10, curr_y)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(60, 6, "Recommended Work on Structure:", border=1)
    rec_w = fetch(f'p2_rec_work_global_{fid}')
    pdf.draw_checkbox(75, curr_y+1, "None", "None" in rec_w)
    pdf.draw_checkbox(95, curr_y+1, "Minor Rehab.", "Minor Rehab" in rec_w)
    pdf.draw_checkbox(125, curr_y+1, "Major Rehab.", "Major Rehab" in rec_w)
    pdf.draw_checkbox(155, curr_y+1, "Replace", "Replace" in rec_w)
    pdf.line(70, curr_y, 70, curr_y+6)
    
    curr_y += 6
    pdf.set_xy(10, curr_y)
    pdf.cell(60, 6, "Timing of Recommended Work:", border=1)
    rec_t = fetch(f'p2_rec_time_global_{fid}')
    pdf.draw_checkbox(75, curr_y+1, "1 to 5 years", "1 to 5" in rec_t)
    pdf.draw_checkbox(105, curr_y+1, "6 to 10 years", "6 to 10" in rec_t)
    pdf.line(70, curr_y, 70, curr_y+6)
    
    curr_y += 6
    pdf.set_xy(12, curr_y+1)
    pdf.multi_cell(191, 4, fetch_multiline(f'p2_overall_comm_{fid}', ''), border=0)
    
    curr_y += 34
    pdf.set_xy(10, curr_y)
    pdf.line(10, curr_y, 205, curr_y)
    pdf.cell(60, 6, "Date of Next Inspection:", border=0)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(135, 6, fetch(f'p2_next_insp_{fid}'), border=0)


    # ==========================================
    # PAGES 5+: COMPACT ELEMENT DATA SHEETS
    # ==========================================
    pdf.set_auto_page_break(auto=False)
    elements = st.session_state.get('report_elements', [])
    
    if elements:
        pdf.add_page(orientation="P") 
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, "ELEMENT DATA", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for el in elements:
            if pdf.get_y() > 195:
                pdf.add_page(orientation="P")
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "ELEMENT DATA (Cont.)", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)

            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Element Group:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, sanitize_text(el.get('group', '')), border=1)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Length:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, f"{safe_float(el.get('L'))}m", border=1, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Element Name:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, sanitize_text(el.get('name', '')), border=1)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Width:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, f"{safe_float(el.get('W'))}m", border=1, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Location:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, sanitize_text(el.get('loc', '')), border=1)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Height:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, f"{safe_float(el.get('H'))}m", border=1, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Material:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, sanitize_text(el.get('mat', '')), border=1)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Count:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, f"{safe_float(el.get('C'))}", border=1, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Element Type:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, sanitize_text(el.get('typ', '')), border=1)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Total Quantity:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, f"{safe_float(el.get('Total')):,.2f} {sanitize_text(el.get('unit', ''))}", border=1, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Environment:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(62.5, 5, sanitize_text(el.get('env', '')), border=1)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Limited Inspection:", border=1, fill=True)
            curr_x, curr_y = pdf.get_x(), pdf.get_y()
            pdf.cell(62.5, 5, "", border=1, new_x="LMARGIN", new_y="NEXT")
            pdf.draw_checkbox(curr_x + 5, curr_y + 0.5, "", el.get('limit_insp'))

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 5, "Protection System:", border=1, fill=True)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(160, 5, sanitize_text(el.get('pro', '')), border=1, new_x="LMARGIN", new_y="NEXT")

            c_y = pdf.get_y()
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(35, 10, "Condition Data:", border=1, fill=True)
            w_col = 160 / 5
            
            pdf.set_xy(45, c_y)
            pdf.cell(w_col, 5, "Units", border=1, align="C", fill=True)
            pdf.cell(w_col, 5, "Excellent", border=1, align="C", fill=True)
            pdf.cell(w_col, 5, "Good", border=1, align="C", fill=True)
            pdf.cell(w_col, 5, "Fair", border=1, align="C", fill=True)
            pdf.cell(w_col, 5, "Poor", border=1, align="C", fill=True)
            
            pdf.set_xy(45, c_y + 5)
            pdf.set_font("helvetica", "", 8)
            pdf.cell(w_col, 5, sanitize_text(el.get('unit', '')), border=1, align="C")
            pdf.cell(w_col, 5, f"{safe_float(el.get('exc')):,.2f}", border=1, align="C")
            pdf.cell(w_col, 5, f"{safe_float(el.get('good')):,.2f}", border=1, align="C")
            pdf.cell(w_col, 5, f"{safe_float(el.get('fair')):,.2f}", border=1, align="C")
            pdf.cell(w_col, 5, f"{safe_float(el.get('poor')):,.2f}", border=1, align="C")
            pdf.set_y(c_y + 10)

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(195, 6, "Comments:", border="LRT", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 8)
            cm_y = pdf.get_y()
            pdf.rect(10, cm_y, 195, 20, 'D')
            pdf.set_xy(12, cm_y + 1)
            pdf.multi_cell(191, 4, fetch_multiline(f"com_{el['uid']}", el.get('comments', '')), border=0)
            pdf.set_y(cm_y + 20)

            pdf.set_font("helvetica", "B", 8)
            pdf.cell(97.5, 6, f"Performance Deficiencies: {sanitize_text(el.get('perf_def', '00 None'))[:40]}", border=1)
            pdf.cell(97.5, 6, f"Maintenance Needs: {sanitize_text(el.get('maint_need', '00 None'))[:40]}", border=1, new_x="LMARGIN", new_y="NEXT")

            act_y = pdf.get_y()
            pdf.rect(10, act_y, 97.5, 12, 'D')
            pdf.rect(107.5, act_y, 97.5, 12, 'D')
            
            pdf.set_xy(12, act_y + 2)
            pdf.cell(30, 4, "Recommended Work:")
            act = el.get('rec_action')
            tim = el.get('rec_time')
            pdf.draw_checkbox(45, act_y + 1.5, "Rehab.", act == "Rehabilitate")
            pdf.draw_checkbox(75, act_y + 1.5, "Replace", act == "Replace")
            pdf.draw_checkbox(45, act_y + 6.5, "1 - 5 Years", tim == "1 - 5 Years")
            pdf.draw_checkbox(75, act_y + 6.5, "6 - 10 Years", tim == "6 - 10 Years")

            pdf.set_xy(109.5, act_y + 2)
            pdf.cell(30, 4, "Maintenance Needs:")
            mtim = el.get('mnt_time')
            pdf.draw_checkbox(140, act_y + 1.5, "Urgent", mtim == "Urgent")
            pdf.draw_checkbox(160, act_y + 1.5, "1 Year", mtim == "1 Year")
            pdf.draw_checkbox(180, act_y + 1.5, "2 Years", mtim == "2 Years")

            pdf.set_y(act_y + 16) 

    pdf.output(filepath)
    return filepath