import streamlit as st
import math
import pandas as pd
from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

st.set_page_config(page_title="回路構成可否判定シート", layout="centered")

# ─── Authentication ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    tabs = st.tabs(["🔐 Login", "📝 Register", "🔄 Reset Password"])
    # Login Tab
    with tabs[0]:
        st.title("🔐 Login")
        usr = st.text_input("Username", key="login_usr")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Login"):
            if check_login(usr, pwd):
                st.session_state.authenticated = True
                st.session_state.username = usr
                st.success("✅ Logged in")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials")
    # Register Tab
    with tabs[1]:
        st.title("📝 Register")
        new_u = st.text_input("Username", key="reg_usr")
        new_p = st.text_input("Password", type="password", key="reg_pwd")
        new_pc= st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.button("Register"):
            if not new_u.strip():
                st.error("Username cannot be empty")
            elif new_p != new_pc:
                st.error("Passwords do not match")
            elif create_user(new_u, new_p):
                st.success("✅ Account created! Please login.")
            else:
                st.error("❗ Username exists")
    # Reset Tab
    with tabs[2]:
        st.title("🔄 Reset Password")
        ru  = st.text_input("Username", key="rst_usr")
        ro  = st.text_input("Old Password", type="password", key="rst_old")
        rn  = st.text_input("New Password", type="password", key="rst_new")
        rnc = st.text_input("Confirm New Password", type="password", key="rst_confirm")
        if st.button("Reset"):
            if rn != rnc:
                st.error("New passwords must match")
            elif not check_login(ru, ro):
                st.error("Invalid username or old password")
            else:
                update_password(ru, rn)
                st.success("✅ Password updated! Please login.")
    st.stop()

# ─── Main App ───
st.sidebar.button("Logout", on_click=logout)
st.title("🔋 回路構成可否判定シート")
st.markdown("This app calculates the **minimum and maximum** number of solar panels connectable in series.")

init_db()
tab1, tab2 = st.tabs(["📥 Add Solar Module", "🔢 Series Calculation"])

# ─── Tab 1: Add & List Modules ───
with tab1:
    st.subheader("📥 Add a New Solar Panel Module")
    manufacturer = st.text_input("メーカー名 (Manufacturer)")
    model_no     = st.text_input("型番 (Model No.)")
    pmax         = st.number_input("【STC】最大出力, Pmax (W)", value=0.0)
    voc          = st.number_input("【STC】開放電圧, Voc (V)",    value=40.79)
    vmpp         = st.number_input("【NOC】動作電圧, Vmpp (V)",   value=31.92)
    isc          = st.number_input("【NOC】短絡電流, Isc (A)",    value=8.50)
    tc           = st.number_input(
        "開放電圧(Voc)の温度係数（%/°C）※不明な時は-0.3として下さい。", 
        value=-0.30
    )

    if st.button("➕ Save Module"):
        if not manufacturer.strip() or not model_no.strip():
            st.error("メーカー名と型番は必須項目です。")
        else:
            save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
            st.success(f"✅ Saved: {manufacturer} {model_no}")

    # Show module list as a table
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        st.markdown("※使用したい太陽電池パネルの仕様を入力して下さい。…")
        rows = []
        for i, (mn, m) in enumerate(mods.items(), start=1):
            rows.append({
                "No": i,
                "メーカー名":              m["manufacturer"],
                "型番":                    mn,
                "【STC】Pmax(W)":          m["pmax_stc"],
                "【STC】Voc(V)":           m["voc_stc"],
                "【NOC】Vmpp(V)":          m["vmpp_noc"],
                "【NOC】Isc(A)":           m["isc_noc"],
                "温度係数(%/°C)":          m["temp_coeff"],
            })
        df = pd.DataFrame(rows)
        st.table(df)

# ─── Tab 2: Series Calculation ───
with tab2:
    st.subheader("🔢 Select Module & Input Conditions")
    mods = load_modules()
    if not mods:
        st.warning("⚠️ No modules yet. Add one in the first tab.")
    else:
        choice = st.selectbox("Choose a Module", list(mods.keys()))
        m = mods[choice]

        t_min = st.number_input("Lowest Site Temp (°C)", value=-5)
        t_max = st.number_input("Highest Site Temp (°C)", value=45)
        v_max = st.number_input("PCS Max Voltage (V)",     value=600)
        v_mp_min = st.number_input("PCS MPPT Min Voltage (V)", value=250)

        # --- Corrected calculations ---
        voc_adj = m["voc_stc"] * (1 + m["temp_coeff"]/100 * (t_min - 25))
        vmpp_adj= m["vmpp_noc"] * (1 + m["temp_coeff"]/100 * (t_max - 25))

        max_series = math.floor(v_max    / voc_adj)
        min_series = math.ceil (v_mp_min / vmpp_adj)

        st.subheader("📊 Results")
        st.write(f"**🔧 Adjusted Voc**: {voc_adj:.2f} V")
        st.write(f"**🔧 Adjusted Vmpp**: {vmpp_adj:.2f} V")
        st.success(f"✅ Maximum Series Panels: {max_series}")
        st.success(f"✅ Minimum Series Panels: {min_series}")
