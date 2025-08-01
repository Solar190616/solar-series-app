import streamlit as st
import math
import pandas as pd

# safe_rerun: use st.experimental_rerun if it exists, otherwise a no-op
try:
    rerun = st.experimental_rerun
except AttributeError:
    def rerun():
        """No-op when experimental_rerun isn't available."""
        pass
        
# — hide the entire top-right toolbar (share, fork, GitHub icon) —
st.markdown(
    """
    <style>
      /* Streamlit header has two divs: 
         - first for title/logo 
         - second for the toolbar icons */
      header > div:nth-child(2) {
        display: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Safe rerun helper
rerun = getattr(st, "experimental_rerun", lambda: None)

def logout():
    st.session_state.authenticated = False
    rerun()

st.set_page_config(page_title="回路構成可否判定シート", layout="centered")

from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode

from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules, delete_module

# ─── Authentication ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login")
    usr = st.text_input("Username", key="login_usr")
    pwd = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login"):
        if check_login(usr, pwd):
            st.session_state.authenticated = True
            rerun()
        else:
            st.error("❌ Invalid credentials")
    # stop here until they log in
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
        # 1) Module & bounds
        choice = st.selectbox("モジュールを選択", list(mods.keys()), key="calc_mod")
        m = mods[choice]

        t_min = st.number_input("設置場所の最低温度 (℃)", key="calc_tmin", value=-5)
        t_max = st.number_input("設置場所の最高温度 (℃)", key="calc_tmax", value=45)

        v_max    = st.session_state["pcs_max"]
        v_mp_min = st.session_state["pcs_mppt_min"]
        mppt_n   = st.session_state["pcs_mppt_count"]
        i_mppt   = st.session_state["pcs_mppt_current"]

        voc_adj  = m["voc_stc"]  * (1 + m["temp_coeff"]/100*(t_min-25))
        vmpp_adj = m["vmpp_noc"] * (1 + m["temp_coeff"]/100*(t_max-25))
        max_s    = math.floor(v_max    / voc_adj) if voc_adj>0 else 0
        min_s    = math.ceil (v_mp_min/ vmpp_adj) if vmpp_adj>0 else 0

        st.markdown(
            f"**🔧 Adjusted Voc:** {voc_adj:.2f} V   •   "
            f"**🔧 Adjusted Vmpp:** {vmpp_adj:.2f} V"
        )
        st.info(f"直列可能枚数：最小 **{min_s}** 枚 ～ 最大 **{max_s}** 枚")

        total_modules = 0
        any_error = False

        # 2) Loop each MPPT input
        for i in range(mppt_n):
            st.markdown("---")
            ref_series = None
            series_vals = []

            # 2a) Series inputs (3 rows)
            for j in range(3):
                cols = st.columns([1, 2, 2])
                if j == 0:
                    cols[0].markdown(f"**MPPT入力回路{i+1}**")
                else:
                    cols[0].write("")

                cols[1].write(f"回路{j+1}の直列枚数")
                key = f"mppt{i}_ser{j}"
                default = min_s if j == 0 else 0
                s = cols[2].number_input(
                    "", key=key,
                    min_value=0, max_value=max_s,
                    value=default, step=1
                )
                series_vals.append(s)

                # Inline range check
                if s > 0 and (s < min_s or s > max_s):
                    cols[2].error(f"{s} は {min_s}～{max_s} 枚の範囲外です。")
                    any_error = True

                # Inline equality check
                if s > 0:
                    if ref_series is None:
                        ref_series = s
                    elif s != ref_series:
                        cols[2].error("全ての直列枚数を同じにしてください。")
                        any_error = True

            # 2b) Current‐sum check
            branches = sum(1 for v in series_vals if v>0)
            if branches > 0:
                total_current = branches * m["isc_noc"]
                if total_current > i_mppt:
                    # show under first row
                    cols = st.columns([1,2,2])
                    cols[0].write("")  # placeholder
                    cols[1].write("")
                    cols[2].error(
                        f"合計入力電流 {total_current:.1f}A が PCS許容 {i_mppt}A を超えています。"
                    )
                    any_error = True
                else:
                    # accumulate modules only when no error in this group
                    if not any_error:
                        total_modules += branches * ref_series if ref_series else 0

        # 3) Final summary or errors
        if any_error:
            st.error("構成にエラーがあります。上記のメッセージをご確認ください。")
        elif total_modules == 0:
            st.error("少なくとも1つの回路に直列枚数を入力してください。")
        else:
            total_power = total_modules * m["pmax_stc"]
            st.success("✅ 全MPPT構成は有効です。")
            st.write(f"• **合計モジュール数:** {total_modules} 枚")
            st.write(f"• **合計PV出力:** {total_power:.0f} W ({total_power/1000:.2f} kW)")
