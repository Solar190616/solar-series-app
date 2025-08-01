import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import (
    init_db,
    save_module, load_modules, delete_module,
    save_pcs,    load_pcs,    delete_pcs
)

# ─── AUTHENTICATION & ACCOUNT MANAGEMENT ───
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

    # — Sign Up (create a new account) —
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
        ru = st.text_input("Username", key="rst_usr")
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

    # prevent access to the rest of the app until authenticated
    st.stop()

# ─── GLOBAL CSS & CONFIG ───
st.markdown("""
<style>
  header > div:nth-child(2) {display: none !important;}
  .css-1d391kg {padding: 1rem !important;}
  .css-1lcbmhc {gap: 0.5rem !important;}
</style>
""", unsafe_allow_html=True)

rerun = getattr(st, "experimental_rerun", lambda: None)
st.set_page_config(page_title="回路構成可否判定シート", layout="wide")

# ─── INITIALIZE DB ───
init_db()

# ─── AUTHENTICATION ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login")
    u = st.text_input("Username", key="login_usr")
    p = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login", key="btn_login"):
        if check_login(u, p):
            st.session_state.authenticated = True
            rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ─── SIDEBAR & LOGOUT ───
if st.sidebar.button("🔓 Logout"):
    st.session_state.authenticated = False
    rerun()

page = st.sidebar.radio(
    "☰ Menu",
    ["PCS Settings", "Modules", "Circuit Config"],
    index=0,
    key="menu_radio"
)

# ─── PAGE: PCS Settings (CRUD) ───
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
                st.success(f"✅ Saved {name}")
                rerun()

    # List and manage existing PCS
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
                    st.success(f"🗑️ Deleted {nm}")
                    rerun()

    # Edit an existing PCS
    if "edit_pcs" in st.session_state:
        nm = st.session_state.pop("edit_pcs")
        p  = pcs_list[nm]
        st.subheader(f"✏️ Edit PCS: {nm}")
        new_name = st.text_input("PCS Name", value=nm, key="edit_pcs_name")
        max_v    = st.number_input("Max Voltage (V)", value=p["max_voltage"], key="edit_pcs_max")
        min_v    = st.number_input("MPPT Min Voltage (V)", value=p["mppt_min_voltage"], key="edit_pcs_min")
        count    = st.number_input("MPPT Inputs", value=p["mppt_count"], key="edit_pcs_count", min_value=1, step=1)
        max_i    = st.number_input("MPPT Max Current (A)", value=p["mppt_max_current"], key="edit_pcs_cur")
        if st.button("Save Changes", key="btn_save_pcs_edit"):
            save_pcs(new_name, max_v, min_v, int(count), max_i)
            st.success(f"✅ Updated {new_name}")
            rerun()

