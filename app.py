import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import (
    init_db,
    save_module, load_modules, delete_module,
    save_pcs,    load_pcs,    delete_pcs
)

# ─── GLOBAL CSS & PAGE CONFIG ───
st.markdown("""
<style>
  header > div:nth-child(2) { display: none !important; }
  .css-1d391kg { padding: 1rem !important; }
  .css-1lcbmhc { gap: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

rerun = getattr(st, "experimental_rerun", lambda: None)
st.set_page_config(page_title="回路構成可否判定シート", layout="wide")

# ─── INIT DATABASE ───
init_db()

# ─── AUTHENTICATION ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login")

    # — Login form —
    user = st.text_input("Username", key="login_usr")
    pwd  = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login", key="btn_login"):
        if check_login(user, pwd):
            st.session_state.authenticated = True
            rerun()
        else:
            st.error("❌ Invalid username or password")

    st.markdown("---")

    # — Sign Up —
    with st.expander("📝 Sign Up", expanded=False):
        su = st.text_input("New Username", key="sign_usr")
        sp = st.text_input("New Password", type="password", key="sign_pwd")
        sc = st.text_input("Confirm Password", type="password", key="sign_conf")
        if st.button("Register", key="btn_register"):
            if not su.strip():
                st.error("Username cannot be empty")
            elif sp != sc:
                st.error("Passwords do not match")
            elif create_user(su, sp):
                st.success(f"✅ Account '{su}' created. You may now log in.")
            else:
                st.error(f"Username '{su}' already exists")

    # — Reset Password —
    with st.expander("🔄 Reset Password", expanded=False):
        ru  = st.text_input("Username", key="rst_usr")
        old = st.text_input("Old Password", type="password", key="rst_old")
        new = st.text_input("New Password", type="password", key="rst_new")
        cn  = st.text_input("Confirm New Password", type="password", key="rst_cn")
        if st.button("Reset Password", key="btn_reset"):
            if new != cn:
                st.error("New passwords must match")
            elif not check_login(ru, old):
                st.error("Invalid username or old password")
            else:
                update_password(ru, new)
                st.success("✅ Password updated! Please log in.")

    st.stop()

# ─── SIDEBAR & LOGOUT ───
if st.sidebar.button("🔓 Logout"):
    st.session_state.authenticated = False
    rerun()

page = st.sidebar.radio(
    "☰ Menu",
    ["PCS Settings", "Modules", "Circuit Config"],
    key="menu_radio"
)

# ─── PAGE 1: PCS Settings (CRUD) ───
if page == "PCS Settings":
    st.header("⚙️ Add / Manage PCS / Inverter Specs")
    pcs_list = load_pcs()

    # Add new PCS
    with st.expander("➕ Add New PCS", expanded=False):
        name  = st.text_input("PCS Name", key="new_pcs_name")
        c1, c2 = st.columns(2, gap="small")
        max_v = c1.number_input("Max Voltage (V)", key="new_pcs_max")
        min_v = c2.number_input("MPPT Min Voltage (V)", key="new_pcs_min")
        c3, c4 = st.columns(2, gap="small")
        count = c3.number_input("MPPT Inputs", key="new_pcs_count", min_value=1, step=1)
        max_i = c4.number_input("MPPT Max Current (A)", key="new_pcs_cur", format="%.1f")
        if st.button("Save PCS", key="btn_save_pcs"):
            if not name.strip():
                st.error("❗ PCS Name is required.")
            else:
                save_pcs(name, max_v, min_v, int(count), max_i)
                st.success(f"✅ Saved PCS '{name}'")
                rerun()

    # List existing PCS
    if pcs_list:
        st.subheader("■ Saved PCS / Inverters")
        hdr = st.columns([1,2,1,1,1,1,2], gap="small")
        for col, title in zip(hdr, ["No","Name","Max V","Min V","#MPPT","Max I","Actions"]):
            col.markdown(f"**{title}**")
        for idx, (nm,p) in enumerate(pcs_list.items(), start=1):
            cols = st.columns([1,2,1,1,1,1,2], gap="small")
            cols[0].write(idx)
            cols[1].write(nm)
            cols[2].write(p["max_voltage"])
            cols[3].write(p["mppt_min_voltage"])
            cols[4].write(p["mppt_count"])
            cols[5].write(p["mppt_max_current"])
            with cols[6]:
                if st.button("✏️", key=f"edit_pcs_{nm}"):
                    st.session_state["edit_pcs"] = nm
                    rerun()
                if st.button("🗑️", key=f"del_pcs_{nm}"):
                    delete_pcs(nm)
                    st.success(f"🗑️ Deleted '{nm}'")
                    rerun()

    # Edit a PCS
    if "edit_pcs" in st.session_state:
        nm = st.session_state.pop("edit_pcs")
        p  = pcs_list[nm]
        st.subheader(f"✏️ Edit PCS: {nm}")
        new_name = st.text_input("PCS Name", value=nm, key="edit_pcs_name")
        max_v    = st.number_input("Max Voltage (V)", value=p["max_voltage"],   key="edit_pcs_max")
        min_v    = st.number_input("MPPT Min Voltage (V)", value=p["mppt_min_voltage"], key="edit_pcs_min")
        count    = st.number_input("MPPT Inputs", value=p["mppt_count"],   key="edit_pcs_count", min_value=1, step=1)
        max_i    = st.number_input("MPPT Max Current (A)", value=p["mppt_max_current"], key="edit_pcs_cur")
        if st.button("Save Changes", key="btn_save_pcs_edit"):
            save_pcs(new_name, max_v, min_v, int(count), max_i)
            st.success(f"✅ Updated PCS '{new_name}'")
            rerun()

# ─── PAGE 2: Modules (CRUD) ───
elif page == "Modules":
    st.header("📥 Add / Manage Solar Panel Modules")
    mods = load_modules()

    # Add new Module
    with st.expander("➕ Add New Module", expanded=False):
        m1,m2 = st.columns(2, gap="small")
        manufacturer = m1.text_input("メーカー名", key="new_mod_mfr")
        model_no     = m2.text_input("型番",       key="new_mod_no")
        c1,c2 = st.columns(2, gap="small")
        pmax = c1.number_input("STC Pmax (W)", key="new_mod_pmax")
        voc  = c2.number_input("STC Voc (V)",  key="new_mod_voc")
        c3,c4 = st.columns(2, gap="small")
        vmpp = c3.number_input("NOC Vmpp (V)", key="new_mod_vmpp")
        isc  = c4.number_input("NOC Isc (A)",  key="new_mod_isc")
        tc   = st.number_input("温度係数 (%/℃)", key="new_mod_tc", value=-0.3)
        if st.button("Save Module", key="btn_save_mod"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("❗ メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.success(f"✅ Saved Module '{model_no}'")
                rerun()

    # List existing Modules
    if mods:
        st.subheader("■ モジュールリスト")
        hdr = st.columns([1,2,2,1,1,1,1,1,2], gap="small")
        for col,title in zip(hdr, ["No","メーカー","型番","Pmax","Voc","Vmpp","Isc","Tc","Actions"]):
            col.markdown(f"**{title}**")
        for idx,(mn,m) in enumerate(mods.items(), start=1):
            cols = st.columns([1,2,2,1,1,1,1,1,2], gap="small")
            cols[0].write(idx)
            cols[1].write(m["manufacturer"])
            cols[2].write(mn)
            cols[3].write(m["pmax_stc"])
            cols[4].write(m["voc_stc"])
            cols[5].write(m["vmpp_noc"])
            cols[6].write(m["isc_noc"])
            cols[7].write(m["temp_coeff"])
            with cols[8]:
                if st.button("✏️", key=f"edit_mod_{mn}"):
                    st.session_state["edit_mod"] = mn
                    rerun()
                if st.button("🗑️", key=f"del_mod_{mn}"):
                    delete_module(mn)
                    st.success(f"🗑️ Deleted '{mn}'")
                    rerun()

    # Edit a Module
    if "edit_mod" in st.session_state:
        mn = st.session_state.pop("edit_mod")
        d  = mods[mn]
        st.subheader(f"✏️ Edit Module: {mn}")
        mf = st.text_input("メーカー名", value=d["manufacturer"], key="edit_mod_mfr")
        pm = st.number_input("STC Pmax (W)",      value=d["pmax_stc"],  key="edit_mod_pmax")
        vc = st.number_input("STC Voc (V)",       value=d["voc_stc"],   key="edit_mod_voc")
        vm = st.number_input("NOC Vmpp (V)",      value=d["vmpp_noc"],  key="edit_mod_vmpp")
        ic = st.number_input("NOC Isc (A)",       value=d["isc_noc"],   key="edit_mod_isc")
        tc = st.number_input("温度係数 (%/℃)",     value=d["temp_coeff"],key="edit_mod_tc")
        if st.button("Save Changes", key="btn_save_mod_edit"):
            save_module(mf, mn, pm, vc, vm, ic, tc)
            st.success(f"✅ Updated Module '{mn}'")
            rerun()

# ─── PAGE 3: Circuit Config ───
else:
    st.header("🔢 Series-Only Circuit Configuration")

    # 1) select a saved PCS spec
    pcs_list = load_pcs()
    if not pcs_list:
        st.warning("⚠️ 先に「PCS Settings」タブで PCS/インバータを追加してください。")
        st.stop()
    spec = st.selectbox("Select PCS/Inverter Spec", list(pcs_list.keys()), key="cfg_pcs")
    pcs  = pcs_list[spec]

    # 2) select a module
    mods = load_modules()
    if not mods:
        st.warning("⚠️ 先に「Modules」タブでモジュールを追加してください。")
        st.stop()
    mod_name = st.selectbox("モジュールを選択", list(mods.keys()), key="cfg_mod")
    m = mods[mod_name]

    # 3) temps
    t1, t2 = st.columns(2, gap="small")
    t_min = t1.number_input("設置最低温度 (℃)", key="cfg_tmin", value=-5, step=1)
    t_max = t2.number_input("設置最高温度 (℃)", key="cfg_tmax", value=45, step=1)

    # 4) pull PCS values
    v_max    = pcs["max_voltage"]
    v_mp_min = pcs["mppt_min_voltage"]
    mppt_n   = pcs["mppt_count"]
    i_mppt   = pcs["mppt_max_current"]

    # 5) compute adjusted Voc/Vmpp & series bounds
    voc_a   = m["voc_stc"]*(1 + m["temp_coeff"]/100*(t_min-25))
    vmpp_a  = m["vmpp_noc"]*(1 + m["temp_coeff"]/100*(t_max-25))
    max_s   = math.floor(v_max    / voc_a)  if voc_a>0   else 0
    min_s   = math.ceil (v_mp_min / vmpp_a) if vmpp_a>0 else 0

    st.info(f"直列可能枚数：最小 **{min_s}** 枚 ～ 最大 **{max_s}** 枚", icon="ℹ️")

    # 6) loop per MPPT
    any_err    = False
    total_mods = 0

    for i in range(mppt_n):
        st.divider()
        st.subheader(f"MPPT入力回路 {i+1}")
        ref_s = None
        vals  = []

        for j in range(3):
            c1, c2 = st.columns([3,1], gap="small")
            label = f"回路{j+1} の直列枚数 (0=未使用)"
            c1.write(label)
            key = f"ser_{i}_{j}"
            default = min_s if j==0 else 0
            s = c2.number_input("", key=key,
                                 min_value=0, max_value=max_s,
                                 value=default, step=1)
            vals.append(s)

            if s>0:
                # range check
                if s<min_s or s>max_s:
                    c2.error(f"{s} 枚は範囲外です。{min_s}～{max_s} 枚で入力してください。", icon="🚫")
                    any_err = True
                # consistency check
                if ref_s is None:
                    ref_s = s
                elif s!=ref_s:
                    c2.error("この MPPT内の全回路で同じ枚数を設定してください。", icon="🚫")
                    any_err = True
                total_mods += s

        # current‐sum check
        used = sum(1 for v in vals if v>0)
        if used>0:
            cur = used * m["isc_noc"]
            if cur>i_mppt:
                c1, c2 = st.columns([3,1], gap="small")
                c2.error(f"合計入力電流 {cur:.1f}A が PCS 許容 {i_mppt}A を超えています。\n"
                         "直列枚数または使用回路数を減らしてください。", icon="🚫")
                any_err = True

    # 7) final summary / error
    if any_err:
        st.error("⚠️ 構成にエラーがあります。上記メッセージをご確認ください。")
    elif total_mods == 0:
        st.error("少なくとも1つの回路で直列枚数を入力してください。")
    else:
        power = total_mods * m["pmax_stc"]
        st.success("✅ 全 MPPT 構成は有効です。")
        c1, c2 = st.columns(2, gap="large")
        c1.metric("合計モジュール数", f"{total_mods} 枚")
        c2.metric("合計PV出力", f"{power/1000:.2f} kW")
