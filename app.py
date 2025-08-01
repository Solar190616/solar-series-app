import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules, delete_module

# safe rerun: no-op if experimental_rerun doesn't exist
rerun = getattr(st, "experimental_rerun", lambda: None)

def logout():
    st.session_state.authenticated = False
    rerun()

st.set_page_config(page_title="回路構成可否判定シート", layout="centered")

# --- Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    tabs = st.tabs(["🔐 Login", "📝 Register", "🔄 Reset Password"])
    with tabs[0]:
        st.title("🔐 Login")
        u = st.text_input("Username", key="login_usr")
        p = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Login"):
            if check_login(u, p):
                st.session_state.authenticated = True
                rerun()
            else:
                st.error("❌ Invalid credentials")
    with tabs[1]:
        st.title("📝 Register")
        ru = st.text_input("Username", key="reg_usr")
        rp = st.text_input("Password", type="password", key="reg_pwd")
        rc = st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.button("Register"):
            if not ru.strip():
                st.error("Username cannot be empty")
            elif rp != rc:
                st.error("Passwords do not match")
            elif create_user(ru, rp):
                st.success("✅ Account created! Please log in.")
            else:
                st.error("❗ Username already exists")
    with tabs[2]:
        st.title("🔄 Reset Password")
        ru  = st.text_input("Username", key="rst_usr")
        old = st.text_input("Old Password", type="password", key="rst_old")
        new = st.text_input("New Password", type="password", key="rst_new")
        cn  = st.text_input("Confirm New Password", type="password", key="rst_confirm")
        if st.button("Reset"):
            if new != cn:
                st.error("New passwords must match")
            elif not check_login(ru, old):
                st.error("Invalid username or old password")
            else:
                update_password(ru, new)
                st.success("✅ Password updated! Please log in.")
    st.stop()

# --- Main App ---
st.sidebar.button("Logout", on_click=logout)
st.title("🔋 回路構成可否判定シート")
st.markdown("This app calculates the **minimum and maximum** number of solar panels connectable in series.")

init_db()

# Three tabs: PCS, Modules, Calculation
tab1, tab2, tab3 = st.tabs([
    "⚙️ PCS Settings",
    "📥 Add / Manage Solar Module",
    "🔢 Series Calculation"
])

# --- Tab 1: PCS Settings ---
with tab1:
    st.subheader("⚙️ PCS Settings")
    st.markdown("Set your inverter/PCS voltage limits here.")
    st.number_input("PCS Max Voltage (V)",      key="pcs_max",      value=600)
    st.number_input("PCS MPPT Min Voltage (V)", key="pcs_mppt_min", value=250)

# --- Tab 2: Add / Manage Modules ---
with tab2:
    st.subheader("📥 Add or Edit a Solar Panel Module")
    mods = load_modules()

    # Edit mode?
    if "edit_module" in st.session_state:
        edit_key = st.session_state.edit_module
        m = mods.get(edit_key, {})
        st.info(f"✏️ Editing module **{edit_key}**")

        manufacturer = st.text_input("メーカー名", value=m.get("manufacturer",""), key="mod_mfr")
        model_no     = st.text_input("型番",       value=edit_key, disabled=True,       key="mod_no")
        pmax         = st.number_input("STC Pmax (W)", value=m.get("pmax_stc",0.0), key="mod_pmax")
        voc          = st.number_input("STC Voc (V)",  value=m.get("voc_stc",0.0),    key="mod_voc")
        vmpp         = st.number_input("NOC Vmpp (V)", value=m.get("vmpp_noc",0.0), key="mod_vmpp")
        isc          = st.number_input("NOC Isc (A)",  value=m.get("isc_noc",0.0),    key="mod_isc")
        tc           = st.number_input("温度係数(%/°C)",  value=m.get("temp_coeff",-0.3),   key="mod_tc")

        c1, c2 = st.columns(2)
        if c1.button("💾 Save Changes"):
            save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
            st.success(f"✅ Updated {model_no}")
            del st.session_state["edit_module"]
            rerun()
        if c2.button("❌ Cancel"):
            del st.session_state["edit_module"]
            rerun()

    else:
        # Add new
        manufacturer = st.text_input("メーカー名", key="mod_mfr_new")
        model_no     = st.text_input("型番",       key="mod_no_new")
        pmax         = st.number_input("STC Pmax (W)", key="mod_pmax_new")
        voc          = st.number_input("STC Voc (V)",  key="mod_voc_new")
        vmpp         = st.number_input("NOC Vmpp (V)", key="mod_vmpp_new")
        isc          = st.number_input("NOC Isc (A)",  key="mod_isc_new")
        tc           = st.number_input("温度係数(%/°C)", key="mod_tc_new", value=-0.3)

        if st.button("➕ Save Module"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("メーカー名と型番は必須項目です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.success(f"✅ Saved {model_no}")
                rerun()

    # Module list always shown
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        st.markdown("※使用したい太陽電池パネルの仕様を入力して下さい。…")
        rows = []
        for i, (mn, m) in enumerate(mods.items(), start=1):
            rows.append({
                "No": i,
                "メーカー名":  m["manufacturer"],
                "型番":        mn,
                "STC Pmax(W)": m["pmax_stc"],
                "STC Voc(V)":  m["voc_stc"],
                "NOC Vmpp(V)": m["vmpp_noc"],
                "NOC Isc(A)":  m["isc_noc"],
                "温度係数":    m["temp_coeff"],
            })
        df = pd.DataFrame(rows)
        st.table(df)

        st.markdown("### ⚙️ Manage Modules")
        choice = st.selectbox("Select Module", list(mods.keys()), key="manage_select")
        c1, c2 = st.columns(2)
        if c1.button("✏️ Edit"):
            st.session_state["edit_module"] = choice
            rerun()
        if c2.button("🗑️ Delete"):
            delete_module(choice)
            st.success(f"✅ Deleted {choice}")
            rerun()

# --- Tab 3: Series Calculation ---
with tab3:
    st.subheader("🔢 Series Calculation")
    mods = load_modules()
    if not mods:
        st.warning("⚠️ No modules to calculate. Add one first.")
    else:
        choice = st.selectbox("Choose a Module", list(mods.keys()), key="calc_mod")
        m = mods[choice]

        t_min = st.number_input("Lowest Site Temp (°C)", key="calc_tmin", value=-5)
        t_max = st.number_input("Highest Site Temp (°C)", key="calc_tmax", value=45)

        pcs_max      = st.session_state.get("pcs_max", 600)
        pcs_mppt_min = st.session_state.get("pcs_mppt_min", 250)

        voc_adj  = m["voc_stc"]  * (1 + m["temp_coeff"]/100 * (t_min - 25))
        vmpp_adj = m["vmpp_noc"] * (1 + m["temp_coeff"]/100 * (t_max - 25))

        max_s = math.floor(pcs_max     / voc_adj)
        min_s = math.ceil (pcs_mppt_min/ vmpp_adj)

        st.subheader("📊 Results")
        st.write(f"**🔧 Adjusted Voc**: {voc_adj:.2f} V")
        st.write(f"**🔧 Adjusted Vmpp**: {vmpp_adj:.2f} V")
        st.success(f"✅ Maximum Series Panels: {max_s}")
        st.success(f"✅ Minimum Series Panels: {min_s}")
