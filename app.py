import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

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
                st.experimental_rerun()
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
        opw = st.text_input("Old Password", type="password", key="rst_old")
        npw = st.text_input("New Password", type="password", key="rst_new")
        cn  = st.text_input("Confirm New Password", type="password", key="rst_confirm")
        if st.button("Reset"):
            if npw != cn:
                st.error("New passwords must match")
            elif not check_login(ru, opw):
                st.error("Invalid username or old password")
            else:
                update_password(ru, npw)
                st.success("✅ Password updated! Please log in.")
    st.stop()

# --- Main App ---
st.sidebar.button("Logout", on_click=logout)
st.title("🔋 回路構成可否判定シート")
st.markdown("This app calculates the **minimum and maximum** number of solar panels connectable in series.")

# Ensure database exists
init_db()

# Set up three tabs: PCS, Module, Calculation
tab1, tab2, tab3 = st.tabs([
    "⚙️ PCS Settings",
    "📥 Add Solar Module",
    "🔢 Series Calculation"
])

# --- Tab 1: PCS Settings ---
with tab1:
    st.subheader("⚙️ PCS Settings")
    st.markdown("Set your inverter/PCS voltage limits here.")
    # these keys auto-persist in session_state
    st.number_input("PCS Max Voltage (V)",      key="pcs_max",     value=600)
    st.number_input("PCS MPPT Min Voltage (V)", key="pcs_mppt_min",value=250)

# --- Tab 2: Add Solar Module ---
with tab2:
    st.subheader("📥 Add a New Solar Panel Module")
    manufacturer = st.text_input("メーカー名 (Manufacturer)", key="mod_mfr")
    model_no     = st.text_input("型番 (Model No.)",           key="mod_no")
    pmax         = st.number_input("【STC】最大出力, Pmax (W)", key="mod_pmax")
    voc          = st.number_input("【STC】開放電圧, Voc (V)",  key="mod_voc")
    vmpp         = st.number_input("【NOC】動作電圧, Vmpp (V)", key="mod_vmpp")
    isc          = st.number_input("【NOC】短絡電流, Isc (A)",  key="mod_isc")
    tc           = st.number_input(
        "開放電圧(Voc)の温度係数（%/°C）※不明な時は-0.3として下さい。",
        key="mod_tc", value=-0.30
    )

    if st.button("➕ Save Module"):
        if not manufacturer.strip() or not model_no.strip():
            st.error("メーカー名と型番は必須項目です。")
        else:
            save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
            st.success(f"✅ Saved: {manufacturer} {model_no}")

    # Display module list
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        st.markdown("※使用したい太陽電池パネルの仕様を入力して下さい。…")
        rows = []
        for i, (mn, m) in enumerate(mods.items(), start=1):
            rows.append({
                "No": i,
                "メーカー名":       m["manufacturer"],
                "型番":             mn,
                "【STC】Pmax(W)":   m["pmax_stc"],
                "【STC】Voc(V)":    m["voc_stc"],
                "【NOC】Vmpp(V)":   m["vmpp_noc"],
                "【NOC】Isc(A)":    m["isc_noc"],
                "温度係数(%/°C)":   m["temp_coeff"],
            })
        df = pd.DataFrame(rows)
        st.table(df)

# --- Tab 3: Series Calculation ---
with tab3:
    st.subheader("🔢 Select Module & Input Conditions")
    mods = load_modules()
    if not mods:
        st.warning("⚠️ No modules yet. Add one in the PCS/Module tabs.")
    else:
        choice = st.selectbox("Choose a Module", list(mods.keys()), key="calc_mod")
        m = mods[choice]

        t_min = st.number_input("Lowest Site Temp (°C)",    key="calc_tmin", value=-5)
        t_max = st.number_input("Highest Site Temp (°C)",   key="calc_tmax", value=45)

        # grab PCS settings from tab1
        pcs_max     = st.session_state.pcs_max
        pcs_mppt_min= st.session_state.pcs_mppt_min

        # calculations
        voc_adj  = m["voc_stc"]  * (1 + m["temp_coeff"]/100 * (t_min - 25))
        vmpp_adj = m["vmpp_noc"] * (1 + m["temp_coeff"]/100 * (t_max - 25))

        max_s = math.floor(pcs_max     / voc_adj)
        min_s = math.ceil (pcs_mppt_min/ vmpp_adj)

        st.subheader("📊 Results")
        st.write(f"**🔧 Adjusted Voc**: {voc_adj:.2f} V")
        st.write(f"**🔧 Adjusted Vmpp**: {vmpp_adj:.2f} V")
        st.success(f"✅ Maximum Series Panels: {max_s}")
        st.success(f"✅ Minimum Series Panels: {min_s}")
