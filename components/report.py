"""
OSIM REPORT MODULE
==============================================================================
This module handles the core data entry for the Municipal Structure Inspection.
It strictly follows the OSIM (Ontario Structure Inspection Manual) guidelines.
It manages Page 1 (Inventory), Page 2 (Field Notes), Page 3 (Element Data),
Page 4 (Repair Required), and Page 5 (Executive Summary).
All states are managed via Streamlit session_state to ensure persistent editing.
"""

import streamlit as st
import json
import os
import uuid
import datetime

# ============================================================================
# --- 1. UNIVERSAL MEMORY FUNCTIONS ---
# ============================================================================

def load_list(filename, default_list):
    """
    Loads a saved JSON list for dropdown options. 
    If the file does not exist, it falls back to the default OSIM list provided.
    
    Args:
        filename (str): The name of the JSON file to load (e.g., 'class.json').
        default_list (list): The list to use if the file is missing.
        
    Returns:
        list: The loaded or default list.
    """
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default_list

def save_list(filename, data_list):
    """
    Saves a customized list back to a JSON file.
    This ensures that when a user adds a new custom dropdown item, it survives
    page refreshes and system reloads.
    
    Args:
        filename (str): The destination JSON file.
        data_list (list): The list of strings to be saved.
    """
    with open(filename, "w") as f:
        json.dump(data_list, f)

# ============================================================================
# --- 2. BULLETPROOF UI HELPERS ---
# ============================================================================

def editable_dropdown_small(label, session_list, filename, key_prefix):
    """
    Creates a dynamic selectbox that allows the user to add or delete options 
    on the fly. It utilizes a popover (gear icon) for management.
    
    Crucially, it checks if a loaded JSON state value exists but isn't in the list,
    and forces it into the list so Streamlit doesn't accidentally delete saved data.
    """
    curr_val = st.session_state.get(f"{key_prefix}_sel")
    if curr_val and curr_val not in session_list:
        session_list.append(curr_val)
        save_list(filename, session_list)

    left, right = st.columns([8, 1])
    with left:
        selected = st.selectbox(
            label=label, 
            options=session_list, 
            label_visibility="collapsed", 
            key=f"{key_prefix}_sel"
        )
    with right:
        with st.popover("⚙️"):
            new_item = st.text_input("Add New", key=f"{key_prefix}_new")
            if st.button("Add", key=f"{key_prefix}_add"):
                if new_item and new_item not in session_list:
                    session_list.append(new_item)
                    save_list(filename, session_list)
                    st.rerun()
            to_del = st.selectbox("Remove", options=session_list, key=f"{key_prefix}_del_sel")
            if st.button("Delete", key=f"{key_prefix}_del"):
                if len(session_list) > 1:
                    session_list.remove(to_del)
                    save_list(filename, session_list)
                    st.rerun()
    return selected

def dynamic_summary_row(label, list_opts, file_name, key_pref):
    """
    Generates a dynamic list of rows (Dropdown + Text Note + Delete Button).
    Uses stable integers [1, 2, 3] rather than UUIDs to ensure perfect 
    saving and loading within JSON project files.
    """
    row_key = f"{key_pref}_rows"
    if row_key not in st.session_state:
        st.session_state[row_key] = [1]

    col_lbl, col_add, col_gear = st.columns([17, 3, 1])
    with col_lbl:
        st.write(f"**{label}**")
    with col_add:
        if st.button("➕ Add Row", key=f"{key_pref}_add_row"):
            next_id = max(st.session_state[row_key]) + 1 if st.session_state[row_key] else 1
            st.session_state[row_key].append(next_id)
            st.rerun()
    with col_gear:
        with st.popover("⚙️"):
            st.write("**Manage Dropdown Options**")
            new_item = st.text_input("Add Option", key=f"{key_pref}_new_opt")
            if st.button("Add Option", key=f"{key_pref}_add_opt"):
                if new_item and new_item not in list_opts:
                    list_opts.append(new_item)
                    save_list(file_name, list_opts)
                    st.rerun()
            to_del = st.selectbox("Remove Option", list_opts, key=f"{key_pref}_del_opt")
            if st.button("Delete Option", key=f"{key_pref}_del_btn"):
                if len(list_opts) > 1:
                    list_opts.remove(to_del)
                    save_list(file_name, list_opts)
                    st.rerun()

    selections = []
    notes = []
    
    rows = st.session_state[row_key].copy()
    
    for i, r_id in enumerate(rows):
        c_left, c_right, c_del = st.columns([10, 10, 1])
        with c_left:
            sel = st.selectbox(
                label=f"{label} {i}", 
                options=list_opts, 
                label_visibility="collapsed", 
                key=f"{key_pref}_sel_{r_id}"
            )
            selections.append(sel)
        with c_right:
            note = st.text_input(
                label=f"Notes {i}", 
                key=f"{key_pref}_note_{r_id}", 
                placeholder=f"Type notes here...", 
                label_visibility="collapsed"
            )
            notes.append(note)
        with c_del:
            if st.button("🗑️", key=f"{key_pref}_del_row_{r_id}"):
                if len(st.session_state[row_key]) > 1:
                    st.session_state[row_key].remove(r_id)
                    if f"{key_pref}_sel_{r_id}" in st.session_state: 
                        del st.session_state[f"{key_pref}_sel_{r_id}"]
                    if f"{key_pref}_note_{r_id}" in st.session_state: 
                        del st.session_state[f"{key_pref}_note_{r_id}"]
                    st.rerun()
                else:
                    st.toast("Cannot delete the last row.")
            
    st.write("") 
    return selections, notes

# ============================================================================
# --- 3. MASTER OSIM DICTIONARIES ---
# ============================================================================

