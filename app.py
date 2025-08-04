import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import (
    init_db,
    save_module, load_modules, delete_module,
    save_pcs,    load_pcs,    delete_pcs
)

# Tell the browser about our manifest
st.markdown(
    '<link rel="manifest" href="/manifest.json">',
    unsafe_allow_html=True
)

# Register our service worker
st.markdown(
    """
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker
            .register('/sw.js')
            .then(reg => console.log('SW registered:', reg.scope))
            .catch(err => console.error('SW registration failed:', err));
        });
      }
    </script>
    """,
    unsafe_allow_html=True
)

# ─── GLOBAL CSS & PAGE CONFIG ───
st.markdown("""
<style>
  header > div:nth-child(2) { display: none !important; }
  .css-1d391kg { padding: 1rem !important; }
  .css-1lcbmhc { gap: 0.5rem !important; }
  
  /* Custom styling for menu tabs */
  .stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    padding: 12px 16px;
    margin: 4px 0;
    transition: all 0.2s ease;
  }
  
  /* Primary button styling (selected tab) */
  .stButton > button[data-baseweb="button"][aria-pressed="true"],
  .stButton > button[data-baseweb="button"].primary {
    background-color: #1f77b4 !important;
    color: white !important;
    border: 2px solid #1f77b4 !important;
  }
  
  /* Secondary button styling (unselected tab) */
  .stButton > button[data-baseweb="button"] {
    background-color: #f0f2f6 !important;
    color: #262730 !important;
    border: 2px solid #e0e0e0 !important;
  }
  
  /* Hover effects */
  .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  /* Force button state updates */
  .stButton > button[data-baseweb="button"][aria-pressed="true"] {
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
  }
  
  /* Ensure proper button styling for all states */
  .stButton > button[data-baseweb="button"]:not([aria-pressed="true"]) {
    background-color: #f0f2f6 !important;
    color: #262730 !important;
    border-color: #e0e0e0 !important;
  }
  
  /* Logout button styling */
  .stButton > button[key="logout_btn"] {
    background-color: #ff4b4b;
    color: white;
    border: 2px solid #ff4b4b;
  }
  
  .stButton > button[key="logout_btn"]:hover {
    background-color: #e63939;
    border-color: #e63939;
  }
</style>
""", unsafe_allow_html=True)

rerun = getattr(st, "experimental_rerun", lambda: None)
st.set_page_config(page_title="回路構成可否判定シート", layout="wide")

