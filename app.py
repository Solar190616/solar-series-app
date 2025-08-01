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

# --- Tab 1: PCS Settings ---
with tab1:
    st.subheader("⚙️ PCS / Inverter Settings")
    st.number_input("PCS Max Voltage (V)",      key="pcs_max",       value=600)
    st.number_input("PCS MPPT Min Voltage (V)", key="pcs_mppt_min",  value=250)
    st.number_input("Number of MPPT Inputs",    key="pcs_mppt_count",value=3, min_value=1)
    st.number_input("PCS MPPT Max Current (A)", key="pcs_mppt_current", value=14.0, format="%.1f")

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

# --- Tab 3: Series & Parallel Calculation ---
with tab3:
    st.subheader("🔢 Series & Parallel Configuration")

    mods = load_modules()
    if not mods:
        st.warning("⚠️ No modules to calculate. Add one first in the previous tab.")
    else:
        # 1) Select module & compute min/max series
        choice = st.selectbox("Choose Module", list(mods.keys()), key="calc_mod")
        m = mods[choice]

        t_min = st.number_input("Lowest Site Temp (℃)",  key="calc_tmin", value=-5)
        t_max = st.number_input("Highest Site Temp (℃)", key="calc_tmax", value=45)

        # PCS settings
        v_max    = st.session_state.get("pcs_max",       600)
        v_mp_min = st.session_state.get("pcs_mppt_min",  250)
        mppt_n   = st.session_state.get("pcs_mppt_count", 3)
        i_mppt   = st.session_state.get("pcs_mppt_current", 14.0)

        # Series calculation
        voc_adj  = m["voc_stc"]  * (1 + m["temp_coeff"]/100*(t_min - 25))
        vmpp_adj = m["vmpp_noc"] * (1 + m["temp_coeff"]/100*(t_max - 25))
        max_s    = math.floor(v_max    / voc_adj) if voc_adj>0 else 0
        min_s    = math.ceil (v_mp_min/ vmpp_adj) if vmpp_adj>0 else 0

        st.markdown(f"**🔧 Adjusted Voc:** {voc_adj:.2f} V   •   **🔧 Adjusted Vmpp:** {vmpp_adj:.2f} V")
        st.info(f"直列可能枚数：最小 **{min_s}** 枚 ～ 最大 **{max_s}** 枚")

        # 2) Input series per MPPT circuit
        st.subheader("■ 回路ごとの直列枚数入力")
        st.markdown("各MPPT回路に直列枚数を入力して下さい（0 = 未使用）")
        series_cols = st.columns(mppt_n)
        series_counts = []
        for i in range(mppt_n):
            cnt = series_cols[i].number_input(
                f"回路{i+1}直列枚数", min_value=0, value=min_s, step=1, key=f"ser_{i}"
            )
            series_counts.append(cnt)

        # 3) Input parallel-string count per MPPT circuit
        st.subheader("■ 回路ごとの並列ストリング数入力")
        st.markdown("各MPPT回路に並列ストリング本数を入力して下さい（1以上）")
        parallel_cols = st.columns(mppt_n)
        parallel_counts = []
        for i in range(mppt_n):
            pc = parallel_cols[i].number_input(
                f"回路{i+1}並列本数", min_value=1, value=1, step=1, key=f"par_{i}"
            )
            parallel_counts.append(pc)

        # 4) Validation
        errors = []
        # series validation
        used_series = [c for c in series_counts if c>0]
        if not used_series:
            errors.append("少なくとも1つの回路に直列枚数を入力して下さい。")
        else:
            for idx, c in enumerate(used_series, start=1):
                if c < min_s or c > max_s:
                    errors.append(f"回路{idx}の直列枚数は {min_s}～{max_s} の範囲で入力して下さい。")
            if len(set(used_series))>1:
                errors.append("全回路の直列枚数を同じにして下さい。")

        # parallel validation
        for idx, p in enumerate(parallel_counts, start=1):
            max_par = math.floor(i_mppt / m["isc_noc"]) if m["isc_noc"]>0 else 0
            if p < 1:
                errors.append(f"回路{idx}の並列本数は1以上で入力して下さい。")
            elif p > max_par:
                errors.append(f"回路{idx}の並列本数は最大 {max_par} 本まで可能です。")

        # 5) Show errors or results
        if errors:
            for e in errors:
                st.error("❌ " + e)
        else:
            # assume all series same
            series = used_series[0]
            total_modules = sum( series * p for p in parallel_counts if series>0 )
            total_power_w = total_modules * m["pmax_stc"]

            st.success("✅ 構成は有効です。")
            st.write(f"• **稼働回路数:** {sum(1 for c in series_counts if c>0)} 回路")
            st.write(f"• **直列枚数／回路:** {series} 枚")
            st.write(f"• **並列本数／回路:** {parallel_counts[0]} 本")
            st.write(f"• **合計モジュール数:** {total_modules} 枚")
            st.write(f"• **合計PV出力:** {total_power_w:.0f} W ({total_power_w/1000:.2f} kW)")

