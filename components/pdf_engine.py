from fpdf import FPDF
import streamlit as st
import os
from datetime import date, datetime

class OSIM_Report(FPDF):
    def header(self):
        # MTO Header Style
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "MUNICIPAL STRUCTURE INSPECTION FORM", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        # Page Numbers
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="R")

def create_pdf(filename="OSIM_Report.pdf"):
    """Generates a professional, grid-based PDF pulling from session state."""
    pdf = OSIM_Report()
    pdf.add_page()
    
    # --- HELPER DATA PULLS ---
    # Prioritize Cover Page data (cp_), fallback to Report data (p1_, p2_) if empty
    def get_val(cp_key, p_key="", default=""):
        val = st.session_state.get(cp_key, st.session_state.get(p_key, default))
        if isinstance(val, (date, datetime)):
            return val.strftime("%Y-%m-%d")
        if val is None:
            return ""
        return str(val)
        
    def get_list_val(list_key):
        items = st.session_state.get(list_key, [])
        if isinstance(items, list) and len(items) > 0:
            return ", ".join([str(i.get('val', i)) for i in items if isinstance(i, dict) and i.get('val') != ""])
        return str(items) if items else "None"

    # Basic Info
    site_no = get_val('cp_site_id', 'p1_site_no')
    str_name = get_val('cp_struct_name', 'p1_str_name')
    str_type = get_val('t', 'p1_type') # from editable dropdowns
    insp_date = get_val('cp_insp_date', 'p2_date')
    
    # Exec Summary Info (Page 5 style)
    imm_interv = get_val('p5_imm_interv_dd', default="None")
    inv_opts = get_list_val('p5_investigations')
    inv_notes = get_val('p5_inv_notes_dd')
    rec_work = get_list_val('p5_rec_work')
    rec_notes = get_val('p5_rec_notes_dd')
    
    # Costs
    cost_rep = st.session_state.get('p5_rep_cost', st.session_state.get('cp_est_replacement', 0.0))
    cost_work = st.session_state.get('p5_rec_work_cost', st.session_state.get('cp_est_rec_work', 0.0))
    
    maint_needs = get_list_val('p5_maint_needs')
    maint_notes = get_val('p5_maint_notes_dd')
    deficiencies = get_list_val('p5_deficiencies')
    def_notes = get_val('p5_def_notes_dd')
    barriers = get_val('p5_barriers_dd', default="Conforming barriers and end treatments present")
    bar_notes = get_val('p5_barrier_notes_dd')

    # --- START DRAWING PDF GRIDS ---
    
    # Grid Settings
    line_h = 8 # Standard row height
    grey = (230, 230, 230)
    pdf.set_draw_color(0, 0, 0)
    
    # 1. Basic Info Block
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(*grey)
    pdf.cell(0, 8, "1. Basic Identification", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, line_h, "Structure Name:", border=1)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(55, line_h, str_name, border=1)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, line_h, "Site No:", border=1)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(55, line_h, site_no, border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, line_h, "Structure Type:", border=1)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(55, line_h, str_type, border=1)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, line_h, "Inspection Date:", border=1)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(55, line_h, insp_date, border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5) # Space

    # 2. Executive Summary Block (Matches Image 35.PNG Layout)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(*grey)
    pdf.cell(0, 8, "Executive Summary & Recommendations", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 9)
    
    # Row: Immediate Intervention
    # X/Y capturing to draw multi-line cells perfectly
    pdf.multi_cell(50, 16, "Immediate Intervention\nRequired", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(140, 16, imm_interv, border=1, new_x="LMARGIN", new_y="NEXT")

    # Row: Additional Investigations
    pdf.set_fill_color(*grey)
    pdf.multi_cell(50, 16, "Additional\nInvestigations:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(70, 16, inv_opts[:80] + "..." if len(inv_opts)>80 else inv_opts, border=1, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, "Investigation\nNotes:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, inv_notes[:40], border=1, new_x="LMARGIN", new_y="NEXT")

    # Row: Recommended Work
    pdf.multi_cell(50, 16, "Recommended Work:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(70, 16, rec_work[:80] + "..." if len(rec_work)>80 else rec_work, border=1, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, "Recommended\nWork Notes:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, rec_notes[:40], border=1, new_x="LMARGIN", new_y="NEXT")

    # Row: Costs
    pdf.multi_cell(50, 16, "Estimated Replacement\nCosts", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(70, 16, f"${float(cost_rep):,.2f}", border=1, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, "Estimate of\nRec. Work Costs", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, f"${float(cost_work):,.2f}", border=1, new_x="LMARGIN", new_y="NEXT")

    # Row: Maintenance Needs
    pdf.multi_cell(50, 16, "Principal Maintenance\nNeeds:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(70, 16, maint_needs[:80], border=1, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, "Principal\nMaintenance Notes:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, maint_notes[:40], border=1, new_x="LMARGIN", new_y="NEXT")

    # Row: Deficiencies
    pdf.multi_cell(50, 16, "Common Deficiencies\nWarranting Short Term\nIntervention:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(70, 16, deficiencies[:80], border=1, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, "Common\nDeficiency Notes:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, def_notes[:40], border=1, new_x="LMARGIN", new_y="NEXT")

    # Row: Barriers
    pdf.multi_cell(50, 16, "Approach/Bridge\nBarriers:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(70, 16, barriers[:80], border=1, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, "Barrier Notes:", border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.multi_cell(35, 16, bar_notes[:40], border=1, new_x="LMARGIN", new_y="NEXT")
    
    # --- OUTPUT ---
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    file_path = os.path.join(export_dir, filename)
    pdf.output(file_path)
    
    return file_path