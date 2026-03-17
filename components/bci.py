import streamlit as st
import pandas as pd

def show_bci():
    st.subheader("🔢 Bridge Condition Index (BCI) Calculator")
    st.info("This module automatically calculates the BCI by mathematically analyzing the Element Condition States generated in Master Report Page 3.")

    if 'report_elements' not in st.session_state or len(st.session_state.report_elements) == 0:
        st.warning("⚠️ No elements found in Master Report Page 3. Add elements there first to see calculations here.")
        return

    elements = st.session_state.report_elements

    # Ensure the key exists to avoid 0.00 render bugs
    if 'cp_bci_score' not in st.session_state:
        st.session_state['cp_bci_score'] = 0.0

    # --- THE MATH ENGINE (RESTORED) ---
    if st.button("🔄 Calculate BCI from Master Report Elements", type="primary", use_container_width=True):
        total_eci = 0.0
        valid_elements = 0
        table_data = []

        for el in elements:
            exc = float(el.get('exc') or 0.0)
            good = float(el.get('good') or 0.0)
            fair = float(el.get('fair') or 0.0)
            poor = float(el.get('poor') or 0.0)
            tot = float(el.get('Total') or 0.0)

            # OSIM Math Formula
            if tot > 0:
                eci = ((exc * 100) + (good * 75) + (fair * 50) + (poor * 25)) / tot
                total_eci += eci
                valid_elements += 1
            else:
                eci = 0.0

            # Restored EXACT OSIM Columns Format
            table_data.append({
                "Element Group": el.get('group', ''),
                "Element Name": el.get('name', ''),
                "Quantity": round(tot, 2),
                "Units": el.get('unit', 'm²'),
                "Exc": round(exc, 2), 
                "Good": round(good, 2), 
                "Fair": round(fair, 2), 
                "Poor": round(poor, 2),
                "ECI": round(eci, 2)
            })

        st.session_state['bci_table_data'] = table_data

        final_bci = (total_eci / valid_elements) if valid_elements > 0 else 0.0
        st.session_state['cp_bci_score'] = round(final_bci, 2)
        st.rerun()

    st.divider()
    
    # --- VISUAL DISPLAY & MANUAL OVERRIDE ---
    # Memory function to update Cover Page instantly if manually overridden here
    def update_bci_override():
        st.session_state['cp_bci_score'] = st.session_state['bci_widget_key']

    current_bci = float(st.session_state.get('cp_bci_score', 0.0))

    if current_bci < 60: rating, p_color = "POOR", "#ef4444" 
    elif current_bci <= 75: rating, p_color = "FAIR", "#f59e0b" 
    else: rating, p_color = "GOOD", "#10b981" 

    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.markdown("### Final System BCI")
        st.number_input(
            "Overall BCI Score (0-100)", 
            min_value=0.0, max_value=100.0, 
            value=current_bci, step=0.1, 
            key="bci_widget_key",
            on_change=update_bci_override,
            help="This value automatically pushes to your Cover Page."
        )
        st.markdown(f"<h2 style='color:{p_color};'>Rating: {rating}</h2>", unsafe_allow_html=True)

    with c2:
        st.markdown("### BCI Condition Visualizer")
        st.write("")
        pct = min(max(int(current_bci), 0), 100)
        st.markdown(f"""
            <div style="width: 100%; background-color: #334155; border-radius: 10px; height: 30px; margin-top: 10px;">
              <div style="width: {pct}%; background-color: {p_color}; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:5px; font-weight:bold; color:#cbd5e1;">
                <span>0 (Poor)</span>
                <span>60 (Fair)</span>
                <span>75 (Good)</span>
                <span>100</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- ELEMENT BREAKDOWN TABLE ---
    if 'bci_table_data' in st.session_state and st.session_state['bci_table_data']:
        st.markdown("### Individual Element Condition Index (ECI) Breakdown")
        df = pd.DataFrame(st.session_state['bci_table_data'])
        st.dataframe(df, use_container_width=True, hide_index=True)