st.markdown(
    """
    <style>
      /* hide ONLY the GitHub repo/fork icon in the header */
      header a[href*="github.com"] {
        display: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── INIT DATABASE ───
init_db()

# ─── AUTHENTICATION ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login")

    # — Login form —
    user = st.text_input("Username", key="login_usr")
    pwd  = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login", key="btn_login"):
        if check_login(user, pwd):
            st.session_state.authenticated = True
            rerun()
        else:
            st.error("❌ Invalid username or password")

    st.markdown("---")

    # — Sign Up —
    with st.expander("📝 Sign Up", expanded=False):
        su = st.text_input("New Username", key="sign_usr")
        sp = st.text_input("New Password", type="password", key="sign_pwd")
        sc = st.text_input("Confirm Password", type="password", key="sign_conf")
        if st.button("Register", key="btn_register"):
            if not su.strip():
                st.error("Username cannot be empty")
            elif sp != sc:
                st.error("Passwords do not match")
            elif create_user(su, sp):
                st.success(f"✅ Account '{su}' created. You may now log in.")
            else:
                st.error(f"Username '{su}' already exists")

    # — Reset Password —
    with st.expander("🔄 Reset Password", expanded=False):
        ru  = st.text_input("Username", key="rst_usr")
        old = st.text_input("Old Password", type="password", key="rst_old")
        new = st.text_input("New Password", type="password", key="rst_new")
        cn  = st.text_input("Confirm New Password", type="password", key="rst_cn")
        if st.button("Reset Password", key="btn_reset"):
            if new != cn:
                st.error("New passwords must match")
            elif not check_login(ru, old):
                st.error("Invalid username or old password")
            else:
                update_password(ru, new)
                st.success("✅ Password updated! Please log in.")

    st.stop()

# ─── HEADER WITH LOGOUT & MENU ───
# Create a header with logout button and menu tabs
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

# Logout button in the rightmost column
with col5:
    if st.button("🔓 Logout", key="logout_btn"):
        st.session_state.show_logout_confirm = True
        rerun()

# Logout confirmation dialog
if st.session_state.get("show_logout_confirm", False):
    # Add overlay and dialog with buttons inside
    st.markdown("""
    <style>
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
    }
    .dialog-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        border: 2px solid #ff4b4b;
        z-index: 1000;
        min-width: 300px;
        text-align: center;
    }
    .dialog-title {
        margin-bottom: 15px;
        color: #333;
        font-size: 18px;
        font-weight: bold;
    }
    .dialog-message {
        margin-bottom: 20px;
        color: #666;
    }
    .dialog-buttons {
        margin-top: 15px;
        display: flex;
        justify-content: center;
        gap: 10px;
    }
    .dialog-button {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        min-width: 80px;
    }
    .btn-yes {
        background-color: #28a745;
        color: white;
    }
    .btn-cancel {
        background-color: #dc3545;
        color: white;
    }
    </style>
    <div class="overlay"></div>
    <div class="dialog-container">
        <div class="dialog-title">🔓 Logout Confirmation</div>
        <div class="dialog-message">Are you sure you want to logout?</div>
        <div class="dialog-buttons">
            <button class="dialog-button btn-yes" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'confirm_logout_clicked'}, '*')">✅ Yes, Logout</button>
            <button class="dialog-button btn-cancel" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'cancel_logout_clicked'}, '*')">❌ Cancel</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hidden buttons to capture JavaScript clicks
    if st.button("", key="confirm_logout_clicked"):
        st.session_state.authenticated = False
        st.session_state.pop("show_logout_confirm", None)
        rerun()
    
    if st.button("", key="cancel_logout_clicked"):
        st.session_state.pop("show_logout_confirm", None)
        rerun()

# Menu tabs in the first 4 columns
with col1:
    pcs_selected = st.button("①PCS入力", key="menu_pcs", type="primary" if st.session_state.get("menu_page", "PCS Settings") == "PCS Settings" else "secondary")
    if pcs_selected:
        st.session_state.menu_page = "PCS Settings"
        rerun()

with col2:
    modules_selected = st.button("②モジュール入力", key="menu_modules", type="primary" if st.session_state.get("menu_page") == "Modules" else "secondary")
    if modules_selected:
        st.session_state.menu_page = "Modules"
        rerun()

with col3:
    circuit_selected = st.button("③回路構成", key="menu_circuit", type="primary" if st.session_state.get("menu_page") == "Circuit Config" else "secondary")
    if circuit_selected:
        st.session_state.menu_page = "Circuit Config"
        rerun()

# Set default page if not set
if "menu_page" not in st.session_state:
    st.session_state.menu_page = "PCS Settings"

page = st.session_state.menu_page