# ─── PAGE: Modules (CRUD) ───
elif page == "Modules":
    st.header("📥 Add / Manage Solar Panel Modules")
    mods = load_modules()

    # Add new module
    with st.expander("➕ Add New Module", expanded=False):
        m1, m2 = st.columns(2, gap="small")
        manufacturer = m1.text_input("メーカー名", key="new_mod_mfr")
        model_no     = m2.text_input("型番",       key="new_mod_no")
        c1, c2 = st.columns(2, gap="small")
        pmax = c1.number_input("STC Pmax (W)", key="new_mod_pmax")
        voc  = c2.number_input("STC Voc (V)",  key="new_mod_voc")
        c3, c4 = st.columns(2, gap="small")
        vmpp = c3.number_input("NOC Vmpp (V)", key="new_mod_vmpp")
        isc  = c4.number_input("NOC Isc (A)",  key="new_mod_isc")
        tc   = st.number_input("温度係数 (%/℃)", key="new_mod_tc", value=-0.3)
        if st.button("Save Module", key="btn_save_mod"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("❗ メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.success(f"✅ Saved {model_no}")
                rerun()

    # List and manage modules
    if mods:
        st.subheader("■ モジュールリスト")
        hdr = st.columns([1,2,2,1,1,1,1,1,2], gap="small")
        for col, title in zip(hdr, ["No","メーカー","型番","Pmax","Voc","Vmpp","Isc","Tc","Actions"]):
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
                    st.success(f"🗑️ Deleted {mn}")
                    rerun()

    # Edit a module
    if "edit_mod" in st.session_state:
        mn = st.session_state.pop("edit_mod")
        d  = mods[mn]
        st.subheader(f"✏️ Edit Module: {mn}")
        mf = st.text_input("メーカー名", value=d["manufacturer"], key="edit_mod_mfr")
        pm = st.number_input("STC Pmax (W)", value=d["pmax_stc"], key="edit_mod_pmax")
        vc = st.number_input("STC Voc (V)",  value=d["voc_stc"],    key="edit_mod_voc")
        vm = st.number_input("NOC Vmpp (V)", value=d["vmpp_noc"],   key="edit_mod_vmpp")
        ic = st.number_input("NOC Isc (A)",  value=d["isc_noc"],    key="edit_mod_isc")
        tc = st.number_input("温度係数 (%/℃)", value=d["temp_coeff"], key="edit_mod_tc")
        if st.button("Save Changes", key="btn_save_mod_edit"):
            save_module(mf, mn, pm, vc, vm, ic, tc)
            st.success(f"✅ Updated {mn}")
            rerun()

# ─── PAGE: Circuit Config ───
else:
    st.header("🔢 Series‐Only Circuit Configuration")
    mods = load_modules()
    if not mods:
        st.warning("⚠️ 先に「Modules」タブでモジュールを追加してください。")
    else:
        choice = st.selectbox("モジュールを選択", list(mods.keys()), key="cfg_mod")
        m = mods[choice]

        t1, t2 = st.columns(2, gap="small")
        t_min = t1.number_input("設置最低温度 (℃)", key="cfg_tmin", value=-5, step=1)
        t_max = t2.number_input("設置最高温度 (℃)", key="cfg_tmax", value=45, step=1)

        v_max    = st.session_state["pcs_max"]
        v_mp_min = st.session_state["pcs_mppt_min"]
        mppt_n   = st.session_state["pcs_mppt_count"]
        i_mppt   = st.session_state["pcs_mppt_current"]

        voc_a   = m["voc_stc"]*(1+m["temp_coeff"]/100*(t_min-25))
        vmpp_a  = m["vmpp_noc"]*(1+m["temp_coeff"]/100*(t_max-25))
        max_s   = math.floor(v_max/voc_a)    if voc_a>0  else 0
        min_s   = math.ceil(v_mp_min/vmpp_a) if vmpp_a>0 else 0

        st.info(f"直列可能枚数：最小 **{min_s}** ～ 最大 **{max_s}** 枚", icon="ℹ️")

        any_err    = False
        total_mods = 0

        for i in range(mppt_n):
            st.divider()
            st.subheader(f"MPPT 入力回路 {i+1}")
            ref_s = None
            vals = []

            for j in range(3):
                label = f"回路{j+1}の直列枚数 (0=未使用)"
                c1, c2 = st.columns([3,1], gap="small")
                c1.write(label)
                s = c2.number_input(
                    "", key=f"ser_{i}_{j}",
                    min_value=0, max_value=max_s,
                    value=(min_s if j==0 else 0), step=1
                )
                vals.append(s)
                if s>0:
                    # range check
                    if s<min_s or s>max_s:
                        c2.error(
                          f"入力{s}枚は範囲外です。\n"
                          f"{min_s}〜{max_s}枚の間で設定して下さい。",
                          icon="🚫"
                        ); any_err=True
                    # consistency check
                    if ref_s is None:
                        ref_s = s
                    elif s!=ref_s:
                        c2.error("回路内で同じ枚数を設定して下さい。", icon="🚫"); any_err=True
                    total_mods += s

            # current‐sum check
            branches = sum(1 for v in vals if v>0)
            if branches>0:
                cur = branches * m["isc_noc"]
                if cur>i_mppt:
                    c1, c2 = st.columns([3,1], gap="small")
                    c2.error(
                      f"合計電流 {cur:.1f}A が PCS 許容 {i_mppt}A を超えています。\n"
                      "直列枚数または回路数を減らして下さい。",
                      icon="🚫"
                    ); any_err=True

        if any_err:
            st.error("⚠️ 構成にエラーがあります。上記を修正して下さい。")
        elif total_mods==0:
            st.error("直列枚数を少なくとも１つ入力してください。")
        else:
            total_pw = total_mods * m["pmax_stc"]
            st.success("✅ 全 MPPT 構成は有効です。")
            c1, c2 = st.columns(2, gap="large")
            c1.metric("合計モジュール数", f"{total_mods} 枚")
            c2.metric("合計PV出力",    f"{total_pw/1000:.2f} kW")
