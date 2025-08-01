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

    # … your Add / Edit form logic here …

    # — Inline module list with Edit/Delete buttons —
    if mods:
        st.subheader("■ モジュールリスト")
        st.markdown("※使用したい太陽電池パネルの仕様を入力して下さい。…")

        # table header
        header_cols = st.columns([1, 2, 2, 1,1,1,1,1,2])
        headers = [
            "No", "メーカー名", "型番",
            "Pmax(W)", "Voc(V)", "Vmpp(V)", "Isc(A)",
            "温度係数", "Actions"
        ]
        for col, h in zip(header_cols, headers):
            col.markdown(f"**{h}**")

        # rows
        for i, (mn, m) in enumerate(mods.items(), start=1):
            row_cols = st.columns([1, 2, 2, 1,1,1,1,1,2])
            # data columns
            row_cols[0].write(i)
            row_cols[1].write(m["manufacturer"])
            row_cols[2].write(mn)
            row_cols[3].write(m["pmax_stc"])
            row_cols[4].write(m["voc_stc"])
            row_cols[5].write(m["vmpp_noc"])
            row_cols[6].write(m["isc_noc"])
            row_cols[7].write(m["temp_coeff"])
            # action buttons
            with row_cols[8]:
                if st.button("✏️ Edit", key=f"edit_{mn}"):
                    st.session_state.edit_module = mn
                    st.experimental_rerun()
                if st.button("🗑️ Delete", key=f"del_{mn}"):
                    delete_module(mn)
                    st.success(f"✅ Deleted {mn}")
                    st.experimental_rerun()

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