# ─── GLOBAL DIALOG FUNCTIONS ───
def show_delete_confirmation():
    if st.session_state.get("show_delete_confirm", False):
        target = st.session_state.get("delete_target", "")
        delete_type = st.session_state.get("delete_type", "")
        
        # Add overlay and dialog with buttons inside
        st.markdown(f"""
        <style>
        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        }}
        .dialog-container {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 2px solid #ff4b4b;
            z-index: 1000;
            min-width: 300px;
            text-align: center;
        }}
        .dialog-title {{
            margin-bottom: 15px;
            color: #333;
            font-size: 18px;
            font-weight: bold;
        }}
        .dialog-message {{
            margin-bottom: 10px;
            color: #666;
        }}
        .dialog-subtitle {{
            margin-bottom: 20px;
            color: #999;
            font-size: 12px;
        }}
        .dialog-buttons {{
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 10px;
        }}
        .dialog-button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            min-width: 80px;
        }}
        .btn-yes {{
            background-color: #28a745;
            color: white;
        }}
        .btn-cancel {{
            background-color: #dc3545;
            color: white;
        }}
        </style>
        <div class="overlay"></div>
        <div class="dialog-container">
            <div class="dialog-title">🗑️ Delete Confirmation</div>
            <div class="dialog-message">Are you sure you want to delete "{target}"?</div>
            <div class="dialog-subtitle">This action cannot be undone.</div>
            <div class="dialog-buttons">
                <button class="dialog-button btn-yes" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'confirm_delete_clicked'}}, '*')">✅ Yes, Delete</button>
                <button class="dialog-button btn-cancel" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'cancel_delete_clicked'}}, '*')">❌ Cancel</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hidden buttons to capture JavaScript clicks
        if st.button("", key="confirm_delete_clicked"):
            if delete_type == "pcs":
                delete_pcs(target)
            elif delete_type == "module":
                delete_module(target)
            st.session_state.pop("show_delete_confirm", None)
            st.session_state.pop("delete_target", None)
            st.session_state.pop("delete_type", None)
            st.session_state.show_success_dialog = True
            st.session_state.success_message = f"Deleted → {target}"
            rerun()
        
        if st.button("", key="cancel_delete_clicked"):
            st.session_state.pop("show_delete_confirm", None)
            st.session_state.pop("delete_target", None)
            st.session_state.pop("delete_type", None)
            rerun()

def show_success_dialog():
    if st.session_state.get("show_success_dialog", False):
        message = st.session_state.get("success_message", "Operation completed successfully!")
        
        # Add overlay and dialog with button inside
        st.markdown(f"""
        <style>
        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        }}
        .dialog-container {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 2px solid #00ff00;
            z-index: 1000;
            min-width: 300px;
            text-align: center;
        }}
        .dialog-title {{
            margin-bottom: 15px;
            color: #333;
            font-size: 18px;
            font-weight: bold;
        }}
        .dialog-message {{
            margin-bottom: 20px;
            color: #666;
        }}
        .dialog-buttons {{
            margin-top: 15px;
            display: flex;
            justify-content: center;
        }}
        .dialog-button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            min-width: 80px;
            background-color: #28a745;
            color: white;
        }}
        </style>
        <div class="overlay"></div>
        <div class="dialog-container">
            <div class="dialog-title">✅ Success</div>
            <div class="dialog-message">{message}</div>
            <div class="dialog-buttons">
                <button class="dialog-button" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'ok_success_clicked'}}, '*')">✅ OK</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hidden button to capture JavaScript clicks
        if st.button("", key="ok_success_clicked"):
            st.session_state.pop("show_success_dialog", None)
            st.session_state.pop("success_message", None)
            rerun()