MASTER_ELEMENTS = {
    "Approaches": [
        "Barrier", 
        "Sidewalk/Curb", 
        "Curb and Gutters", 
        "Drainage System", 
        "Wearing Surface", 
        "Approach Slabs"
    ],
    "Accessories": [
        "Signs", 
        "Bridge Mounted Sign Supports", 
        "Electrical", 
        "Noise Barriers", 
        "Utilities", 
        "Other"
    ],
    "Barriers": [
        "Barrier/Parapet Walls", 
        "Barrier/Parapet Walls (interior)", 
        "Barrier/Parapet Walls (exterior)", 
        "Railing Systems", 
        "Railing Systems - Timber", 
        "Hand Railings", 
        "Posts (Steel/Concrete)", 
        "Posts - Timber"
    ],
    "Trusses/ Arches": [
        "Top Chords", 
        "Verticals", 
        "Diagonals", 
        "Bottom Chords", 
        "Connections", 
        "Top Chords - Eagle Bridge", 
        "Verticals - Eagle Bridge", 
        "Diagonals - Eagle Bridge", 
        "Bottom Chords - Eagle Bridge", 
        "Connections - Eagle Bridge"
    ],
    "Joints": [
        "Armouring / Retaining Devices", 
        "Concrete End Dams", 
        "Seals/ Sealants"
    ],
    "Sidewalks/ Curbs": [
        "Sidewalks and Medians", 
        "Curbs"
    ],
    "Decks": [
        "Drainage System", 
        "Wearing Surface", 
        "Deck Top - Thin Slab", 
        "Deck Top - Thick Slab", 
        "Deck - Timber", 
        "Soffit-Inside Boxes", 
        "Soffit - Thick Slab", 
        "Soffit - Thin Slab"
    ],
    "Culverts": [
        "Inlet Components", 
        "Outlet Components", 
        "Barrel"
    ],
    "Beams/ Main Longitudinal Elements": [
        "Girders", 
        "Girders -Steel", 
        "Girders - Timber", 
        "Inside Boxes (sides & bottoms)", 
        "Inside Boxes (sides & bottoms) - Steel", 
        "Stringers", 
        "Floor Beams - Concrete", 
        "Floor Beams - Steel", 
        "Diaphrams - Concrete", 
        "Diaphrams - Steel, wood etc."
    ],
    "Bracing": [
        "Bracing - Steel", 
        "Bracing - Timber", 
        "Bracing", 
        "Blocking - Timber"
    ],
    "Coatings": [
        "Railing Systems/ Hand Railing", 
        "Structural steel"
    ],
    "Abutments": [
        "Wingwalls", 
        "Wingwalls - Gabion Baskets", 
        "Ballast Walls", 
        "Bearings", 
        "Abutment Walls", 
        "Abutment Walls - Gabion Baskets"
    ],
    "Piers": [
        "Bearings", 
        "Caps", 
        "Caps - Timber", 
        "Shafts/ Columns/ Pier Bents", 
        "Columns - Timber"
    ],
    "Foundations": [
        "Sonotubes", 
        "Foundations (below ground level)"
    ],
    "Retaining Walls": [
        "Barrier Systems on Walls", 
        "Railing Systems", 
        "Drainage System", 
        "Walls"
    ],
    "Embankments and Streams": [
        "Embankments", 
        "Slope Protection", 
        "Streams and Waterways"
    ]
}

DEFAULT_PD = [
    "00 None", 
    "01 Load carrying capacity", 
    "02 Excessive deformations (deflections & rotation)", 
    "03 Continuing settlement", 
    "04 Continuing movements", 
    "05 Seized bearings", 
    "06 Bearing not uniformly loaded/unstable", 
    "07 Jammed expansion joint", 
    "08 Pedestrian/vehicular hazard", 
    "09 Rough riding surface", 
    "10 Surface ponding", 
    "11 Deck drainage", 
    "12 Slippery surfaces", 
    "13 Flooding/channel blockage", 
    "14 Undermining of foundation", 
    "15 Unstable embankments", 
    "16 Other"
]

DEFAULT_MN = [
    "00 None", 
    "01 Lift and swing bridge maintenance", 
    "02 Bridge cleaning", 
    "03 Bridge handrail maintenance", 
    "04 Painting steel bridge structures", 
    "05 Bridge deck joint repair", 
    "06 Bridge bearing maintenance", 
    "07 Repair of structural steel", 
    "08 Repair of bridge concrete", 
    "09 Repair of bridge timber", 
    "10 Bailey bridges maintenance", 
    "11 Animal/pest control", 
    "12 Bridge surface repair", 
    "13 Erosion control at bridges", 
    "14 Concrete sealing", 
    "15 Rout and seal", 
    "16 Bridge deck drainage", 
    "17 Scaling (loose Concrete or ACR Steel)", 
    "18 Other"
]

INV_LIST_DEF = [
    ("Rehabilitation/Replacement Study", False, ["General", "Barrier Only", "Truss Structure"], [22000.0, 8000.0, 25000.0]),
    ("Material Condition Survey", True, [], []),
    ("Detailed Deck Condition Survey", False, ["Asphalt W/S", "Exposed Deck"], [20000.0, 15000.0]),
    ("Non-destructive Delamination Survey of Asphalt- Covered Deck", False, [], []),
    ("Concrete Substructure Condition Survey", False, [], []),
    ("Detailed Coating Condition Survey", False, [], []),
    ("Detailed Timber Investigation", False, [], []),
    ("Underwater Investigation", False, [], [13000.0]), 
    ("Fatigue Investigation", False, [], []),
    ("Seismic Investigation", False, [], []),
    ("Structure Evaluation", False, ["General", "Truss Structure"], [15000.0, 17500.0]),
    ("Monitoring", True, [], []),
    ("Monitoring of Deformations, Settlement and Movements", False, [], [3500.0]),
    ("Monitoring Crack Widths", False, [], [3500.0])
]

# ============================================================================
# --- 4. MATH & CALCULATION ENGINE ---
# ============================================================================

def safe_float(val):
    """Safely converts a string/None value to a float to prevent calculation crashes."""
    try:
        return float(val) if val is not None else 0.0
    except ValueError:
        return 0.0

def calculate_total_qty(name, L, W, H, C):
    """
    Automated Geometry Engine.
    Determines the total quantity based on the specific Element Name.
    Applies logic for linear (m), area (m2), and discrete (each) variables.
    
    Args:
        name (str): The OSIM element name.
        L (float): Length.
        W (float): Width.
        H (float): Height.
        C (float): Count / Modifier.
        
    Returns:
        float: The calculated total quantity.
    """
    L = safe_float(L)
    W = safe_float(W)
    H = safe_float(H)
    C_val = safe_float(C)
    
    # If Count is provided, it acts as a multiplier for linear/area elements
    C_mult = C_val if C_val > 0 else 1.0

    # Elements measured as "Each" or strictly by Count
    discrete_items = [
        "Signs", 
        "Bridge Mounted Sign Supports", 
        "Electrical", 
        "Utilities", 
        "Other", 
        "Posts (Steel/Concrete)", 
        "Posts - Timber", 
        "Connections", 
        "Connections - Eagle Bridge", 
        "Seals/ Sealants", 
        "Drainage System", 
        "Stringers", 
        "Bracing", 
        "Bracing - Steel", 
        "Bracing - Timber", 
        "Blocking - Timber", 
        "Bearings", 
        "Sonotubes", 
        "Wingwalls - Gabion Baskets", 
        "Columns - Timber", 
        "Embankments", 
        "Slope Protection",
        "Streams and Waterways"
    ]
    if name in discrete_items:
        return C_val

    # Elements measured strictly by Length (Linear Meters)
    linear_items = [
        "Barrier", 
        "Noise Barriers", 
        "Railing Systems", 
        "Railing Systems - Timber", 
        "Hand Railings", 
        "Armouring / Retaining Devices", 
        "Curb and Gutters"
    ]
    if name in linear_items:
        return L * C_mult

    # Specialized linear profiles (Sidewalks, Curbs)
    if name in ["Sidewalk/Curb", "Sidewalks and Medians", "Curbs"]:
        return L * (W + H) * C_mult

    # Vertical Area Elements (Length x Height)
    vertical_area_items = [
        "Barrier/Parapet Walls", 
        "Barrier/Parapet Walls (interior)", 
        "Barrier/Parapet Walls (exterior)", 
        "Barrier Systems on Walls", 
        "Walls", 
        "Wingwalls"
    ]
    if name in vertical_area_items:
        return L * H * C_mult

    # Secondary Vertical Area Elements (Width x Height)
    if name in ["Ballast Walls", "Abutment Walls", "Abutment Walls - Gabion Baskets"]:
        return W * H * C_mult

    # Volumetric/Surface wrapped items (Caps)
    if name in ["Caps", "Caps - Timber"]:
        return C_mult * 2 * ((W * H) + (L * H) + (L * W))

    # Default logic: Deck Area / Standard Area (Length x Width)
    return L * W * C_mult


