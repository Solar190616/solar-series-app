import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import init_db, save_module, load_modules, delete_module

# ─── Hide Streamlit toolbar & tighten layout ───
st.markdown("""
<style>
  header > div:nth-child(2) { display: none !important; }
  .css-1d391kg { padding: 1rem; }
  .css-1lcbmhc { gap: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── Safe rerun helper ───
rerun = getattr(st, "experimental_rerun", lambda: None)

# ─── Set page config ───
st.set_page_config(page_title="回路構成可否判定シート", layout="wide")

# ─── Seed default PCS settings once ───
default_pcs = {
    "pcs_max": 450,
    "pcs_mppt_min": 35,
    "pcs_mppt_count": 3,
    "pcs_mppt_current": 14.0
}
for k, v in default_pcs.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── AUTH ───
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

# ─── Sidebar + Logout ───
st.sidebar.button("🔓 Logout", on_click=lambda: (st.session_state.update({"authenticated": False}), rerun()))
page = st.sidebar.radio("☰ Menu", ["PCS Settings", "Modules", "Circuit Config"], key="menu")

# ─── PCS Settings ───
if page == "PCS Settings":
    st.header("⚙️ PCS / Inverter Settings")
    st.number_input("PCS Max Voltage (V)",
                    key="pcs_max",
                    value=st.session_state["pcs_max"],
                    step=1)
    st.number_input("PCS MPPT Min Voltage (V)",
                    key="pcs_mppt_min",
                    value=st.session_state["pcs_mppt_min"],
                    step=1)
    st.number_input("Number of MPPT Inputs",
                    key="pcs_mppt_count",
                    value=st.session_state["pcs_mppt_count"],
                    min_value=1,
                    step=1)
    st.number_input("PCS MPPT Max Current (A)",
                    key="pcs_mppt_current",
                    value=st.session_state["pcs_mppt_current"],
                    format="%.1f",
                    step=0.1)

# ─── Modules ───
elif page == "Modules":
    st.header("📥 Add / Manage Solar Module")
    init_db()
    mods = load_modules()

    with st.expander("➕ Add New Module"):
        m1, m2 = st.columns(2)
        manufacturer = m1.text_input("メーカー名", key="new_mfr")
        model_no     = m2.text_input("型番",       key="new_no")
        c1, c2 = st.columns(2)
        pmax = c1.number_input("STC Pmax (W)", key="new_pmax")
        voc  = c2.number_input("STC Voc (V)",  key="new_voc")
        c3, c4 = st.columns(2)
        vmpp = c3.number_input("NOC Vmpp (V)", key="new_vmpp")
        isc  = c4.number_input("NOC Isc (A)",  key="new_isc")
        tc   = st.number_input("温度係数 (%/℃)", key="new_tc", value=-0.3)
        if st.button("Save Module", key="save_new"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.success(f"Saved {model_no}")
                rerun()

    if mods:
        st.subheader("■ モジュールリスト")
        hdr = st.columns([1,2,2,1,1,1,1,1,2])
        for col, h in zip(hdr, ["No","メーカー名","型番","Pmax","Voc","Vmpp","Isc","Tc",""]):
            col.markdown(f"**{h}**")
        for idx, (mn, m) in enumerate(mods.items(), start=1):
            cols = st.columns([1,2,2,1,1,1,1,1,2])
            cols[0].write(idx)
            cols[1].write(m["manufacturer"])
            cols[2].write(mn)
            cols[3].write(m["pmax_stc"])
            cols[4].write(m["voc_stc"])
            cols[5].write(m["vmpp_noc"])
            cols[6].write(m["isc_noc"])
            cols[7].write(m["temp_coeff"])
            with cols[8]:
                if st.button("✏️", key=f"edit_{mn}"):
                    st.session_state.edit = mn
                    rerun()
                if st.button("🗑️", key=f"del_{mn}"):
                    delete_module(mn)
                    st.success(f"Deleted {mn}")
                    rerun()

    if "edit" in st.session_state:
        mn = st.session_state.pop("edit")
        data = load_modules()[mn]
        st.subheader(f"✏️ Edit {mn}")
        mf = st.text_input("メーカー名", value=data["manufacturer"], key="edit_mfr")
        pm = st.number_input("STC Pmax (W)", value=data["pmax_stc"], key="edit_pmax")
        vc = st.number_input("STC Voc (V)",  value=data["voc_stc"],    key="edit_voc")
        vm = st.number_input("NOC Vmpp (V)", value=data["vmpp_noc"],   key="edit_vmpp")
        ic = st.number_input("NOC Isc (A)",  value=data["isc_noc"],    key="edit_isc")
        tc = st.number_input("温度係数 (%/℃)", value=data["temp_coeff"], key="edit_tc")
        if st.button("Save Changes", key="save_edit"):
            save_module(mf, mn, pm, vc, vm, ic, tc)
            st.success(f"Updated {mn}")
            rerun()

# ─── Circuit Config ───
else:
    st.header("🔢 Series-Only Circuit Config")
    mods = load_modules()
    if not mods:
        st.warning("Add a module first.")
    else:
        choice = st.selectbox("モジュールを選択", list(mods.keys()), key="cfg_mod")
        m = mods[choice]

        t1, t2 = st.columns(2, gap="small")
        t_min = t1.number_input("最低温度 (℃)", key="cfg_tmin", value=-5, step=1)
        t_max = t2.number_input("最高温度 (℃)", key="cfg_tmax", value=45, step=1)

        # fetch with defaults
        v_max    = st.session_state.get("pcs_max", default_pcs["pcs_max"])
        v_mp_min = st.session_state.get("pcs_mppt_min", default_pcs["pcs_mppt_min"])
        mppt_n   = st.session_state.get("pcs_mppt_count", default_pcs["pcs_mppt_count"])
        i_mppt   = st.session_state.get("pcs_mppt_current", default_pcs["pcs_mppt_current"])

        voc_a = m["voc_stc"]*(1+m["temp_coeff"]/100*(t_min-25))
        vmpp_a= m["vmpp_noc"]*(1+m["temp_coeff"]/100*(t_max-25))
        max_s = math.floor(v_max / voc_a) if voc_a>0 else 0
        min_s = math.ceil(v_mp_min / vmpp_a) if vmpp_a>0 else 0

        st.info(f"直列可能: {min_s} 〜 {max_s} 枚", icon="ℹ️")

        any_err = False
        total_mod = 0

        for i in range(mppt_n):
            st.divider()
            ref_s = None
            vals = []
            for j in range(3):
                c1, c2 = st.columns([3,1], gap="small")
                if j==0:
                    c1.markdown(f"**MPPT回路{i+1}**")
                else:
                    c1.write("")
                s = c2.number_input(
                    "", key=f"ser_{i}_{j}",
                    min_value=0, max_value=max_s,
                    value=(min_s if j==0 else 0), step=1
                )
                vals.append(s)
                if s>0:
                    if s<min_s or s>max_s:
                        c2.error(f"{s}外", icon="⚠️")
                        any_err = True
                    if ref_s is None:
                        ref_s = s
                    elif s!=ref_s:
                        c2.error("同数に", icon="⚠️")
                        any_err = True
                    total_mod += s

            # input current check
            branches = sum(1 for v in vals if v>0)
            if branches>0:
                cur = branches * m["isc_noc"]
                if cur>i_mppt:
                    c1,c2 = st.columns([3,1], gap="small")
                    c2.error(f"{cur}A>限度{i_mppt}A", icon="⚠️")
                    any_err = True

        if any_err:
            st.error("⚠️ エラーがあります。")
        elif total_mod==0:
            st.error("直列枚数を入力してください。")
        else:
            power = total_mod * m["pmax_stc"]
            st.success("✅ Config valid")
            c1,c2 = st.columns(2, gap="large")
            c1.metric("合計モジュール", f"{total_mod}")
            c2.metric("合計PV出力", f"{power/1000:.2f} kW")