def show_edit_confirmation():
    if st.session_state.get("show_edit_confirm", False):
        target = st.session_state.get("edit_target", "")
        edit_type = st.session_state.get("edit_type", "")
        
        # Add overlay and dialog with buttons inside
        st.markdown(f"""
        <style>
        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        }}
        .dialog-container {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 2px solid #1f77b4;
            z-index: 1000;
            min-width: 300px;
            text-align: center;
        }}
        .dialog-title {{
            margin-bottom: 15px;
            color: #333;
            font-size: 18px;
            font-weight: bold;
        }}
        .dialog-message {{
            margin-bottom: 10px;
            color: #666;
        }}
        .dialog-subtitle {{
            margin-bottom: 20px;
            color: #999;
            font-size: 12px;
        }}
        .dialog-buttons {{
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 10px;
        }}
        .dialog-button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            min-width: 80px;
        }}
        .btn-yes {{
            background-color: #28a745;
            color: white;
        }}
        .btn-cancel {{
            background-color: #dc3545;
            color: white;
        }}
        </style>
        <div class="overlay"></div>
        <div class="dialog-container">
            <div class="dialog-title">✏️ Edit Confirmation</div>
            <div class="dialog-message">Do you want to edit "{target}"?</div>
            <div class="dialog-subtitle">You will be able to modify all fields.</div>
            <div class="dialog-buttons">
                <button class="dialog-button btn-yes" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'confirm_edit_clicked'}}, '*')">✅ Yes, Edit</button>
                <button class="dialog-button btn-cancel" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'cancel_edit_clicked'}}, '*')">❌ No, Cancel</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hidden buttons to capture JavaScript clicks
        if st.button("", key="confirm_edit_clicked"):
            if edit_type == "pcs":
                st.session_state["edit_pcs"] = target
            elif edit_type == "module":
                st.session_state["edit_mod"] = target
            st.session_state.pop("show_edit_confirm", None)
            st.session_state.pop("edit_target", None)
            st.session_state.pop("edit_type", None)
            rerun()
        
        if st.button("", key="cancel_edit_clicked"):
            st.session_state.pop("show_edit_confirm", None)
            st.session_state.pop("edit_target", None)
            st.session_state.pop("edit_type", None)
            rerun()

# Show dialogs if needed
show_delete_confirmation()
show_edit_confirmation()
show_success_dialog()

# ─── PAGE 1: PCS Settings ───
if page == "PCS Settings":
    st.header("⚙️ Add / Manage PCS / Inverter Specs")

    # — Add New PCS —
    with st.expander("➕ Add New PCS"):
        name  = st.text_input("PCS Name", key="new_pcs_name")
        c1,c2 = st.columns(2, gap="small")
        max_v = c1.number_input("Max Voltage (V)", key="new_pcs_max")
        min_v = c2.number_input("MPPT Min Voltage (V)", key="new_pcs_min")
        c3,c4 = st.columns(2, gap="small")
        count = c3.number_input("MPPT Inputs", key="new_pcs_count", min_value=1, step=1)
        max_i = c4.number_input("MPPT Max Current (A)", key="new_pcs_cur", format="%.1f")
        if st.button("Save PCS", key="btn_save_pcs"):
            if not name.strip():
                st.error("Name required")
            else:
                save_pcs(name, max_v, min_v, int(count), max_i)
                st.session_state.show_success_dialog = True
                st.session_state.success_message = f"Saved → {name}"
                rerun()

    # — Responsive PCS Table —
    pcs_list = load_pcs()
    if pcs_list:
        st.subheader("■ Saved PCS / Inverters")
        df_pcs = (
            pd.DataFrame.from_dict(pcs_list, orient="index")
              .reset_index()
              .rename(columns={
                  "index":"Name",
                  "max_voltage":"Max V (V)",
                  "mppt_min_voltage":"Min V (V)",
                  "mppt_count":"# MPPT",
                  "mppt_max_current":"Max I (A)"
              })
        )
        st.dataframe(df_pcs, use_container_width=True)

        choice = st.selectbox(
            "Select a PCS to Edit/Delete",
            df_pcs["Name"],
            key="pcs_choice"
        )
        e1,e2 = st.columns(2, gap="small")
        if e1.button("✏️ Edit", key="pcs_edit_btn"):
            st.session_state.show_edit_confirm = True
            st.session_state.edit_target = choice
            st.session_state.edit_type = "pcs"
            rerun()
        if e2.button("🗑️ Delete", key="pcs_del_btn"):
            if st.session_state.get("edit_pcs") == choice:
                st.error("Cannot delete while editing. Please save or cancel the edit first.")
            else:
                st.session_state.show_delete_confirm = True
                st.session_state.delete_target = choice
                st.session_state.delete_type = "pcs"
                rerun()

    # — Edit PCS Form —
    if "edit_pcs" in st.session_state:
        nm = st.session_state["edit_pcs"]
        p  = pcs_list[nm]
        st.subheader(f"✏️ Edit PCS: {nm}")
        new_name = st.text_input("PCS Name", value=nm, key="edit_pcs_name")
        max_v    = st.number_input("Max Voltage (V)",       value=p["max_voltage"], key="edit_pcs_max")
        min_v    = st.number_input("MPPT Min Voltage (V)",  value=p["mppt_min_voltage"], key="edit_pcs_min")
        count    = st.number_input("MPPT Inputs",           value=p["mppt_count"], key="edit_pcs_count", min_value=1, step=1)
        max_i    = st.number_input("MPPT Max Current (A)",  value=p["mppt_max_current"], key="edit_pcs_cur")
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("Save Changes", key="btn_save_pcs_edit"):
                if not new_name.strip():
                    st.error("Name required")
                else:
                    # Delete old entry if name changed
                    if new_name != nm:
                        delete_pcs(nm)
                    # Save new entry
                    save_pcs(new_name, max_v, min_v, int(count), max_i)
                    st.session_state.show_success_dialog = True
                    st.session_state.success_message = f"Updated → {new_name}"
                    st.session_state.pop("edit_pcs", None)
                    rerun()
        with col2:
            if st.button("Cancel", key="btn_cancel_pcs_edit"):
                st.session_state.pop("edit_pcs", None)
                rerun()

# ─── PAGE 2: Modules ───
elif page == "Modules":
    st.header("📥 Add / Manage Solar Panel Modules")

    # — Add New Module —
    with st.expander("➕ Add New Module"):
        m1,m2 = st.columns(2, gap="small")
        manufacturer = m1.text_input("メーカー名", key="new_mod_mfr")
        model_no     = m2.text_input("型番",       key="new_mod_no")
        c1,c2 = st.columns(2, gap="small")
        pmax = c1.number_input("STC Pmax (W)", key="new_mod_pmax")
        voc  = c2.number_input("STC Voc (V)",  key="new_mod_voc")
        c3,c4 = st.columns(2, gap="small")
        vmpp = c3.number_input("NOC Vmpp (V)", key="new_mod_vmpp")
        isc  = c4.number_input("NOC Isc (A)",  key="new_mod_isc")
        tc   = st.number_input("温度係数 (%/℃)", key="new_mod_tc", value=-0.3)
        if st.button("Save Module", key="btn_save_mod"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.session_state.show_success_dialog = True
                st.session_state.success_message = f"Saved → {model_no}"
                rerun()

    # — Responsive Module Table —
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        df_mod = pd.DataFrame([
            {
              "Model No.": mn,
              "メーカー名": m["manufacturer"],
              "Pmax (W)":   m["pmax_stc"],
              "Voc (V)":    m["voc_stc"],
              "Vmpp (V)":   m["vmpp_noc"],
              "Isc (A)":    m["isc_noc"],
              "TempCoeff":  m["temp_coeff"],
            }
            for mn,m in mods.items()
        ])
        st.dataframe(df_mod, use_container_width=True)

        choice = st.selectbox("Select a Module to Edit/Delete",
                              df_mod["Model No."], key="mod_choice")
        m1,m2 = st.columns(2, gap="small")
        if m1.button("✏️ Edit", key="mod_edit_btn"):
            st.session_state.show_edit_confirm = True
            st.session_state.edit_target = choice
            st.session_state.edit_type = "module"
            rerun()
        if m2.button("🗑️ Delete", key="mod_del_btn"):
            if st.session_state.get("edit_mod") == choice:
                st.error("Cannot delete while editing. Please save or cancel the edit first.")
            else:
                st.session_state.show_delete_confirm = True
                st.session_state.delete_target = choice
                st.session_state.delete_type = "module"
                rerun()

    # — Edit Module Form —
    if "edit_mod" in st.session_state:
        mn = st.session_state["edit_mod"]
        d  = mods[mn]
        st.subheader(f"✏️ Edit Module: {mn}")
        mf = st.text_input("メーカー名", value=d["manufacturer"], key="edit_mod_mfr")
        new_model_no = st.text_input("型番", value=mn, key="edit_mod_no")
        pm = st.number_input("STC Pmax (W)",      value=d["pmax_stc"], key="edit_mod_pmax")
        vc = st.number_input("STC Voc (V)",       value=d["voc_stc"],  key="edit_mod_voc")
        vm = st.number_input("NOC Vmpp (V)",      value=d["vmpp_noc"], key="edit_mod_vmpp")
        ic = st.number_input("NOC Isc (A)",       value=d["isc_noc"],  key="edit_mod_isc")
        tc = st.number_input("温度係数 (%/℃)",     value=d["temp_coeff"],key="edit_mod_tc")
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("Save Changes", key="btn_save_mod_edit"):
                if not mf.strip() or not new_model_no.strip():
                    st.error("メーカー名と型番は必須です。")
                else:
                    # Delete old entry if model number changed
                    if new_model_no != mn:
                        delete_module(mn)
                    # Save new entry
                    save_module(mf, new_model_no, pm, vc, vm, ic, tc)
                    st.session_state.show_success_dialog = True
                    st.session_state.success_message = f"Updated → {new_model_no}"
                    st.session_state.pop("edit_mod", None)
                    rerun()
        with col2:
            if st.button("Cancel", key="btn_cancel_mod_edit"):
                st.session_state.pop("edit_mod", None)
                rerun()

# ─── PAGE 3: Circuit Config ───
else:
    st.header("🔢 Series-Only Circuit Configuration")

    # 1) select a saved PCS spec
    pcs_list = load_pcs()
    if not pcs_list:
        st.warning("⚠️ 先に「PCS Settings」タブで PCS/インバータを追加してください。")
        st.stop()
    spec = st.selectbox("Select PCS/Inverter Spec", list(pcs_list.keys()), key="cfg_pcs")
    pcs  = pcs_list[spec]

    # 2) select a module
    mods = load_modules()
    if not mods:
        st.warning("⚠️ 先に「Modules」タブでモジュールを追加してください。")
        st.stop()
    mod_name = st.selectbox("モジュールを選択", list(mods.keys()), key="cfg_mod")
    m = mods[mod_name]

    # 3) temps
    t1, t2 = st.columns(2, gap="small")
    t_min = t1.number_input("設置最低温度 (℃)", key="cfg_tmin", value=-5, step=1)
    t_max = t2.number_input("設置最高温度 (℃)", key="cfg_tmax", value=45, step=1)

    # 4) pull PCS values
    v_max    = pcs["max_voltage"]
    v_mp_min = pcs["mppt_min_voltage"]
    mppt_n   = pcs["mppt_count"]
    i_mppt   = pcs["mppt_max_current"]

    # 5) compute adjusted Voc/Vmpp & series bounds
    voc_a   = m["voc_stc"]*(1 + m["temp_coeff"]/100*(t_min-25))
    vmpp_a  = m["vmpp_noc"]*(1 + m["temp_coeff"]/100*(t_max-25))
    max_s   = math.floor(v_max    / voc_a)  if voc_a>0   else 0
    min_s   = math.ceil (v_mp_min / vmpp_a) if vmpp_a>0 else 0

    st.info(f"直列可能枚数：最小 **{min_s}** 枚 ～ 最大 **{max_s}** 枚", icon="ℹ️")

    # 6) loop per MPPT
    any_err    = False
    total_mods = 0

    for i in range(mppt_n):
        st.divider()
        st.subheader(f"MPPT入力回路 {i+1}")
        ref_s = None
        vals  = []

        for j in range(3):
            c1, c2 = st.columns([3,1], gap="small")
            label = f"回路{j+1} の直列枚数 (0=未使用)"
            c1.write(label)
            key = f"ser_{i}_{j}"
            default = min_s if j==0 else 0
            s = c2.number_input("直列枚数", key=key,
                               min_value=0, max_value=max_s,
                               value=default, step=1)
            vals.append(s)

            if s>0:
                # range check
                if s<min_s or s>max_s:
                    c2.error(f"{s} 枚は範囲外です。{min_s}～{max_s} 枚で入力してください。", icon="🚫")
                    any_err = True
                # consistency check
                if ref_s is None:
                    ref_s = s
                elif s!=ref_s:
                    c2.error("この MPPT内の全回路で同じ枚数を設定してください。", icon="🚫")
                    any_err = True
                total_mods += s

        # current‐sum check
        used = sum(1 for v in vals if v>0)
        if used>0:
            cur = used * m["isc_noc"]
            if cur>i_mppt:
                c1, c2 = st.columns([3,1], gap="small")
                c2.error(f"合計入力電流 {cur:.1f}A が PCS 許容 {i_mppt}A を超えています。\n"
                         "直列枚数または使用回路数を減らしてください。", icon="🚫")
                any_err = True

    # 7) final summary / error
    if any_err:
        st.error("⚠️ 構成にエラーがあります。上記メッセージをご確認ください。")
    elif total_mods == 0:
        st.error("少なくとも1つの回路で直列枚数を入力してください。")
    else:
        power = total_mods * m["pmax_stc"]
        st.success("✅ 全 MPPT 構成は有効です。")
        c1, c2 = st.columns(2, gap="large")
        c1.metric("合計モジュール数", f"{total_mods} 枚")
        c2.metric("合計PV出力", f"{power/1000:.2f} kW")