# ============================================================================
# --- 5. MAIN REPORT UI MODULE ---
# ============================================================================

def show_report():
    """
    Renders the entire Master Report module, including Pages 1 through 5.
    Handles data validation, condition state math, and state tracking.
    """
    st.subheader("📝 Master Report Data Entry")
    fid = st.session_state.get('form_id', 'init')

    # ------------------------------------------------------------------------
    # STATE INITIALIZATION (Loading default dictionaries into memory)
    # ------------------------------------------------------------------------
    if 'class_opts' not in st.session_state:
        st.session_state.class_opts = load_list("class.json", ["BRIDGE", "CULVERT", "RETAINING WALL"])
    
    if 'loc_opts' not in st.session_state:
        st.session_state.loc_opts = load_list("loc.json", ["-", "North & South/ East & West of Structure", "Top of Deck", "Underside of Structure", "On Approach", "Below Roadway"])
    
    if 'mat_opts' not in st.session_state:
        st.session_state.mat_opts = load_list("mat.json", ["-", "Concrete", "Steel", "Timber", "Asphalt", "Gravel", "Masonry", "Neoprene"])
    
    if 'typ_opts' not in st.session_state:
        st.session_state.typ_opts = load_list("typ.json", ["-", "Steel Flex Beam", "Reinforced Concrete", "Gravel Wearing Surface", "Asphalt Wearing Surface", "Strip Seal"])
    
    if 'env_opts' not in st.session_state:
        st.session_state.env_opts = load_list("env.json", ["Severe", "Moderate", "Benign"])
    
    if 'pro_opts' not in st.session_state:
        st.session_state.pro_opts = load_list("pro.json", ["None", "Paint", "Hot Dip Galvanizing", "Asphalt", "Epoxy"])
    
    if 'pd_opts' not in st.session_state:
        st.session_state.pd_opts = load_list("pd.json", DEFAULT_PD)
    
    if 'mn_opts' not in st.session_state:
        st.session_state.mn_opts = load_list("mn.json", DEFAULT_MN)
    
    if 'dir_opts' not in st.session_state:
        st.session_state.dir_opts = load_list("dir.json", ["North-South", "East-West", "Northeast-Southwest", "Northwest-Southeast"])
    
    if 'equip_opts' not in st.session_state:
        st.session_state.equip_opts = load_list("equip.json", ["Measuring tape, hip waders, camera and hammer", "Drone", "Snooper", "Ladders", "Boat"])
    
    if 'weather_opts' not in st.session_state:
        st.session_state.weather_opts = load_list("weather.json", ["Clear", "Mostly Cloudy", "Overcast", "Rain", "Snow"])

    if 'imm_opts' not in st.session_state:
        st.session_state.imm_opts = load_list("imm.json", ["None", "Close Bridge", "Post Bridge"])
    
    if 'inv_opts' not in st.session_state:
        st.session_state.inv_opts = load_list("inv.json", [
            "None", "Rehabilitation/Replacement Study", "Detailed Deck Condition Survey", 
            "Non-destructive Delamination Survey of Asphalt- Covered Deck", "Concrete Substructure Condition Survey", 
            "Detailed Coating Condition Survey", "Detailed Timber Investigation", "Underwater Investigation", 
            "Fatigue Investigation", "Seismic Investigation", "Structure Evaluation", 
            "Monitoring of Deformations, Settlement and Movements", "Monitoring Crack Widths"
        ])
    
    if 'work_opts' not in st.session_state:
        st.session_state.work_opts = load_list("work.json", [
            "None", "Replace Structure (Urgent)", "Replace Structure (1-5 years)", "Replace Structure (6-10 years)", 
            "Minor Rehabilitation (1-5 years)", "Minor Rehabilitation (6-10 years)", "Major Rehabilitation (1-5 years)", 
            "Major Rehabilitation (6-10 years)", "Rehabilitate Element (Urgent)", "Rehabilitate Element (1-5 years)", 
            "Rehabilitate Element (6-10 years)", "Closure"
        ])
    
    if 'maint_opts' not in st.session_state:
        st.session_state.maint_opts = load_list("maint.json", ["None", "Clearing Vegetation: Blocking Sign", "Concrete Repairs", "Signage Restoration", "Roadway Surface Repairs"])
    
    if 'def_opts' not in st.session_state:
        st.session_state.def_opts = load_list("def.json", ["None", "Severe Scaling", "Severe Erosion", "Exposed reinforcement", "Deteriorated Joint Seal"])
    
    if 'bar_opts' not in st.session_state:
        st.session_state.bar_opts = load_list("barriers.json", ["None", "Barriers present and conforming", "Barriers present, not conforming", "No barriers present"])

    if 'report_elements' not in st.session_state:
        st.session_state.report_elements = []


    # ------------------------------------------------------------------------
    # --- PAGE 1: MUNICIPAL STRUCTURE INSPECTION FORM (INVENTORY) ---
    # ------------------------------------------------------------------------
    with st.expander("📄 Page 1: Structure Inventory", expanded=True):
        st.markdown("<h3 style='text-align: center;'>MUNICIPAL STRUCTURE INSPECTION FORM</h3>", unsafe_allow_html=True)
        
        top1, top2 = st.columns([1, 1])
        with top1:
            st.write("**Structure Classification**")
            editable_dropdown_small("Structure Classification", st.session_state.class_opts, "class.json", "p1_class")
        with top2:
            st.write("**Site No.**")
            st.text_input("Site No.", key=f"p1_site_no_{fid}", label_visibility="collapsed")

        with st.container(border=True):
            st.markdown("#### INVENTORY DATA:")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Structure Name", key=f"p1_str_name_{fid}")
                st.text_input("Main Hwy/Road #", key=f"p1_hwy_{fid}")
                st.text_input("Road Name", key=f"p1_road_name_{fid}")
                st.text_input("Structure Location", key=f"p1_location_{fid}")
                
                c_lat, c_lon = st.columns(2)
                c_lat.text_input("Latitude", key=f"p1_lat_{fid}")
                c_lon.text_input("Longitude", key=f"p1_lon_{fid}")
                
                st.text_input("Owner(s)", key=f"p1_owner_{fid}")
                st.text_input("MTO Region", key=f"p1_region_{fid}")
                st.text_input("MTO District", key=f"p1_district_{fid}")
                st.text_input("Old County", key=f"p1_county_{fid}")
                st.text_input("Geographic Twp.", key=f"p1_twp_{fid}")
                st.text_input("Structure Type", key=f"p1_type_{fid}")

            with col2:
                st.write("**Under Structure:**")
                try: 
                    st.pills("Under Structure", ["Navigable Water", "Non-Navigable Water", "Rail", "Road", "Pedestrian", "Other"], selection_mode="multi", key=f"p1_under_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.multiselect("Under Structure", ["Navigable Water", "Non-Navigable Water", "Rail", "Road", "Pedestrian", "Other"], key=f"p1_under_{fid}", label_visibility="collapsed")

                st.write("**On Structure:**")
                try: 
                    st.pills("On Structure", ["Rail", "Road", "Pedestrian", "Other"], selection_mode="multi", key=f"p1_on_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.multiselect("On Structure", ["Rail", "Road", "Pedestrian", "Other"], key=f"p1_on_{fid}", label_visibility="collapsed")
                
                st.write("**Heritage Designation:**")
                st.selectbox("Heritage", ["Not Cons.", "Cons./Not App.", "List/Not Desig.", "Desig./not List", "Desig. & List"], key=f"p1_heritage_{fid}", label_visibility="collapsed")
                
                st.write("**Road Class:**")
                try: 
                    st.pills("Road Class", ["Freeway", "Arterial", "Collector", "Local"], selection_mode="single", key=f"p1_road_class_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.radio("Road Class", ["Freeway", "Arterial", "Collector", "Local"], horizontal=True, key=f"p1_road_class_{fid}", label_visibility="collapsed")

                c2a, c2b = st.columns(2)
                c2a.number_input("Posted Speed", min_value=0, step=10, key=f"p1_speed_{fid}")
                c2b.number_input("No. of Lanes", min_value=1, step=1, key=f"p1_lanes_{fid}")
                c2a.number_input("AADT", min_value=0, step=100, key=f"p1_aadt_{fid}")
                c2b.number_input("% Trucks", min_value=0.0, step=1.0, key=f"p1_trucks_{fid}")

                st.write("**Special Routes:**")
                try: 
                    st.pills("Special Routes", ["Transit", "Truck", "School", "Bicycle"], selection_mode="multi", key=f"p1_routes_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.multiselect("Special Routes", ["Transit", "Truck", "School", "Bicycle"], key=f"p1_routes_{fid}", label_visibility="collapsed")
                
                st.number_input("Detour Length Around Structure (km)", min_value=0.0, step=0.1, key=f"p1_detour_{fid}")

            st.divider()
            
            # --- MATH AUTOMATION: Deck Area Formula ---
            dim1, dim2 = st.columns(2)
            with dim1:
                deck_len = st.number_input("Total Deck Length (m)", min_value=0.0, step=0.1, value=0.0, key=f"p1_deck_len_{fid}")
                str_width = st.number_input("Overall Str. Width (m)", min_value=0.0, step=0.1, value=0.0, key=f"p1_str_width_{fid}")
                
                calc_deck_area = float(round(deck_len * str_width, 2))
                st.session_state[f"p1_deck_area_{fid}"] = calc_deck_area
                deck_area = st.number_input("Total Deck Area (m²)", step=0.1, help="Auto-calculated (Length x Width)", key=f"p1_deck_area_{fid}")
                
                st.number_input("Roadway Width (m)", min_value=0.0, step=0.1, key=f"p1_road_width_{fid}")
                st.text_input("Span Lengths (m)", key=f"p1_span_lens_{fid}")
            with dim2:
                st.number_input("Fill on Structure (m)", min_value=0.0, step=0.1, key=f"p1_fill_{fid}")
                st.number_input("Skew Angle (Degrees)", step=1, key=f"p1_skew_{fid}")
                
                st.write("**Direction of Structure**")
                editable_dropdown_small("Dir", st.session_state.dir_opts, "dir.json", "p1_dir")
                
                st.number_input("No. of Spans", min_value=1, step=1, key=f"p1_spans_{fid}")

        with st.container(border=True):
            st.markdown("#### HISTORICAL DATA")
            h1, h2 = st.columns(2)
            with h1:
                st.text_input("Year Built", key=f"p1_yr_built_{fid}")
                st.text_input("Year of Last Major Rehab.", key=f"p1_yr_rehab_{fid}")
                st.text_input("Current Load Limit (tonnes)", key=f"p1_load_limit_{fid}")
                st.text_input("Load Limit By-Law #", key=f"p1_bylaw_num_{fid}")
                st.text_input("By-Law Expiry Date", key=f"p1_bylaw_exp_{fid}")
                st.text_input("Min. Vertical Clearance (m)", key=f"p1_vert_clear_{fid}")
            with h2:
                st.text_input("Last OSIM Inspection", key=f"p1_last_osim_{fid}")
                st.text_input("Last Enhanced OSIM Inspection", key=f"p1_last_eosim_{fid}")
                st.text_input("Last Bridge Master Inspection", key=f"p1_last_bmaster_{fid}")
                st.text_input("Last Evaluation", key=f"p1_last_eval_{fid}")
                st.text_input("Last Underwater Inspection", key=f"p1_last_under_{fid}")
                st.text_input("Last Condition Survey", key=f"p1_last_cond_{fid}")
            
            st.write("**Rehabilitation History: (Date / Description)**")
            st.text_area("Rehab History", key=f"p1_rehab_hist_{fid}", label_visibility="collapsed", height=100)


    # ------------------------------------------------------------------------
    # --- PAGE 2: FIELD INSPECTION & OVERALL NOTES ---
    # ------------------------------------------------------------------------
    with st.expander("📄 Page 2: Field Inspection & Investigations", expanded=True):
        
        with st.container(border=True):
            st.markdown("#### FIELD INSPECTION INFORMATION")
            f1, f2 = st.columns(2)
            with f1:
                insp_date = st.date_input("Date of Inspection", key=f"p2_date_{fid}")
                st.text_input("Inspector", key=f"p2_inspector_{fid}")
                st.text_input("Others in Party", key=f"p2_others_{fid}")
            with f2:
                st.write("**Type of Inspection:**")
                try: 
                    st.pills("Type of Inspection", ["OSIM", "Enhanced OSIM"], selection_mode="single", key=f"p2_insp_type_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.radio("Type of Inspection", ["OSIM", "Enhanced OSIM"], horizontal=True, key=f"p2_insp_type_{fid}", label_visibility="collapsed")
                
                st.write("**Access Equipment Used:**")
                editable_dropdown_small("Equip", st.session_state.equip_opts, "equip.json", "p2_equip")
                st.write("**Weather:**")
                editable_dropdown_small("Weather", st.session_state.weather_opts, "weather.json", "p2_weather")
                st.text_input("Temperature (°C)", key=f"p2_temp_{fid}")

        with st.container(border=True):
            st.markdown("#### ADDITIONAL INVESTIGATION REQUIRED")
            inv_total_cost = 0.0
            hcols = st.columns([4, 2, 2, 2])
            hcols[0].write("**Investigation Type**")
            hcols[1].write("**Specifics**")
            hcols[2].write("**Priority**")
            hcols[3].write("**Estimated Cost**")
            st.divider()
            
            for idx, (inv_name, is_header, opts, costs) in enumerate(INV_LIST_DEF):
                if is_header:
                    st.markdown(f"*{inv_name}*")
                else:
                    cols = st.columns([4, 2, 2, 2])
                    padding = "padding-left: 20px;" if "Survey" in inv_name or "Monitoring of" in inv_name or "Monitoring Crack" in inv_name else ""
                    cols[0].markdown(f"<div style='padding-top:8px; {padding}'>{inv_name}</div>", unsafe_allow_html=True)
                    
                    spec_val = None
                    if opts:
                        spec_val = cols[1].selectbox("Spec", opts, key=f"inv_spec_{idx}_{fid}", label_visibility="collapsed")
                    
                    prio = cols[2].selectbox("Priority", ["None", "Normal", "Urgent"], key=f"inv_prio_{idx}_{fid}", label_visibility="collapsed")
                    cost_key = f"inv_cost_{idx}_{fid}"
                    prev_prio_key = f"prev_prio_{idx}_{fid}"

                    if prev_prio_key not in st.session_state:
                        st.session_state[prev_prio_key] = "None"
                    if cost_key not in st.session_state:
                        st.session_state[cost_key] = 0.0
                        
                    # Automated Cost Injection for Investigations
                    if prio != "None" and st.session_state[prev_prio_key] == "None":
                        def_cost = float(costs[opts.index(spec_val)]) if opts and spec_val in opts else (float(costs[0]) if costs else 0.0)
                        st.session_state[cost_key] = def_cost
                        st.session_state[prev_prio_key] = prio
                        st.rerun() 
                    elif prio == "None" and st.session_state[prev_prio_key] != "None":
                        st.session_state[cost_key] = 0.0
                        st.session_state[prev_prio_key] = prio
                        st.rerun() 
                        
                    cost_val = cols[3].number_input("Cost", min_value=0.0, step=100.0, key=cost_key, label_visibility="collapsed")
                    inv_total_cost += cost_val

            st.divider()
            tcols = st.columns([4, 2, 2, 2])
            tcols[0].text_input("Load Posting – Estimated Load Limit", key=f"p2_load_post_{fid}", placeholder="Load Limit")
            tcols[2].markdown("<div style='text-align:right; padding-top:8px;'><b>Total Cost:</b></div>", unsafe_allow_html=True)
            tcols[3].markdown(f"<div style='padding-top:8px;'><b>$ {inv_total_cost:,.2f}</b></div>", unsafe_allow_html=True)
            st.session_state['total_inv_cost'] = inv_total_cost 
            
            st.write("**Investigation Notes:**")
            st.text_area("Investigation Notes", key=f"p2_inv_notes_area_{fid}", height=80, label_visibility="collapsed")

        with st.container(border=True):
            st.markdown("#### OVERALL STRUCTURAL NOTES (Significant Findings)")
            o1, o2 = st.columns(2)
            with o1:
                st.write("**Recommended Work on Structure:**")
                try: 
                    st.pills("Rec Work", ["None", "Minor Rehab.", "Major Rehab.", "Replace"], selection_mode="single", key=f"p2_rec_work_global_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.radio("Rec Work", ["None", "Minor Rehab.", "Major Rehab.", "Replace"], horizontal=True, key=f"p2_rec_work_global_{fid}", label_visibility="collapsed")
            with o2:
                st.write("**Timing of Recommended Work:**")
                try: 
                    st.pills("Rec Timing", ["1 to 5 years", "6 to 10 years"], selection_mode="single", key=f"p2_rec_time_global_{fid}", label_visibility="collapsed")
                except AttributeError: 
                    st.radio("Rec Timing", ["1 to 5 years", "6 to 10 years"], horizontal=True, key=f"p2_rec_time_global_{fid}", label_visibility="collapsed")
            
            st.write("**Overall Comments:**")
            st.text_area("Overall Comments", key=f"p2_overall_comm_{fid}", height=120, label_visibility="collapsed")
            
            p2_date_val = st.session_state.get(f"p2_date_{fid}")
            if p2_date_val:
                try: 
                    next_date = p2_date_val.replace(year=p2_date_val.year + 2).strftime("%B %Y")
                except ValueError: 
                    next_date = p2_date_val.replace(year=p2_date_val.year + 2, month=2, day=28).strftime("%B %Y")
            else:
                next_date = ""

            st.text_input("**Date of Next Inspection:**", value=next_date, key=f"p2_next_insp_{fid}")

        st.divider()
        st.markdown("##### REFERENCE DICTIONARIES")
        dict_col1, dict_col2 = st.columns(2)
        with dict_col1:
            st.markdown("**Suspected Performance Deficiencies**")
            st.markdown(f"<div style='font-size:0.75em; line-height:1.2; column-count: 2; column-gap: 20px;'>{'<br>'.join(DEFAULT_PD)}</div>", unsafe_allow_html=True)
        with dict_col2:
            st.markdown("**Maintenance Needs**")
            st.markdown(f"<div style='font-size:0.75em; line-height:1.2; column-count: 2; column-gap: 20px;'>{'<br>'.join(DEFAULT_MN)}</div>", unsafe_allow_html=True)


    # ------------------------------------------------------------------------
    # --- PAGE 3: ELEMENT DATA ---
    # ------------------------------------------------------------------------
    with st.expander("📄 Page 3: Element Data", expanded=True):
        st.info("Input geometry. The Engine will automatically calculate Total Quantity and balance your Condition States.")
        
        for item in st.session_state.report_elements:
            if 'uid' not in item:
                item['uid'] = str(uuid.uuid4())

        with st.expander("➕ Add Element Data Card", expanded=False):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                sel_grp = st.selectbox("Element Group", options=list(MASTER_ELEMENTS.keys()), key="rep_grp")
            with c2:
                sel_name = st.selectbox("Element Name", options=MASTER_ELEMENTS[sel_grp], key="rep_name")
            with c3:
                st.write("")
                st.write("")
                if st.button("Add Card"):
                    st.session_state.report_elements.append({
                        "uid": str(uuid.uuid4()), "group": sel_grp, "name": sel_name,
                        "loc": "-", "mat": "-", "typ": "-", "env": "Severe", "pro": "None",
                        "L": None, "W": None, "H": None, "C": None, "limit_insp": False,
                        "Total": 0.0, "unit": "m²", "exc": None, "good": None, "fair": None, "poor": None,
                        "comments": "", "perf_def": "00 None", "maint_need": "00 None",
                        "rec_action": None, "rec_time": None, "mnt_time": None, "est_cost": 0.0 
                    })
                    group_order = list(MASTER_ELEMENTS.keys())
                    st.session_state.report_elements.sort(key=lambda x: group_order.index(x['group']))
                    st.rerun()

        if len(st.session_state.report_elements) > 0:
            st.markdown("#### ELEMENT DATA")

        for item in st.session_state.report_elements:
            uid = item['uid']
            with st.expander(f"📋 {item['group']} - {item['name']}", expanded=False):
                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown(f"**Element Group:** {item['group']}")
                    st.markdown(f"**Element Name:** {item['name']}")
                    st.write("**Location:**")
                    item['loc'] = editable_dropdown_small("Location", st.session_state.loc_opts, "loc.json", f"loc_{uid}")
                    st.write("**Material:**")
                    item['mat'] = editable_dropdown_small("Material", st.session_state.mat_opts, "mat.json", f"mat_{uid}")
                    st.write("**Element Type:**")
                    item['typ'] = editable_dropdown_small("Element Type", st.session_state.typ_opts, "typ.json", f"typ_{uid}")
                    st.write("**Environment:**")
                    item['env'] = editable_dropdown_small("Environment", st.session_state.env_opts, "env.json", f"env_{uid}")
                    st.write("**Protection System:**")
                    item['pro'] = editable_dropdown_small("Protection System", st.session_state.pro_opts, "pro.json", f"pro_{uid}")
                
                with c_right:
                    item['L'] = st.number_input("Length (L)", value=item.get('L'), key=f"L_{uid}", placeholder="-")
                    item['W'] = st.number_input("Width (W)", value=item.get('W'), key=f"W_{uid}", placeholder="-")
                    item['H'] = st.number_input("Height (H)", value=item.get('H'), key=f"H_{uid}", placeholder="-")
                    item['C'] = st.number_input("Count (C)", value=item.get('C'), key=f"C_{uid}", placeholder="-")
                    
                    if f"tot_{uid}" not in st.session_state:
                        st.session_state[f"tot_{uid}"] = float(item.get('Total', 0.0))
                    
                    current_geom = (item['L'], item['W'], item['H'], item['C'])
                    if 'last_geom' not in item:
                        item['last_geom'] = current_geom
                    
                    if item['last_geom'] != current_geom:
                        calc_qty = calculate_total_qty(item['name'], item['L'], item['W'], item['H'], item['C'])
                        st.session_state[f"tot_{uid}"] = float(calc_qty)
                        item['last_geom'] = current_geom
                        
                    st.number_input("Total Quantity", key=f"tot_{uid}")
                    item['Total'] = st.session_state[f"tot_{uid}"]
                    st.write("")
                    st.write("")
                    item['limit_insp'] = st.checkbox("Limited Inspection", value=item['limit_insp'], key=f"lim_{uid}")

                st.divider()
                st.write("**Condition Data:**")
                cond1, cond2, cond3, cond4, cond5 = st.columns(5)
                cond1.write("Units")
                cond2.write("Excellent")
                cond3.write("Good")
                cond4.write("Fair")
                cond5.write("Poor")
                
                item['unit'] = cond1.selectbox("Unit", ["m²", "m", "Each", "LS", "m³"], key=f"u_{uid}", label_visibility="collapsed")
                item['good'] = cond3.number_input("Good", min_value=0.0, value=item.get('good'), key=f"g_{uid}", label_visibility="collapsed", placeholder="-")
                item['fair'] = cond4.number_input("Fair", min_value=0.0, value=item.get('fair'), key=f"f_{uid}", label_visibility="collapsed", placeholder="-")
                item['poor'] = cond5.number_input("Poor", min_value=0.0, value=item.get('poor'), key=f"p_{uid}", label_visibility="collapsed", placeholder="-")

                if f"e_{uid}" not in st.session_state:
                    st.session_state[f"e_{uid}"] = float(item.get('exc') or 0.0)

                current_cond = (item['Total'], item['good'], item['fair'], item['poor'])
                if 'last_cond' not in item:
                    item['last_cond'] = current_cond
                
                if item['last_cond'] != current_cond:
                    g = safe_float(item['good'])
                    f = safe_float(item['fair'])
                    p = safe_float(item['poor'])
                    current_total = safe_float(item['Total'])
                    st.session_state[f"e_{uid}"] = max(0.0, current_total - (g + f + p))
                    item['last_cond'] = current_cond

                cond2.number_input("Exc", key=f"e_{uid}", label_visibility="collapsed")
                item['exc'] = st.session_state[f"e_{uid}"]

                e = safe_float(item['exc'])
                g = safe_float(item['good'])
                f = safe_float(item['fair'])
                p = safe_float(item['poor'])
                current_total = safe_float(item['Total'])

                if round(e + g + f + p, 2) != round(current_total, 2) and current_total > 0:
                    st.warning(f"⚠️ Warning: Sum of condition states ({round(e+g+f+p, 2)}) does not equal Total Quantity ({round(current_total, 2)}).")

                st.write("**Comments:**")
                item['comments'] = st.text_area("Comments", value=item['comments'], key=f"com_{uid}", label_visibility="collapsed", placeholder="Enter field observations here...")

                d_col, m_col = st.columns(2)
                with d_col:
                    st.write("**Performance Deficiencies:**")
                    item['perf_def'] = editable_dropdown_small("Perf Def", st.session_state.pd_opts, "pd.json", f"pd_{uid}")
                with m_col:
                    st.write("**Maintenance Needs:**")
                    item['maint_need'] = editable_dropdown_small("Maint Need", st.session_state.mn_opts, "mn.json", f"mn_{uid}")

                st.write("")
                rw_col, ma_col = st.columns(2)
                
                with rw_col:
                    st.write("**Recommended Work:**")
                    try:
                        item['rec_action'] = st.pills("Action", ["Rehabilitate", "Replace"], selection_mode="single", default=item.get('rec_action'), key=f"ract_{uid}", label_visibility="collapsed")
                        item['rec_time'] = st.pills("Timeframe", ["1 - 5 Years", "6 - 10 Years"], selection_mode="single", default=item.get('rec_time'), key=f"rtim_{uid}", label_visibility="collapsed")
                    except AttributeError:
                        act_val = item.get('rec_action') or "None"
                        item['rec_action'] = st.radio("Action", ["None", "Rehabilitate", "Replace"], index=["None", "Rehabilitate", "Replace"].index(act_val), horizontal=True, key=f"ract_{uid}", label_visibility="collapsed")
                        if item['rec_action'] == "None": item['rec_action'] = None
                        time_val = item.get('rec_time') or "None"
                        item['rec_time'] = st.radio("Timeframe", ["None", "1 - 5 Years", "6 - 10 Years"], index=["None", "1 - 5 Years", "6 - 10 Years"].index(time_val), horizontal=True, key=f"rtim_{uid}", label_visibility="collapsed")
                        if item['rec_time'] == "None": item['rec_time'] = None

                with ma_col:
                    st.write("**Maintenance Needs:**")
                    try:
                        item['mnt_time'] = st.pills("Maint Timeframe", ["Urgent", "1 Year", "2 Years"], selection_mode="single", default=item.get('mnt_time'), key=f"mtim_{uid}", label_visibility="collapsed")
                    except AttributeError:
                        mnt_val = item.get('mnt_time') or "None"
                        item['mnt_time'] = st.radio("Maint Timeframe", ["None", "Urgent", "1 Year", "2 Years"], index=["None", "Urgent", "1 Year", "2 Years"].index(mnt_val), horizontal=True, key=f"mtim_{uid}", label_visibility="collapsed")
                        if item['mnt_time'] == "None": item['mnt_time'] = None

                st.write("")
                if st.button("🗑️ Delete Element Card", key=f"del_card_{uid}", type="primary"):
                    st.session_state.report_elements = [e for e in st.session_state.report_elements if e['uid'] != uid]
                    st.rerun()

    # ------------------------------------------------------------------------
    # --- PAGE 4: REPAIR AND REHABILITATION REQUIRED ---
    # ------------------------------------------------------------------------
    with st.expander("📄 Page 4: Repair and Rehabilitation Required", expanded=True):
        sum_cols = st.columns([2.5, 4, 1, 1, 1, 1.5], gap="small")
        sum_cols[0].write("**Element**")
        sum_cols[1].write("**Repair and Rehabilitation Required**")
        sum_cols[2].markdown("<div style='text-align:center;'><b>6 - 10 Years</b></div>", unsafe_allow_html=True)
        sum_cols[3].markdown("<div style='text-align:center;'><b>1 - 5 Years</b></div>", unsafe_allow_html=True)
        sum_cols[4].markdown("<div style='text-align:center;'><b>< 1 year</b></div>", unsafe_allow_html=True)
        sum_cols[5].write("**Estimated Cost**")

        total_est_cost = 0.0
        for item in st.session_state.report_elements:
            uid = item['uid']
            rec_act = item.get('rec_action')
            rec_time = item.get('rec_time')
            mnt_time = item.get('mnt_time')
            m_need = item.get('maint_need', '00 None')
            
            if bool(rec_act or mnt_time or (m_need and "00 None" not in m_need)):
                r_cols = st.columns([2.5, 4, 1, 1, 1, 1.5], gap="small")
                r_cols[0].markdown(f"<div style='padding-top:10px;'>{item['name']}</div>", unsafe_allow_html=True)
                
                parts = []
                if rec_act == "Rehabilitate": 
                    parts.append("Rehabilitate Element.")
                if rec_act == "Replace": 
                    parts.append("Replace Element.")
                if m_need and "00 None" not in m_need: 
                    parts.append(m_need)
                
                new_default = " ".join(parts) if parts else "Maintenance required."
                
                if f"rt_{uid}" not in st.session_state:
                    st.session_state[f"rt_{uid}"] = new_default
                    st.session_state[f"prev_def_text_{uid}"] = new_default
                if st.session_state.get(f"prev_def_text_{uid}") != new_default:
                    st.session_state[f"rt_{uid}"] = new_default
                    st.session_state[f"prev_def_text_{uid}"] = new_default
                
                item['summary_desc'] = r_cols[1].text_input("Desc", key=f"rt_{uid}", label_visibility="collapsed")

                p_6_10 = "X" if rec_time == "6 - 10 Years" else ""
                p_1_5 = "X" if rec_time == "1 - 5 Years" or mnt_time == "2 Years" else ""
                p_1 = "X" if mnt_time in ["Urgent", "1 Year"] else ""
                
                r_cols[2].markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold;'>{p_6_10}</div>", unsafe_allow_html=True)
                r_cols[3].markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold;'>{p_1_5}</div>", unsafe_allow_html=True)
                r_cols[4].markdown(f"<div style='text-align:center; padding-top:10px; font-weight:bold;'>{p_1}</div>", unsafe_allow_html=True)
                
                item['est_cost'] = r_cols[5].number_input("Cost", min_value=0.0, value=float(item.get('est_cost', 0.0)), step=100.0, key=f"cost_{uid}", label_visibility="collapsed")
                total_est_cost += item['est_cost']

        st.divider()
        t_cols = st.columns([2.5, 4, 1, 1, 1, 1.5], gap="small")
        t_cols[4].write("**Total Cost:**")
        t_cols[5].markdown(f"**$ {total_est_cost:,.2f}**")

    # ------------------------------------------------------------------------
    # --- PAGE 5: EXECUTIVE SUMMARY ---
    # ------------------------------------------------------------------------
    with st.expander("📄 Page 5: Executive Summary", expanded=True):
        st.info("Build your final inspection summary. Use the Auto-Fill button to instantly pull calculations from the Element Data (Page 3) and map Overall Notes (Page 2).")
        
        # THE AUTO-FILL BRIDGE ENGINE
        if st.button("🔄 Auto-Fill Page 5 from Report Data", key="rep_autofill_p5", type="primary"):
            
            # 1. Map Page 2 "Overall Recommended Work" to Page 5 Dropdown
            p2_work_val = st.session_state.get(f"p2_rec_work_global_{fid}", "None")
            p2_time_val = st.session_state.get(f"p2_rec_time_global_{fid}", "1 to 5 years")
            
            mapped_overall = "None"
            if p2_work_val != "None":
                work_map = {
                    "Minor Rehab.": "Minor Rehabilitation",
                    "Major Rehab.": "Major Rehabilitation",
                    "Replace": "Replace Structure"
                }
                time_map = {
                    "1 to 5 years": "(1-5 years)",
                    "6 to 10 years": "(6-10 years)"
                }
                work_str = work_map.get(p2_work_val, p2_work_val)
                time_str = time_map.get(p2_time_val, "")
                mapped_overall = f"{work_str} {time_str}".strip()

            # Ensure the newly mapped option actually exists in the dropdown list
            if mapped_overall not in st.session_state.work_opts:
                st.session_state.work_opts.append(mapped_overall)
                save_list("work.json", st.session_state.work_opts)

            # Set the selection
            st.session_state["rep_p5_overall_rw_sel"] = mapped_overall

            # 2. Extract Urgent Maintenance items
            urgents = [el['name'] for el in st.session_state.report_elements if el.get('mnt_time') == "Urgent"]
            if urgents:
                val = "Urgent maintenance: " + ", ".join(urgents)
                if val not in st.session_state.imm_opts: 
                    st.session_state.imm_opts.append(val)
                st.session_state["rep_p5_imm_interv_dd_sel"] = val

            # 3. Extract Additional Investigations from Page 2
            auto_inv = []
            for idx, (inv_name, is_header, opts, costs) in enumerate(INV_LIST_DEF):
                if not is_header and st.session_state.get(f"inv_prio_{idx}_{fid}", "None") != "None":
                    spec = st.session_state.get(f"inv_spec_{idx}_{fid}", "")
                    val = f"{inv_name} ({spec})" if spec else inv_name
                    if val not in st.session_state.inv_opts: 
                        st.session_state.inv_opts.append(val)
                    auto_inv.append(val)
            if auto_inv:
                new_uids = []
                for i, val in enumerate(auto_inv):
                    n_id = i + 1
                    new_uids.append(n_id)
                    st.session_state[f"rep_inv_sel_{n_id}"] = val
                st.session_state['rep_inv_rows'] = new_uids
            
            # 4. Extract Specific Element Work from Page 3
            auto_rw = []
            for el in st.session_state.report_elements:
                act = el.get('rec_action')
                tim = el.get('rec_time')
                if act and act != "None":
                    t_str = f" ({tim})" if tim and tim != "None" else ""
                    val = f"{act} {el['name']}{t_str}"
                    if val not in st.session_state.work_opts: 
                        st.session_state.work_opts.append(val)
                    if val not in auto_rw: 
                        auto_rw.append(val)
            if auto_rw:
                new_uids = []
                for i, val in enumerate(auto_rw):
                    n_id = i + 1
                    new_uids.append(n_id)
                    st.session_state[f"rep_rw_sel_{n_id}"] = val
                st.session_state['rep_rw_rows'] = new_uids
                
            # 5. Extract Maintenance Needs from Page 3
            auto_mn = []
            for el in st.session_state.report_elements:
                mn = el.get('maint_need', '')
                if mn and "00 None" not in mn: 
                    val = f"{el['name']}: {mn[3:]}"
                    if val not in st.session_state.maint_opts: 
                        st.session_state.maint_opts.append(val)
                    auto_mn.append(val)
            if auto_mn:
                new_uids = []
                for i, val in enumerate(auto_mn):
                    n_id = i + 1
                    new_uids.append(n_id)
                    st.session_state[f"rep_pm_sel_{n_id}"] = val
                st.session_state['rep_pm_rows'] = new_uids

            # 6. Extract Performance Deficiencies from Page 3
            auto_def = []
            for el in st.session_state.report_elements:
                pd = el.get('perf_def', '')
                if pd and "00 None" not in pd: 
                    val = f"{el['name']}: {pd[3:]}"
                    if val not in st.session_state.def_opts: 
                        st.session_state.def_opts.append(val)
                    auto_def.append(val)
            if auto_def:
                new_uids = []
                for i, val in enumerate(auto_def):
                    n_id = i + 1
                    new_uids.append(n_id)
                    st.session_state[f"rep_cd_sel_{n_id}"] = val
                st.session_state['rep_cd_rows'] = new_uids

            # 7. COST CALCULATION ENGINE (RESTORED TO THE ORIGINAL WORKING TIER SYSTEM)
            mr_total_length = float(st.session_state.get(f"p1_deck_len_{fid}", 0.0))
            mr_deck_width = float(st.session_state.get(f"p1_str_width_{fid}", 0.0))

            calc_rep_cost = 0.0
            if mr_total_length > 0 and mr_deck_width > 0:
                if mr_total_length <= 10 and mr_deck_width <= 10: rate = 12000
                elif mr_total_length <= 10 and mr_deck_width > 10: rate = 11000
                elif 10 < mr_total_length <= 20 and mr_deck_width <= 10: rate = 10000
                elif 10 < mr_total_length <= 20 and mr_deck_width > 10: rate = 9000
                elif 20 < mr_total_length <= 30 and mr_deck_width <= 10: rate = 8500
                elif 20 < mr_total_length <= 30 and mr_deck_width >= 10: rate = 8000
                elif mr_total_length > 30 and mr_deck_width <= 10: rate = 7000
                else: rate = 6500 
                calc_rep_cost = float(rate * mr_total_length * mr_deck_width)

            # Calculates percentage logic dynamically based on what was mapped to overall_rw
            overall_rw = st.session_state.get("rep_p5_overall_rw_sel", "")
            calc_rec_work_cost = 0.0
            
            if overall_rw:
                if "Replace Structure" in overall_rw: calc_rec_work_cost = calc_rep_cost
                elif "Major Rehabilitation" in overall_rw: calc_rec_work_cost = calc_rep_cost * 0.60
                elif "Minor Rehabilitation" in overall_rw: calc_rec_work_cost = calc_rep_cost * 0.25
                elif "Rehabilitate Element" in overall_rw: calc_rec_work_cost = calc_rep_cost * 0.05
                
            st.session_state["rep_est_replacement"] = float(calc_rep_cost)
            st.session_state["rep_est_rec_work"] = float(calc_rec_work_cost)

            st.rerun()

        # --- PAGE 5 UI ---
        with st.container(border=True):
            c1, c2 = st.columns([2, 8])
            c1.markdown("**Immediate Intervention Required:**")
            with c2:
                st.session_state.p5_imm_interv_dd = editable_dropdown_small("Imm", st.session_state.imm_opts, "imm.json", "rep_p5_imm_interv_dd")
            
        with st.container(border=True):
            rep_inv_sels, rep_inv_notes = dynamic_summary_row("Additional Investigations", st.session_state.inv_opts, "inv.json", "rep_inv")
            
            st.divider()
            col_orw1, col_orw2 = st.columns(2)
            with col_orw1:
                st.markdown("**Final Overall Recommended Work:**")
                st.session_state.rep_p5_overall_rw = editable_dropdown_small("Overall", st.session_state.work_opts, "work.json", "rep_p5_overall_rw")
            with col_orw2:
                st.markdown("**Overall Recommended Work Notes:**")
                st.text_area("Overall Notes", key="rep_p5_overall_rw_notes", label_visibility="collapsed", height=68)

            st.write("")
            rep_work_sels, rep_work_notes = dynamic_summary_row("↳ Specific Element Recommended Works", st.session_state.work_opts, "work.json", "rep_rw")
            st.divider()
            
            rep_pm_sels, rep_pm_notes = dynamic_summary_row("Principal Maintenance Needs", st.session_state.maint_opts, "maint.json", "rep_pm")
            rep_def_sels, rep_def_notes = dynamic_summary_row("Common Deficiencies", st.session_state.def_opts, "def.json", "rep_cd")
            rep_bar_sels, rep_bar_notes = dynamic_summary_row("Approach/Bridge Barriers", st.session_state.bar_opts, "barriers.json", "rep_bar")

        st.divider()
        st.write("**Cost Estimates**")

        cost1, cost2 = st.columns(2)
        with cost1:
            st.session_state.p5_rep_cost = st.number_input(
                "Estimated Replacement Costs ($)", 
                step=1000.0, 
                key="rep_est_replacement"
            )
        with cost2:
            st.session_state.p5_rec_work_cost = st.number_input(
                "Estimate of Recommended Work Costs ($)", 
                step=1000.0, 
                help="Calculated via Auto-Fill using the standard OSIM deck area rate tiers and recommended work percentages.", 
                key="rep_est_rec_work"
            )

    return st.session_state.report_elements