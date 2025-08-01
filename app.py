import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules, delete_module

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

st.set_page_config(page_title="回路構成可否判定シート", layout="centered")

# Authentication
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

# Main App
st.sidebar.button("Logout", on_click=logout)
st.title("🔋 回路構成可否判定シート")
st.markdown("This app calculates the **minimum and maximum** number of solar panels connectable in series.")

init_db()

tab1, tab2, tab3 = st.tabs([
    "⚙️ PCS Settings",
    "📥 Add / Manage Solar Module",
    "🔢 Series Calculation"
])

# Tab 1: PCS
with tab1:
    st.subheader("⚙️ PCS Settings")
    st.session_state.pcs_max      = st.number_input("PCS Max Voltage (V)", key="pcs_max", value=600)
    st.session_state.pcs_mppt_min = st.number_input("PCS MPPT Min Voltage (V)", key="pcs_mppt_min", value=250)

# Tab 2: Modules
with tab2:
    st.subheader("📥 Add a New Solar Panel Module")
    # … (add/edit form code) …

    # **Module List Table** – this is the snippet above
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        st.markdown("※使用したい太陽電池パネルの仕様を入力して下さい。…")
        rows = []
        for i, (mn, m) in enumerate(mods.items(), start=1):
            rows.append({
                "No": i,
                "メーカー名":    m["manufacturer"],
                "型番":          mn,
                "STC Pmax(W)":   m["pmax_stc"],
                "STC Voc(V)":    m["voc_stc"],
                "NOC Vmpp(V)":   m["vmpp_noc"],
                "NOC Isc(A)":    m["isc_noc"],
                "温度係数":      m["temp_coeff"],
            })
        df = pd.DataFrame(rows)
        st.table(df)

        # Manage buttons …
        choice = st.selectbox("Select Module", list(mods.keys()), key="manage_select")
        c1, c2 = st.columns(2)
        if c1.button("✏️ Edit"): …
        if c2.button("🗑️ Delete"): …

# Tab 3: Series Calculation
with tab3:
    st.subheader("🔢 Series Calculation")
    mods = load_modules()
    if not mods:
        st.warning("⚠️ No modules to calculate. Add one first.")
    else:
        choice = st.selectbox("Choose a Module", list(mods.keys()), key="calc_mod")
        m = mods[choice]
        t_min = st.number_input("Lowest Site Temp (°C)", value=-5, key="calc_tmin")
        t_max = st.number_input("Highest Site Temp (°C)", value=45, key="calc_tmax")
        pcs_max      = st.session_state.pcs_max
        pcs_mppt_min = st.session_state.pcs_mppt_min

        voc_adj  = m["voc_stc"]  * (1 + m["temp_coeff"]/100 * (t_min - 25))
        vmpp_adj = m["vmpp_noc"] * (1 + m["temp_coeff"]/100 * (t_max - 25))

        max_s = math.floor(pcs_max     / voc_adj)
        min_s = math.ceil (pcs_mppt_min/ vmpp_adj)

        st.subheader("📊 Results")
        st.write(f"**🔧 Adjusted Voc**: {voc_adj:.2f} V")
        st.write(f"**🔧 Adjusted Vmpp**: {vmpp_adj:.2f} V")
        st.success(f"✅ Maximum Series Panels: {max_s}")
        st.success(f"✅ Minimum Series Panels: {min_s}")
