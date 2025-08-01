import pandas as pd
import streamlit as st
import math
from auth import check_login, create_user, update_password
from db import init_db, save_module, load_modules

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

st.set_page_config(page_title="Solar Panel Series Calculator", layout="centered")

# --- Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    st.sidebar.button("Logout", on_click=logout)
else:
    auth_tabs = st.tabs(["🔐 Login", "📝 Register", "🔄 Reset Password"])
    with auth_tabs[0]:
        st.title("🔐 Login to Solar Config App")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if check_login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials")
    with auth_tabs[1]:
        st.title("📝 Register New Account")
        new_user = st.text_input("Username", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.button("Register"):
            if not new_user.strip():
                st.error("❗ Username cannot be empty")
            elif new_pass != confirm_pass:
                st.error("❗ Passwords do not match")
            elif create_user(new_user, new_pass):
                st.success("✅ Account created! Please login.")
            else:
                st.error("❗ Username already exists")
    with auth_tabs[2]:
        st.title("🔄 Reset Password")
        rp_user = st.text_input("Username", key="reset_user")
        rp_old = st.text_input("Old Password", type="password", key="reset_old")
        rp_new = st.text_input("New Password", type="password", key="reset_new")
        rp_confirm = st.text_input("Confirm New Password", type="password", key="reset_confirm")
        if st.button("Reset Password"):
            if rp_new != rp_confirm:
                st.error("❗ New passwords do not match")
            elif not check_login(rp_user, rp_old):
                st.error("❌ Invalid username or old password")
            else:
                update_password(rp_user, rp_new)
                st.success("✅ Password updated! Please login.")
    st.stop()

# --- Main App Content ---
st.title("🔋 回路構成可否判定シート")
st.markdown("This app calculates the **minimum and maximum number of solar panels** that can be connected in series.")

init_db()
tab1, tab2 = st.tabs(["📥 Add Solar Module", "🔢 Series Calculation"])

with tab1:
    st.subheader("📥 Add a New Solar Panel Module")

    manufacturer  = st.text_input("メーカー名 (Manufacturer)", key="mod_maker")
    model_number  = st.text_input("型番 (Model No.)",       key="mod_no")
    pmax          = st.number_input("【STC】最大出力, Pmax (W)",      value=0.0)
    voc           = st.number_input("【STC】開放電圧, Voc (V)",       value=40.79)
    vmpp          = st.number_input("【NOC】動作電圧, Vmpp (V)",      value=31.92)
    isc           = st.number_input("【NOC】短絡電流, Isc (A)",       value=8.50)
    temp_coeff    = st.number_input(
                        "開放電圧(Voc)の温度係数（%/°C）※不明な時は-0.3として下さい。",
                        value=-0.30
                    )

    if st.button("➕ Save Module"):
        if not manufacturer.strip() or not model_number.strip():
            st.error("❗ メーカー名と型番は必須項目です。")
        else:
            save_module(manufacturer, model_number, pmax, voc, vmpp, isc, temp_coeff)
            st.success(f"✅ '{manufacturer} {model_number}' saved!")

   # ── after save_module() and load_modules() ──
modules = load_modules()
if modules:
    st.subheader("■ モジュールリスト")
    st.markdown("※使用したい太陽電池パネルの仕様を入力して下さい。正しく入力されていない場合は、構成可否判定が正しくできませんので、記入間違いがないように入力して下さい。")

    # build rows
    rows = []
    for idx, (model_no, m) in enumerate(modules.items(), start=1):
        rows.append({
            "No": idx,
            "メーカー名":       m["manufacturer"],
            "型番":             model_no,
            "【STC】最大出力 Pmax(W)":    m["pmax"],
            "【STC】開放電圧 Voc(V)":     m["voc"],
            "【NOC】動作電圧 Vmpp(V)":    m["vmpp"],
            "【NOC】短絡電流 Isc(A)":     m["isc"],
            "開放電圧(Voc)の温度係数 (%/°C) ※不明な時は-0.3として下さい。": m["temp_coeff"],
        })

    df = pd.DataFrame(rows)
    # display as static table
    st.table(df)

with tab2:
    st.subheader("🔢 Select Module & Input Conditions")
    modules = load_modules()

    if not modules:
        st.warning("⚠️ No modules found. Please add a module first in the 'Add Solar Module' tab.")
    else:
        module_name = st.selectbox("Choose a Solar Panel Module", list(modules.keys()), key="select_mod")
        module = modules[module_name]

        temp_min = st.number_input("Lowest Site Temp (°C)", value=-5, key="site_min")
        temp_max = st.number_input("Highest Site Temp (°C)", value=45, key="site_max")
        pcs_max_v = st.number_input("PCS Max Voltage (V)", value=600, key="pcs_max")
        pcs_mppt_min = st.number_input("PCS MPPT Min Voltage (V)", value=250, key="pcs_min")

        voc_adj = module['voc'] * (1 + module['temp_coeff']/100*(temp_min-25))
        vmp_adj = module['vmp'] * (1 + module['temp_coeff']/100*(temp_max-25))
        max_series = math.floor(pcs_max_v / voc_adj)
        min_series = math.ceil(pcs_mppt_min / vmp_adj)

        st.subheader("📊 Results")
        st.write(f"**🔧 Adjusted Voc**: {voc_adj:.2f} V")
        st.write(f"**🔧 Adjusted Vmp**: {vmp_adj:.2f} V")
        st.success(f"✅ **Maximum Series Panels**: {max_series}")
        st.success(f"✅ **Minimum Series Panels**: {min_series}")
