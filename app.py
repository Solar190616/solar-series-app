import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db import (
    init_db,
    save_module, load_modules, delete_module,
    save_pcs,    load_pcs,    delete_pcs
)

# ─── PAGE & STYLING SETUP ─────────────────────────────────────────────────────
st.set_page_config(page_title="回路構成可否判定シート", layout="wide")

st.markdown("""
<style>
  /* hide top‐right Streamlit icons */
  header > div:nth-child(2) { display: none !important; }
  header a[href*="github.com"] { display: none !important; }

  /* tighten app padding & gaps */
  .css-1d391kg { padding: 1rem !important; }
  .css-1lcbmhc { gap: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# Safe rerun helper
rerun = getattr(st, "experimental_rerun", lambda: None)

# ─── INITIALIZE DB ────────────────────────────────────────────────────────────
init_db()

# ─── AUTHENTICATION ───────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login")
    u = st.text_input("Username", key="login_user")
    p = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if check_login(u, p):
            st.session_state.authenticated = True
            rerun()
        else:
            st.error("❌ Invalid credentials")

    st.markdown("---")
    with st.expander("📝 Sign Up"):
        su = st.text_input("New Username", key="signup_user")
        sp = st.text_input("New Password", type="password", key="signup_pass")
        sc = st.text_input("Confirm Password", type="password", key="signup_conf")
        if st.button("Register"):
            if not su:
                st.error("Username required")
            elif sp != sc:
                st.error("Passwords do not match")
            elif create_user(su, sp):
                st.success("✅ Registration successful")
            else:
                st.error("Username already exists")

    with st.expander("🔄 Reset Password"):
        ru = st.text_input("Username", key="reset_user")
        op = st.text_input("Old Password", type="password", key="reset_old")
        np = st.text_input("New Password", type="password", key="reset_new")
        nc = st.text_input("Confirm New", type="password", key="reset_conf")
        if st.button("Reset"):
            if np != nc:
                st.error("Passwords must match")
            elif not check_login(ru, op):
                st.error("Invalid username or old password")
            else:
                update_password(ru, np)
                st.success("✅ Password updated")

    st.stop()

# ─── ENSURE MENU STATE ────────────────────────────────────────────────────────
if "menu" not in st.session_state:
    st.session_state.menu = "PCS Settings"

# ─── MODAL CONFIRMATION HELPERS ────────────────────────────────────────────────
def confirm_modal(key, title, text, on_confirm):
    """Generic modal. Show if st.session_state[key] True."""
    if st.session_state.get(key):
        with st.modal(title):
            st.write(text)
            c1, c2 = st.columns(2, gap="small")
            if c1.button("✅ Yes"):
                st.session_state[key] = False
                on_confirm()
            if c2.button("❌ Cancel"):
                st.session_state[key] = False
                rerun()

# ─── TOP BAR: LOGOUT + 3-STEP ARROW MENU ─────────────────────────────────────
col0, col1 = st.columns([1,6], gap="small")
with col0:
    if st.button("🔓 Logout", key="logout_btn"):
        st.session_state.logout_confirm = True
        rerun()
confirm_modal(
    key="logout_confirm",
    title="🔓 Logout Confirmation",
    text="Are you sure you want to logout?",
    on_confirm=lambda: (st.session_state.update(authenticated=False), rerun())
)

with col1:
    page = st.session_state.menu
    # build arrow‐stepper HTML
    html = '<div class="stepper-container">'
    for idx,(key,label) in enumerate([
        ("PCS Settings","PCS入力"),
        ("Modules","モジュール入力"),
        ("Circuit Config","回路構成")
    ], start=1):
        circ = ["","①","②","③"][idx]
        act  = "active" if page==key else ""
        html += f'''
          <div class="step {act}"
               onclick="window.location.search='?menu={key}'">
            {circ}{label}
          </div>'''
    html += "</div>"
    st.markdown(html + """
    <style>
      .stepper-container {
        display:flex; justify-content:center; align-items:center;
        margin:0.5rem 0 1rem;
      }
      .step {
        position: relative;
        background:#0284c7; color:#fff;
        padding:0.5rem 1rem; margin-right:4px;
        font-weight:600; cursor:pointer; user-select:none;
      }
      .step:last-child { margin-right:0; }
      .step:after {
        content:""; position:absolute; top:0; right:-12px;
        border-top:12px solid transparent;
        border-bottom:12px solid transparent;
        border-left:12px solid #0284c7;
      }
      .step.active {
        background:#0ea5e9;
      }
      .step.active:after {
        border-left-color:#0ea5e9;
      }
      .step:hover {
        background:#06b6d4;
      }
      .step:hover:after {
        border-left-color:#06b6d4;
      }
    </style>
    """, unsafe_allow_html=True)

    # capture ?menu param via new API
    qp = st.query_params
    if qp.get("menu", [None])[0] in ["PCS Settings","Modules","Circuit Config"]:
        st.session_state.menu = qp["menu"][0]
    page = st.session_state.menu

st.markdown("---")

# ─── PAGE 1: PCS SETTINGS ─────────────────────────────────────────────────────
if page == "PCS Settings":
    st.header("⚙️ Add / Manage PCS / Inverter Specs")

    # add new PCS
    with st.expander("➕ Add New PCS"):
        n1, n2 = st.columns(2, gap="small")
        name = n1.text_input("PCS Name", key="new_pcs_name")
        maxv = n2.number_input("Max Voltage (V)", key="new_pcs_max")
        n3, n4 = st.columns(2, gap="small")
        minv = n3.number_input("MPPT Min Voltage (V)", key="new_pcs_min")
        curv = n4.number_input("MPPT Max Current (A)", key="new_pcs_cur")
        count= st.number_input("# MPPT Inputs", key="new_pcs_cnt", min_value=1, step=1)
        if st.button("Save PCS"):
            if not name:
                st.error("Name is required")
            else:
                save_pcs(name,maxv,minv,int(count),curv)
                st.success(f"Saved → {name}")
                rerun()

    pcsd = load_pcs()
    if pcsd:
        st.subheader("■ Saved PCS / Inverters")
        df = pd.DataFrame.from_dict(pcsd, orient="index").reset_index()
        df.columns = ["Name","max_voltage","mppt_min_voltage","mppt_count","mppt_max_current"]
        st.dataframe(df, use_container_width=True)

        sel = st.selectbox("Select PCS", df["Name"], key="pcs_sel")
        c1,c2 = st.columns(2, gap="small")
        if c1.button("✏️ Edit PCS"):
            st.session_state.edit_confirm = True
            st.session_state.edit_target  = sel
            st.session_state.edit_type    = "pcs"
            rerun()
        if c2.button("🗑️ Delete PCS"):
            st.session_state.delete_confirm = True
            st.session_state.delete_target  = sel
            st.session_state.delete_type    = "pcs"
            rerun()

    # edit/delete modals
    confirm_modal(
        key="edit_confirm",
        title="✏️ Edit Confirmation",
        text=f"Do you want to edit '{st.session_state.get('edit_target','')}'?",
        on_confirm=lambda: (st.session_state.update(edit_pcs=st.session_state.pop("edit_target")), rerun())
    )
    confirm_modal(
        key="delete_confirm",
        title="🗑️ Delete Confirmation",
        text=f"Delete '{st.session_state.get('delete_target','')}' permanently?",
        on_confirm=lambda: (
            delete_pcs(st.session_state.pop("delete_target")),
            st.success("Deleted successfully"),
            rerun()
        )
    )

# ─── PAGE 2: MODULES ──────────────────────────────────────────────────────────
elif page == "Modules":
    st.header("📥 Add / Manage Solar Panel Modules")

    with st.expander("➕ Add New Module"):
        c1,c2 = st.columns(2, gap="small")
        mfr    = c1.text_input("メーカー名", key="new_mod_mfr")
        mno    = c2.text_input("型番",     key="new_mod_no")
        c3,c4 = st.columns(2, gap="small")
        pmax   = c3.number_input("STC Pmax (W)", key="new_mod_pmax")
        voc    = c4.number_input("STC Voc (V)",  key="new_mod_voc")
        c5,c6 = st.columns(2, gap="small")
        vmpp   = c5.number_input("NOC Vmpp (V)", key="new_mod_vmpp")
        isc    = c6.number_input("NOC Isc (A)",  key="new_mod_isc")
        tc     = st.number_input("温度係数 (%/℃)", key="new_mod_tc", value=-0.3)
        if st.button("Save Module"):
            if not mfr or not mno:
                st.error("Both fields required")
            else:
                save_module(mfr,mno,pmax,voc,vmpp,isc,tc)
                st.success(f"Saved → {mno}")
                rerun()

    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        dfm = pd.DataFrame([
            {
              "Model No.": mn,
              "メーカー名": d["manufacturer"],
              "Pmax (W)": d["pmax_stc"],
              "Voc (V)":  d["voc_stc"],
              "Vmpp (V)": d["vmpp_noc"],
              "Isc (A)":  d["isc_noc"],
              "TempCoeff":d["temp_coeff"]
            }
            for mn,d in mods.items()
        ])
        st.dataframe(dfm, use_container_width=True)

        sel = st.selectbox("Select Module", dfm["Model No."], key="mod_sel")
        e1,e2 = st.columns(2, gap="small")
        if e1.button("✏️ Edit Module"):
            st.session_state.edit_confirm = True
            st.session_state.edit_target  = sel
            st.session_state.edit_type    = "mod"
            rerun()
        if e2.button("🗑️ Delete Module"):
            st.session_state.delete_confirm = True
            st.session_state.delete_target  = sel
            st.session_state.delete_type    = "mod"
            rerun()

    confirm_modal(
        key="edit_confirm",
        title="✏️ Edit Confirmation",
        text=f"Do you want to edit '{st.session_state.get('edit_target','')}'?",
        on_confirm=lambda: (
            st.session_state.update(edit_mod=st.session_state.pop("edit_target")),
            rerun()
        )
    )
    confirm_modal(
        key="delete_confirm",
        title="🗑️ Delete Confirmation",
        text=f"Delete '{st.session_state.get('delete_target','')}' permanently?",
        on_confirm=lambda: (
            delete_module(st.session_state.pop("delete_target")),
            st.success("Deleted successfully"),
            rerun()
        )
    )

    # If edit_mod is set, show the edit form
    if "edit_mod" in st.session_state:
        mn = st.session_state.pop("edit_mod")
        d  = mods[mn]
        st.subheader(f"✏️ Edit Module: {mn}")
        mfr = st.text_input("メーカー名", value=d["manufacturer"], key="edt_mod_mfr")
        p   = st.number_input("STC Pmax (W)", value=d["pmax_stc"], key="edt_mod_pmax")
        v   = st.number_input("STC Voc (V)",  value=d["voc_stc"],  key="edt_mod_voc")
        vm  = st.number_input("NOC Vmpp (V)", value=d["vmpp_noc"], key="edt_mod_vmpp")
        i   = st.number_input("NOC Isc (A)",  value=d["isc_noc"],  key="edt_mod_isc")
        t   = st.number_input("温度係数 (%/℃)", value=d["temp_coeff"],key="edt_mod_tc")
        if st.button("Save Changes"):
            save_module(mfr,mn,p,v,vm,i,t)
            st.success("Module updated")
            rerun()

# ─── PAGE 3: SERIES-ONLY CIRCUIT CONFIG ───────────────────────────────────────
else:
    st.header("🔢 Series-Only Circuit Configuration")

    pcsd = load_pcs()
    if not pcsd:
        st.warning("まず PCS 設定を追加してください。")
        st.stop()
    sel_pcs = st.selectbox("Select PCS", list(pcsd.keys()), key="cfg_pcs")
    pcs     = pcsd[sel_pcs]

    modd = load_modules()
    if not modd:
        st.warning("まず モジュールを追加してください。")
        st.stop()
    sel_mod = st.selectbox("モジュールを選択", list(modd.keys()), key="cfg_mod")
    mod     = modd[sel_mod]

    c1,c2 = st.columns(2, gap="small")
    tmin   = c1.number_input("設置最低温度 (℃)", key="cfg_tmin", value=-5, step=1)
    tmax   = c2.number_input("設置最高温度 (℃)", key="cfg_tmax", value=45, step=1)

    # adjust Voc/Vmpp by temp
    voc_adj  = mod["voc_stc"]*(1+mod["temp_coeff"]/100*(tmin-25))
    vmpp_adj = mod["vmpp_noc"]*(1+mod["temp_coeff"]/100*(tmax-25))

    max_s = math.floor(pcs["max_voltage"]/voc_adj) if voc_adj>0 else 0
    min_s = math.ceil(pcs["mppt_min_voltage"]/vmpp_adj) if vmpp_adj>0 else 0

    st.info(f"直列可能枚数：**{min_s}**～**{max_s}** 枚")

    any_err = False
    total   = 0

    for i in range(pcs["mppt_count"]):
        st.divider()
        st.subheader(f"MPPT回路 {i+1}")
        ref   = None
        used  = 0
        cur_i = 0

        for j in range(3):
            colA, colB = st.columns([3,1], gap="small")
            colA.write(f"回路{j+1} 直列枚数")
            key = f"cell_{i}_{j}"
            val = colB.number_input("", key=key, min_value=0, max_value=max_s, value=(min_s if j==0 else 0), step=1)
            if val>0:
                used += 1
                cur_i += mod["isc_noc"]
                total += val
                if val<min_s or val>max_s:
                    colB.error("範囲外", icon="🚫")
                    any_err = True
                if ref is None:
                    ref = val
                elif val != ref:
                    colB.error("統一してください", icon="🚫")
                    any_err = True

        # check current
        if used>0 and cur_i>pcs["mppt_max_current"]:
            st.error(f"入力電流 {cur_i}A が上限 {pcs['mppt_max_current']}A を超えています。", icon="🚫")
            any_err = True

    if any_err:
        st.error("⚠️ 構成にエラーがあります。修正してください。")
    elif total==0:
        st.error("少なくとも1つの回路を使用してください。")
    else:
        st.success("✅ 全 MPPT 構成は有効です。")
        st.metric("合計モジュール数", f"{total} 枚")
        st.metric("合計PV出力", f"{total*mod['pmax_stc']/1000:.2f} kW")
