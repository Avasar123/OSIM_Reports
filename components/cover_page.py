import streamlit as st
import datetime

def show_cover_page():
    st.subheader("📑 Final Cover Page Summary")
    st.info("Click the button below to instantly pull all data from your Master Report into this final grid.")

    # --- THE SYNC ENGINE ---
    if st.button("🔄 Sync with Master Report", type="primary", use_container_width=True):
        fid = st.session_state.get('form_id', 'init')
        
        # Basic Info
        st.session_state['cp_str_name'] = st.session_state.get(f'p1_str_name_{fid}', '')
        st.session_state['cp_site_id'] = st.session_state.get(f'p1_site_no_{fid}', '')
        st.session_state['cp_location'] = st.session_state.get(f'p1_location_{fid}', '')
        st.session_state['cp_owner'] = st.session_state.get(f'p1_owner_{fid}', '')
        st.session_state['cp_year_built'] = st.session_state.get(f'p1_yr_built_{fid}', '')
        st.session_state['cp_str_type'] = st.session_state.get(f'p1_type_{fid}', '')
        st.session_state['cp_road_name'] = st.session_state.get(f'p1_road_name_{fid}', '')
        st.session_state['cp_bridge_or_culvert'] = st.session_state.get(f'p1_class_sel', '')
        st.session_state['cp_load_posting'] = st.session_state.get(f'p2_load_post_{fid}', '')
        
        st.session_state['cp_lat'] = st.session_state.get(f'p1_lat_{fid}', '')
        st.session_state['cp_lon'] = st.session_state.get(f'p1_lon_{fid}', '')
        st.session_state['cp_orient'] = st.session_state.get('p1_dir_sel', '')

        # Geometry
        st.session_state['cp_length'] = float(st.session_state.get(f'p1_deck_len_{fid}', 0.0))
        st.session_state['cp_width'] = float(st.session_state.get(f'p1_str_width_{fid}', 0.0))
        st.session_state['cp_road_width'] = float(st.session_state.get(f'p1_road_width_{fid}', 0.0))
        st.session_state['cp_deck_area'] = float(st.session_state.get(f'p1_deck_area_{fid}', 0.0))
        st.session_state['cp_spans'] = int(st.session_state.get(f'p1_spans_{fid}', 1))
        st.session_state['cp_skew'] = int(st.session_state.get(f'p1_skew_{fid}', 0))
        st.session_state['cp_aadt'] = int(st.session_state.get(f'p1_aadt_{fid}', 0))
        st.session_state['cp_lanes'] = int(st.session_state.get(f'p1_lanes_{fid}', 2))
        st.session_state['cp_trucks'] = float(st.session_state.get(f'p1_trucks_{fid}', 0.0))
        st.session_state['cp_speed'] = int(st.session_state.get(f'p1_speed_{fid}', 0))

        # Inspection Data (Merging Inspector and Others in Party)
        st.session_state['cp_insp_date'] = st.session_state.get(f'p2_date_{fid}', datetime.date.today())
        st.session_state['cp_insp_type'] = st.session_state.get(f'p2_insp_type_{fid}', 'OSIM')
        
        insp = st.session_state.get(f'p2_inspector_{fid}', '')
        others = st.session_state.get(f'p2_others_{fid}', '')
        if others:
            st.session_state['cp_inspector'] = f"{insp} (Others: {others})" if insp else f"Others: {others}"
        else:
            st.session_state['cp_inspector'] = insp

        # Overall Findings
        st.session_state['cp_findings'] = st.session_state.get(f'p2_overall_comm_{fid}', '')
        st.session_state['cp_imm_interv'] = st.session_state.get('rep_p5_imm_interv_dd_sel', 'None')
        
        # --- Helper logic to pull items AND their notes ---
        def get_list_with_notes(prefix):
            row_ids = st.session_state.get(f'{prefix}_rows', [])
            result = []
            for r in row_ids:
                sel = st.session_state.get(f"{prefix}_sel_{r}", "")
                note = st.session_state.get(f"{prefix}_note_{r}", "")
                if sel and sel != "None":
                    line = f"• {sel}"
                    if note:
                        line += f" (Notes: {note})"
                    result.append(line)
            return "\n".join(result)

        # Investigations (Combining dynamic rows + Page 2 General Notes)
        inv_list_str = get_list_with_notes("rep_inv")
        p2_inv_notes = st.session_state.get(f'p2_inv_notes_area_{fid}', '')
        if p2_inv_notes:
            if inv_list_str:
                st.session_state['cp_add_inv'] = f"{inv_list_str}\nGeneral Notes: {p2_inv_notes}"
            else:
                st.session_state['cp_add_inv'] = f"General Notes: {p2_inv_notes}"
        else:
            st.session_state['cp_add_inv'] = inv_list_str

        # Recommended Work (Combining Overall + Specific Rows + Notes)
        rw_list_str = get_list_with_notes("rep_rw")
        overall_rw = st.session_state.get('rep_p5_overall_rw_sel', '')
        overall_note = st.session_state.get('rep_p5_overall_rw_notes', '')
        
        if overall_rw and overall_rw != "None":
            rw_top = f"OVERALL: {overall_rw}"
            if overall_note:
                rw_top += f" (Notes: {overall_note})"
            if rw_list_str:
                st.session_state['cp_rec_work'] = f"{rw_top}\n{rw_list_str}"
            else:
                st.session_state['cp_rec_work'] = rw_top
        else:
            st.session_state['cp_rec_work'] = rw_list_str

        # Maintenance, Deficiencies, Barriers
        st.session_state['cp_maint_needs'] = get_list_with_notes("rep_pm")
        st.session_state['cp_deficiencies'] = get_list_with_notes("rep_cd")
        st.session_state['cp_barriers'] = get_list_with_notes("rep_bar")

        # Costs
        st.session_state['cp_est_rep_cost'] = float(st.session_state.get('rep_est_replacement', 0.0))
        st.session_state['cp_est_rw_cost'] = float(st.session_state.get('rep_est_rec_work', 0.0))
        
        st.toast("✅ Cover Page Synced with Master Report!", icon="🔄")
        st.rerun()

    st.divider()

    # --- COVER PAGE GRID UI ---
    st.markdown("<h3 style='text-align: center;'>STRUCTURE SUMMARY</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        c1, c2 = st.columns([6, 4])
        
        with c1:
            st.text_input("Structure Name", key="cp_str_name")
            st.text_input("Road Name", key="cp_road_name")
            st.text_input("Bridge or Culvert", key="cp_bridge_or_culvert")
            st.text_input("Site ID", key="cp_site_id")
            st.text_input("Location", key="cp_location")
            st.text_input("Owner", key="cp_owner")
            st.text_input("Structure Type", key="cp_str_type")
            st.number_input("No. of Spans/Cells", min_value=1, step=1, key="cp_spans")
            st.text_input("Year Built", key="cp_year_built")
            st.text_input("Load Posting", key="cp_load_posting")
            
        with c2:
            st.markdown("**Cover Photo**")
            st.file_uploader("Upload Structure Image", type=["jpg", "png", "jpeg"], key="cp_image_upload", label_visibility="collapsed")
            if st.session_state.get("cp_image_upload"):
                st.image(st.session_state["cp_image_upload"], use_container_width=True)

    with st.container(border=True):
        col_dim1, col_dim2, col_dim3 = st.columns(3)
        with col_dim1:
            st.number_input("Length (m)", step=0.1, key="cp_length")
            st.number_input("Width (m)", step=0.1, key="cp_width")
            st.number_input("Roadway Width (m)", step=0.1, key="cp_road_width")
            st.number_input("Deck Area (m²)", step=0.1, key="cp_deck_area")
        with col_dim2:
            st.number_input("AADT", step=100, key="cp_aadt")
            st.number_input("No. of Lanes", step=1, key="cp_lanes")
            st.number_input("Posted Speed (km/h)", step=10, key="cp_speed")
            st.number_input("Trucks (%)", step=0.1, key="cp_trucks")
        with col_dim3:
            st.text_input("Latitude", key="cp_lat")
            st.text_input("Longitude", key="cp_lon")
            st.text_input("Orientation", key="cp_orient")
            st.number_input("Skew (deg)", step=1, key="cp_skew")
            
    with st.container(border=True):
        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.date_input("Inspection Date", key="cp_insp_date")
        col_i2.text_input("Inspector(s) & Others", key="cp_inspector")
        col_i3.text_input("Type of Inspection", key="cp_insp_type")
        
    with st.container(border=True):
        bci_val = float(st.session_state.get('cp_bci_score', 0.0))
        if bci_val < 60: rating, color = "POOR", "red"
        elif bci_val <= 75: rating, color = "FAIR", "orange"
        else: rating, color = "GOOD", "green"
            
        cbci1, cbci2 = st.columns([1, 1])
        cbci1.metric("Bridge Condition Index (BCI)", f"{bci_val:.2f}")
        cbci2.markdown(f"<h3 style='text-align:center; padding-top:10px; color:{color};'>CONDITION RATING: {rating}</h3>", unsafe_allow_html=True)
        
    with st.container(border=True):
        st.markdown("### SIGNIFICANT FINDINGS")
        st.text_area("Findings", key="cp_findings", label_visibility="collapsed", height=150)

    with st.container(border=True):
        st.markdown("### ACTION PLAN")
        st.text_input("Immediate Intervention Required", key="cp_imm_interv")
        
        ca1, ca2 = st.columns(2)
        with ca1:
            st.markdown("**Additional Investigations**")
            st.text_area("Investigations", key="cp_add_inv", label_visibility="collapsed", height=100)
            st.markdown("**Recommended Work**")
            st.text_area("Rec Work", key="cp_rec_work", label_visibility="collapsed", height=100)
            
            st.number_input("Estimated Replacement Costs ($)", step=1000.0, key="cp_est_rep_cost")
            
        with ca2:
            st.markdown("**Principal Maintenance Needs**")
            st.text_area("Maintenance", key="cp_maint_needs", label_visibility="collapsed", height=100)
            st.markdown("**Common Deficiencies**")
            st.text_area("Deficiencies", key="cp_deficiencies", label_visibility="collapsed", height=100)
            
            st.number_input("Estimate of Rec. Work Costs ($)", step=1000.0, key="cp_est_rw_cost")

    with st.container(border=True):
        st.markdown("**Approach/Bridge Barriers**")
        st.text_area("Barriers", key="cp_barriers", label_visibility="collapsed", height=80)