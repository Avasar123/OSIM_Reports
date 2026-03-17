import streamlit as st
import os
import json
import datetime
import shutil
import uuid
from streamlit.errors import StreamlitAPIException

# --- SET UP PAGE CONFIG ---
st.set_page_config(page_title="OSIM Inspection App", layout="wide")


# =========================================================================
# --- USER MANAGEMENT FUNCTIONS (Must be defined before login screen) ---
# =========================================================================

USERS_FILE = "users.json"
DEFAULT_USERS = {
    "OSIM": {"password": "Quinpool", "role": "Master"},
    "Admin": {"password": "osim", "role": "Admin"}
}

def load_users():
    """Loads users from the JSON vault. Creates the vault if it doesn't exist."""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump(DEFAULT_USERS, f, indent=4)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users_dict):
    """Saves updated user credentials to the JSON vault."""
    with open(USERS_FILE, "w") as f:
        json.dump(users_dict, f, indent=4)


# =========================================================================
# --- SECURITY GATE: REALISTIC ENGINEERING LOGIN SCREEN ---
# =========================================================================

# Initialize login state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

if not st.session_state['logged_in']:
    # Inject Custom CSS for the Realistic Engineering UI
    st.markdown("""
        <style>
        /* Hide default Streamlit elements */
        [data-testid="stHeader"] {display: none;}
        [data-testid="stSidebar"] {display: none;}
        .stTabs {display: none;}
        
        /* REALISTIC INFRASTRUCTURE BACKGROUND */
        .stApp {
            background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.95)), 
                        url("https://images.unsplash.com/photo-1552594879-11ba105a39cb?q=80&w=2070&auto=format&fit=crop") no-repeat center center fixed !important;
            background-size: cover !important;
        }

        /* Clean, Professional Security Card */
        .login-box {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            text-align: center;
            color: white;
            margin-top: 15vh;
        }
        
        h1 {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 400;
            letter-spacing: 2px;
            color: #f8fafc;
            margin-bottom: 30px;
            text-transform: uppercase;
            font-size: 1.8rem;
        }
        
        .stTextInput > div > div > input {
            background-color: rgba(0, 0, 0, 0.5) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 4px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3b82f6 !important; 
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.4) !important;
        }
        
        .stTextInput p {
            color: #94a3b8 !important;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .stButton > button {
            border-radius: 4px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h1>OSIM SECURE PORTAL</h1>", unsafe_allow_html=True)
        
        st.write("")
        username = st.text_input("Inspector ID")
        password = st.text_input("Passcode", type="password")
        st.write("")
        
        if st.button("Access System", type="primary", use_container_width=True):
            users_db = load_users()
            
            # Authenticate against the dynamic JSON vault
            if username in users_db and users_db[username]["password"] == password:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = username
                st.session_state['user_role'] = users_db[username]["role"]
                st.rerun()
            else:
                st.error("🚫 Access Denied. Invalid ID or Passcode.")
                
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()


# =========================================================================
# --- THE MAIN APP ENGINE (Only runs if logged_in == True) ---
# =========================================================================

SAVE_DIR = "saved_inspections"
os.makedirs(SAVE_DIR, exist_ok=True)

def get_folders():
    folders = [f.name for f in os.scandir(SAVE_DIR) if f.is_dir()]
    return sorted(folders)

class StateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def create_new_report():
    protected_keys = ["active_folder_sel", "logged_in", "current_user", "user_role"]
    saved_values = {k: st.session_state[k] for k in protected_keys if k in st.session_state}
    
    st.session_state.clear()
    
    for k, v in saved_values.items():
        st.session_state[k] = v
        
    st.session_state['current_report_name'] = None
    
    st.session_state['report_elements'] = []
    st.session_state['cp_inv_table'] = [{"id": str(uuid.uuid4()), "col1": "Rehabilitation/Replacement Study", "col2": "LS", "col3": 8000.0}]
    st.session_state['cp_work_table'] = [{"id": str(uuid.uuid4()), "col1": "Minor Rehabilitation", "col2": "LS", "col3": 15000.0}]
    st.session_state['p5_investigations'] = [{"id": str(uuid.uuid4()), "val": "Rehabilitation/Replacement Study"}]
    st.session_state['p5_rec_work'] = [{"id": str(uuid.uuid4()), "val": "Minor Rehabilitation (1-5 years)"}]
    st.session_state['p5_maint_needs'] = [{"id": str(uuid.uuid4()), "val": ""}]
    st.session_state['p5_deficiencies'] = [{"id": str(uuid.uuid4()), "val": ""}]

def save_project(folder, filename):
    data_to_save = {}
    for key, value in st.session_state.items():
        if not key.startswith("FormSubmitter:") and not key.startswith("_"):
            if key.endswith(("_add", "_del", "_btn", "_add_opt", "_del_opt", "_add_row", "_del_row", "_input")) or key.startswith(("add_", "del_")):
                continue
            if key in ["active_folder_sel", "selected_file_sel", "current_report_name", "logged_in", "current_user", "user_role"]:
                continue
                
            try:
                json.dumps(value, cls=StateEncoder)
                data_to_save[key] = value
            except TypeError:
                pass 
            
    # THE AUDIT STAMP: Inject who saved this and when
    data_to_save["_audit_last_saved_by"] = st.session_state.get('current_user', 'Unknown')
    data_to_save["_audit_last_saved_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    folder_path = os.path.join(SAVE_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, f"{filename}.json")
    
    with open(filepath, "w") as f:
        json.dump(data_to_save, f, cls=StateEncoder, indent=4)
    return filepath

def load_project(folder, filename):
    filepath = os.path.join(SAVE_DIR, folder, filename)
    with open(filepath, "r") as f:
        saved_data = json.load(f)
        
    protected_keys = ["active_folder_sel", "selected_file_sel", "logged_in", "current_user", "user_role"]
    saved_values = {k: st.session_state[k] for k in protected_keys if k in st.session_state}
    
    st.session_state.clear()
    
    for k, v in saved_values.items():
        st.session_state[k] = v
        
    st.session_state['current_report_name'] = filename.replace(".json", "")
        
    for key, value in saved_data.items():
        if key.endswith(("_add", "_del", "_btn", "_add_opt", "_del_opt", "_add_row", "_del_row", "_input")) or key.startswith(("add_", "del_")):
            continue
        if key in protected_keys:
            continue
            
        if "date" in key.lower() and isinstance(value, str) and not key.startswith("_audit"):
            try:
                val_to_set = datetime.datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                val_to_set = value
        else:
            val_to_set = value
            
        try:
            st.session_state[key] = val_to_set
        except StreamlitAPIException:
            pass
        except Exception:
            pass

# --- SIDEBAR: PROJECT MANAGEMENT ---
with st.sidebar:
    st.title("⚙️ OSIM Manager")
    
    # Active User Header & Logout
    colA, colB = st.columns([7, 3])
    with colA:
        st.markdown(f"👤 **{st.session_state['current_user']}** ({st.session_state['user_role']})")
    with colB:
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # --- 3-TIER ACCESS CONTROLS ---
    # Only visible if the logged-in user is explicitly a Master or an Admin
    if st.session_state.get('user_role') in ["Master", "Admin"]:
        st.divider()
        panel_title = "👑 Master Controls" if st.session_state['user_role'] == "Master" else "🛡️ Admin Controls"
        st.markdown(f"### {panel_title}")
        
        with st.expander("👥 Manage System Users"):
            current_users_db = load_users()
            
            # Add New User Section
            st.markdown("**Add New User**")
            new_id = st.text_input("New Inspector ID", key="add_user_id")
            new_pass = st.text_input("Passcode", key="add_user_pass")
            
            # BOTH Master and Admin can create Users AND Admins
            new_role = st.selectbox("Role", ["User", "Admin"], key="add_user_role")
            
            if st.button("➕ Add / Update User", use_container_width=True):
                if new_id and new_pass:
                    # Security Check: Prevent anyone from overwriting the Master account
                    if new_id == "OSIM":
                        st.error("🚫 Access Denied: Cannot modify the Master account.")
                    else:
                        current_users_db[new_id] = {"password": new_pass, "role": new_role}
                        save_users(current_users_db)
                        st.success(f"User '{new_id}' successfully created/updated!")
                else:
                    st.error("Enter ID and Passcode.")
            
            st.divider()
            
            # View & Delete Users Section
            st.markdown("**Current Users**")
            for u_id, u_data in current_users_db.items():
                
                # STRICT GHOST PROTOCOL: The OSIM account is completely hidden from this list
                if u_id == "OSIM" or u_data['role'] == "Master":
                    continue
                    
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"- **{u_id}** ({u_data['role']})")
                
                # Logic to determine if the current person is allowed to delete this user
                can_delete = True
                
                # 1. SUICIDE PREVENTION: You cannot delete the account you are currently logged into
                if u_id == st.session_state['current_user']:
                    can_delete = False
                
                # 2. Admins cannot delete other Master accounts (if they somehow existed)
                if st.session_state['user_role'] == "Admin" and u_data['role'] == "Master":
                    can_delete = False 
                    
                if can_delete:
                    if c2.button("🗑️", key=f"del_u_{u_id}"):
                        del current_users_db[u_id]
                        save_users(current_users_db)
                        st.rerun()
                else:
                    if u_id == st.session_state['current_user']:
                        c2.markdown("*(You)*") # Shows this instead of the delete button

    st.divider()
    
    if st.button("📄 New Report", type="primary", use_container_width=True, key="new_report_btn"):
        create_new_report()
        st.toast("Fresh blank report loaded!", icon="📄")
        st.rerun()

    st.divider()
    
    folders = get_folders()
    
    st.markdown("### 📁 Project Folder")
    c_fold, c_fgear = st.columns([8, 2])
    
    with c_fold:
        folder_opts = ["- Select / Create -"] + folders
        active_folder = st.selectbox("Select Folder:", options=folder_opts, label_visibility="collapsed", key="active_folder_sel")
        
    with c_fgear:
        with st.popover("⚙️"):
            st.markdown("**Folder Actions**")
            new_folder = st.text_input("Create New Folder", placeholder="Folder name...", key="new_folder_input")
            if st.button("Create", use_container_width=True, key="create_folder_btn"):
                if new_folder:
                    os.makedirs(os.path.join(SAVE_DIR, new_folder), exist_ok=True)
                    st.rerun()
            
            if active_folder != "- Select / Create -":
                st.divider()
                ren_folder = st.text_input("Rename Folder", placeholder="New name...", key="ren_folder_input")
                if st.button("Rename", use_container_width=True, key="rename_folder_btn"):
                    if ren_folder:
                        os.rename(os.path.join(SAVE_DIR, active_folder), os.path.join(SAVE_DIR, ren_folder))
                        st.session_state['active_folder_sel'] = ren_folder
                        st.rerun()
                
                if st.button("Delete Folder", use_container_width=True, key="delete_folder_btn"):
                    shutil.rmtree(os.path.join(SAVE_DIR, active_folder))
                    st.session_state['active_folder_sel'] = "- Select / Create -"
                    st.rerun()

    st.divider()
    
    st.markdown("### Save Progress")
    if active_folder == "- Select / Create -":
        st.info("⚠️ Select a folder above to save.")
    else:
        curr_report = st.session_state.get('current_report_name')
        
        if curr_report:
            st.success(f"Editing: **{curr_report}**")
            if st.button("Save Report", use_container_width=True, type="primary", key="update_report_btn"):
                save_project(active_folder, curr_report)
                st.toast(f"✅ Updated {curr_report}.json", icon="💾")
                st.rerun() 
                
            with st.expander("Duplicate Report..."):
                save_as_name = st.text_input("New Report Name", placeholder="e.g. Copy_of_Site16", key="save_as_input")
                if st.button("Duplicate", use_container_width=True, key="save_as_btn"):
                    if save_as_name:
                        save_project(active_folder, save_as_name)
                        st.session_state['current_report_name'] = save_as_name
                        st.session_state['selected_file_sel'] = f"{save_as_name}.json"
                        st.toast(f"Saved duplicate as {save_as_name}.json", icon="💾")
                        st.rerun()
                    else:
                        st.error("Enter a new name.")
        else:
            save_name = st.text_input("Report Name", placeholder="e.g. Site16_Culvert", label_visibility="collapsed", key="save_report_input")
            if st.button("Save New Report", use_container_width=True, key="save_report_btn"):
                if save_name:
                    save_project(active_folder, save_name)
                    st.session_state['current_report_name'] = save_name
                    st.session_state['selected_file_sel'] = f"{save_name}.json"
                    st.toast(f"Saved new report: {save_name}.json", icon="💾")
                    st.rerun()
                else:
                    st.error("Enter a report name.")
            
    st.divider()
    
    st.markdown("### Load / Manage Reports")
    if active_folder != "- Select / Create -":
        saved_files = [f for f in os.listdir(os.path.join(SAVE_DIR, active_folder)) if f.endswith(".json")]
        
        if saved_files:
            c_file, c_gear = st.columns([8, 2])
            with c_file:
                selected_file = st.selectbox("Select a Report:", options=["- Select -"] + saved_files, label_visibility="collapsed", key="selected_file_sel")
            with c_gear:
                if selected_file != "- Select -":
                    with st.popover("⚙️"):
                        st.markdown("**File Actions**")
                        if st.button("📂 Load Report", use_container_width=True, key="load_report_btn"):
                            load_project(active_folder, selected_file)
                            st.toast(f"✅ Loaded {selected_file}", icon="📂")
                            st.rerun()
                            
                        if st.button("🗑️ Delete Report", use_container_width=True, key="delete_report_btn"):
                            os.remove(os.path.join(SAVE_DIR, active_folder, selected_file))
                            st.session_state['selected_file_sel'] = "- Select -"
                            if st.session_state.get('current_report_name') == selected_file.replace(".json", ""):
                                create_new_report()
                            st.rerun()
                            
                        st.divider()
                        new_name = st.text_input("New Name", placeholder="Rename without .json", key="ren_report_input")
                        if st.button("Rename", use_container_width=True, key="rename_report_btn"):
                            if new_name:
                                old_path = os.path.join(SAVE_DIR, active_folder, selected_file)
                                new_path = os.path.join(SAVE_DIR, active_folder, f"{new_name}.json")
                                os.rename(old_path, new_path)
                                if st.session_state.get('current_report_name') == selected_file.replace(".json", ""):
                                    st.session_state['current_report_name'] = new_name
                                st.session_state['selected_file_sel'] = f"{new_name}.json"
                                st.rerun()
            
            # --- THE AUDIT LOG DISPLAY ---
            if st.session_state.get('current_report_name') == selected_file.replace(".json", ""):
                last_by = st.session_state.get('_audit_last_saved_by', 'Unknown')
                last_time = st.session_state.get('_audit_last_saved_time', 'Never')
                if last_by != 'Unknown':
                    st.caption(f"📝 *Last saved by **{last_by}** on {last_time}*")
        else:
            st.info("No saved reports in this folder.")
    else:
        st.info("Select a folder above to view reports.")

    st.divider()
    
    # 5. Export UI
    st.markdown("### Export Report")
    if st.button("Generate PDF Report", use_container_width=True, key="generate_pdf_btn"):
        with st.spinner("Compiling PDF..."):
            try:
                from components.pdf_engine import create_pdf
                site_number = st.session_state.get('cp_site_id', st.session_state.get('p1_site_no', 'UnknownSite'))
                if not site_number: site_number = "UnknownSite"
                
                pdf_path = create_pdf(f"OSIM_Report_{site_number}.pdf")
                st.session_state['pdf_path'] = pdf_path
                st.success("PDF generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {e}")

    if 'pdf_path' in st.session_state and os.path.exists(st.session_state['pdf_path']):
        with open(st.session_state['pdf_path'], "rb") as pdf_file:
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_file.read(),
                file_name=os.path.basename(st.session_state['pdf_path']),
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="download_pdf_btn"
            )

# --- APP NAVIGATION & TABS ---
st.title(" Municipal Structure Inspection")

tab1, tab2, tab3, tab4 = st.tabs(["📑 Cover Page", " BCI Calculator", "📝 Master Report", "📸 Photosheet"])

with tab1:
    try:
        from components.cover_page import show_cover_page
        show_cover_page()
    except Exception as e:
        st.error(f"Cover Page error: {e}")

with tab2:
    try:
        from components.bci import show_bci
        show_bci()
    except ImportError:
        st.info("BCI Calculator component not built yet.")

with tab3:
    try:
        from components.report import show_report
        show_report()
    except Exception as e:
        st.error(f"Report error: {e}")

with tab4:
    st.info("Photosheet section will go here.")