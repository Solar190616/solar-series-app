import streamlit as st
import math
from auth import check_login
from db import init_db, save_module, load_modules

st.set_page_config(page_title="Solar Panel Series Calculator", layout="centered")

# --- Login Section ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login to Solar Config App")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("✅ Login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

# --- App Content ---
st.title("🔋 回路構成可否判定シート")
st.markdown("This app calculates the **minimum and maximum number of solar panels** that can be connected in series.")

init_db()
tab1, tab2 = st.tabs(["📥 Add Solar Module", "🔢 Series Calculation"])

with tab1:
    st.subheader("📥 Add a New Solar Panel Module")
    name = st.text_input("Module Name")
    voc = st.number_input("Voc (V)", value=40.79)
    vmp = st.number_input("Vmp (V)", value=31.92)
    temp_coeff = st.number_input("Temperature Coefficient (%/°C)", value=-0.22)

    if st.button("➕ Save Module"):
        if name.strip():
            save_module(name, voc, vmp, temp_coeff)
            st.success(f"✅ '{name}' saved successfully!")
        else:
            st.error("❗ Module name cannot be empty.")

    modules = load_modules()
    if modules:
        st.markdown("### 📃 Saved Modules")
        for key, val in modules.items():
            st.markdown(f"- **{key}**: Voc={val['voc']} V, Vmp={val['vmp']} V, Temp Coeff={val['temp_coeff']} %/°C")

with tab2:
    st.subheader("🔢 Select Module & Input Conditions")
    modules = load_modules()

    if not modules:
        st.warning("⚠️ No modules found. Please add a module first in the 'Add Solar Module' tab.")
    else:
        module_name = st.selectbox("Choose a Solar Panel Module", list(modules.keys()))
        module = modules[module_name]

        temp_min = st.number_input("Lowest Site Temp (°C)", value=-5)
        temp_max = st.number_input("Highest Site Temp (°C)", value=45)
        pcs_max_v = st.number_input("PCS Max Voltage (V)", value=600)
        pcs_mppt_min = st.number_input("PCS MPPT Min Voltage (V)", value=250)

        voc_adj = module['voc'] * (1 + module['temp_coeff'] / 100 * (temp_min - 25))
        vmp_adj = module['vmp'] * (1 + module['temp_coeff'] / 100 * (temp_max - 25))
        max_series = math.floor(pcs_max_v / voc_adj)
        min_series = math.ceil(pcs_mppt_min / vmp_adj)

        st.subheader("📊 Results")
        st.write(f"**🔧 Adjusted Voc**: {voc_adj:.2f} V")
        st.write(f"**🔧 Adjusted Vmp**: {vmp_adj:.2f} V")
        st.success(f"✅ **Maximum Series Panels**: {max_series}")
        st.success(f"✅ **Minimum Series Panels**: {min_series}")
