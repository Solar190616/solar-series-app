import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules, delete_module

# Safe rerun helper
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
    # … same login/register/reset code as before …
    with tabs[0]:
        u = st.text_input("Username", key="login_usr")
        p = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Login"):
            if check_login(u, p):
                st.session_state.authenticated = True
                rerun()
            else:
                st.error("❌ Invalid credentials")
    with tabs[1]:
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
st.markdown(
    "This app calculates the **minimum and maximum** number of solar panels connectable in series, "
    "**parallel** strings, total modules, and total PV output."
)

init_db()

tab1, tab2, tab3 = st.tabs([
    "⚙️ PCS Settings",
    "📥 Add / Manage Solar Module",
    "🔢 Series & Parallel Calculation"
])

# --- Tab 1: PCS / Inverter Settings ---
with tab1:
    st.subheader("⚙️ PCS / Inverter Settings")
    st.markdown("Set your inverter/PCS voltage limits here.")

    # ← Set these to your new defaults:
    st.number_input(
        "PCS Max Voltage (V)",
        key="pcs_max",
        value=450,      # default changed from 600 to 450
        step=1,
    )
    st.number_input(
        "PCS MPPT Min Voltage (V)",
        key="pcs_mppt_min",
        value=35,       # default changed from 250 to 35
        step=1,
    )
    st.number_input(
        "Number of MPPT Inputs",
        key="pcs_mppt_count",
        value=3,        # default kept at 3
        min_value=1,
        step=1,
    )
    st.number_input(
        "PCS MPPT Max Current (A)",
        key="pcs_mppt_current",
        value=14.0,     # default changed to 14.0
        format="%.1f",
        step=0.1,
    )

# --- Tab 2: Add / Manage Solar Module ---
with tab2:
    st.subheader("📥 Add or Edit a Solar Panel Module")
    mods = load_modules()

    # Edit mode?
    if "edit_module" in st.session_state:
        key = st.session_state.edit_module
        m = mods.get(key, {})
        st.info(f"✏️ Editing **{key}**")

        manufacturer = st.text_input("メーカー名", value=m.get("manufacturer",""), key="mod_mfr")
        model_no     = st.text_input("型番",     value=key,            disabled=True, key="mod_no")
        pmax         = st.number_input("STC Pmax (W)", value=m.get("pmax_stc",0.0), key="mod_pmax")
        voc          = st.number_input("STC Voc (V)",  value=m.get("voc_stc",0.0),  key="mod_voc")
        vmpp         = st.number_input("NOC Vmpp (V)", value=m.get("vmpp_noc",0.0), key="mod_vmpp")
        isc          = st.number_input("NOC Isc (A)",  value=m.get("isc_noc",0.0),  key="mod_isc")
        tc           = st.number_input("温度係数(%/°C)",  value=m.get("temp_coeff",-0.3), key="mod_tc")

        c1, c2 = st.columns(2)
        if c1.button("💾 Save Changes"):
            save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
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
                st.error("メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                rerun()

    # Inline Table with Edit/Delete
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        # header
        hdr_cols = st.columns([1,2,2,1,1,1,1,1,2])
        headers = ["No","メーカー名","型番","Pmax(W)","Voc(V)",
                   "Vmpp(V)","Isc(A)","温度係数","Actions"]
        for col, h in zip(hdr_cols, headers):
            col.markdown(f"**{h}**")

        # rows
        for idx, (mn, m) in enumerate(mods.items(), start=1):
            row_cols = st.columns([1,2,2,1,1,1,1,1,2])
            row_cols[0].write(idx)
            row_cols[1].write(m["manufacturer"])
            row_cols[2].write(mn)
            row_cols[3].write(m["pmax_stc"])
            row_cols[4].write(m["voc_stc"])
            row_cols[5].write(m["vmpp_noc"])
            row_cols[6].write(m["isc_noc"])
            row_cols[7].write(m["temp_coeff"])
            with row_cols[8]:
                if st.button("✏️", key=f"edit_{mn}"):
                    st.session_state["edit_module"] = mn
                    rerun()
                if st.button("🗑️", key=f"del_{mn}"):
                    delete_module(mn)
                    rerun()

# --- Tab 3: Series‐Only Configuration per MPPT Input ---
with tab3:
    st.subheader("🔢 回路構成入力（直列のみ）")

    mods = load_modules()
    if not mods:
        st.warning("⚠️ 先にモジュールを登録してください。")
    else:
        # Module & temp settings
        choice = st.selectbox("モジュールを選択", list(mods.keys()), key="calc_mod")
        m = mods[choice]
        t_min = st.number_input("設置最低温度 (℃)", key="calc_tmin", value=-5, step=1)
        t_max = st.number_input("設置最高温度 (℃)", key="calc_tmax", value=45, step=1)

        # Compute adjusted voltages & series bounds
        v_max    = st.session_state["pcs_max"]
        v_mp_min = st.session_state["pcs_mppt_min"]
        mppt_n   = st.session_state["pcs_mppt_count"]

        voc_adj  = m["voc_stc"]  * (1 + m["temp_coeff"]/100*(t_min-25))
        vmpp_adj = m["vmpp_noc"] * (1 + m["temp_coeff"]/100*(t_max-25))
        max_s    = math.floor(v_max    / voc_adj) if voc_adj>0 else 0
        min_s    = math.ceil (v_mp_min/ vmpp_adj) if vmpp_adj>0 else 0

        st.markdown(
            f"**🔧 Voc:** {voc_adj:.2f} V   • **🔧 Vmpp:** {vmpp_adj:.2f} V"
        )
        st.info(f"直列可能枚数：最小 {min_s} 枚 〜 最大 {max_s} 枚", icon="ℹ️")

        total_modules = 0
        any_error = False

        # Loop over each MPPT input
        for i in range(mppt_n):
            st.divider()  # slimline separator
            st.markdown(f"**MPPT入力回路 {i+1}**")
            ref_s = None

            # Three sub-circuits
            for j in range(3):
                label = f"回路{j+1}の直列枚数"
                default = min_s if j == 0 else 0

                col1, col2 = st.columns([3,1], gap="small")
                col1.write(label)
                s = col2.number_input(
                    "", key=f"mppt{i}_ser{j}",
                    min_value=0, max_value=max_s,
                    value=default, step=1
                )

                # Inline validations
                if s>0:
                    if s < min_s or s > max_s:
                        col2.error(f"{s} は {min_s}〜{max_s} の範囲外です。")
                        any_error = True
                    if ref_s is None:
                        ref_s = s
                    elif s != ref_s:
                        col2.error("全て同じ枚数にして下さい。")
                        any_error = True
                    total_modules += s

        # Final summary or error
        if any_error:
            st.error("❌ エラーがあります。上記を修正してください。")
        elif total_modules == 0:
            st.error("少なくとも１つの回路を使ってください。")
        else:
            total_power = total_modules * m["pmax_stc"]
            st.success("✅ 全MPPT構成は有効です。")
            st.write(f"• 合計モジュール数: {total_modules} 枚")
            st.write(f"• 合計PV出力: {total_power:.0f} W ({total_power/1000:.2f} kW)")

