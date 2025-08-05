import streamlit as st
import math
import pandas as pd

from auth import check_login, create_user, update_password
from db   import (
    init_db,
    save_module, load_modules, delete_module,
    save_pcs,    load_pcs,    delete_pcs
)

# Tell the browser about our manifest
st.markdown(
    '<link rel="manifest" href="/manifest.json">',
    unsafe_allow_html=True
)

# Register our service worker
st.markdown(
    """
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker
            .register('/sw.js')
            .then(reg => console.log('SW registered:', reg.scope))
            .catch(err => console.error('SW registration failed:', err));
        });
      }
    </script>
    """,
    unsafe_allow_html=True
)

# ─── GLOBAL CSS & PAGE CONFIG ───
st.markdown("""
<style>
  header > div:nth-child(2) { display: none !important; }
  .css-1d391kg { padding: 1rem !important; }
  .css-1lcbmhc { gap: 0.5rem !important; }
  
  /* Enhanced styling for menu tabs */
  .stButton > button {
    width: 100%;
    border-radius: 12px;
    font-weight: 800;
    font-size: 16px;
    padding: 16px 20px;
    margin: 6px 0;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border: 1px solid;
    position: relative;
    overflow: hidden;
  }
  
  /* Primary button styling (selected tab) */
  .stButton > button[data-baseweb="button"][aria-pressed="true"],
  .stButton > button[data-baseweb="button"].primary {
    background: linear-gradient(135deg, #1f77b4 0%, #0d5aa7 100%) !important;
    color: white !important;
    border-color: #0d5aa7 !important;
    box-shadow: 0 6px 15px rgba(31, 119, 180, 0.4) !important;
    transform: translateY(-2px);
  }
  
  /* Secondary button styling (unselected tab) */
  .stButton > button[data-baseweb="button"] {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    color: #495057 !important;
    border-color: #dee2e6 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
  }
  
  /* Hover effects */
  .stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
  }
  
  /* Primary button hover */
  .stButton > button[data-baseweb="button"][aria-pressed="true"]:hover,
  .stButton > button[data-baseweb="button"].primary:hover {
    background: linear-gradient(135deg, #0d5aa7 0%, #0a4a8a 100%) !important;
    box-shadow: 0 8px 20px rgba(31, 119, 180, 0.5) !important;
  }
  
  /* Secondary button hover */
  .stButton > button[data-baseweb="button"]:hover:not([aria-pressed="true"]):not(.primary) {
    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
    color: #212529 !important;
    border-color: #adb5bd !important;
  }
  
  /* Force button state updates */
  .stButton > button[data-baseweb="button"][aria-pressed="true"] {
    background: linear-gradient(135deg, #1f77b4 0%, #0d5aa7 100%) !important;
    color: white !important;
    border-color: #0d5aa7 !important;
    box-shadow: 0 6px 15px rgba(31, 119, 180, 0.4) !important;
    transform: translateY(-2px);
  }
  
  /* Ensure proper button styling for all states */
  .stButton > button[data-baseweb="button"]:not([aria-pressed="true"]):not(.primary) {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    color: #495057 !important;
    border-color: #dee2e6 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
  }
  
  /* Logout button styling */
  .stButton > button[key="logout_btn"] {
    background: linear-gradient(135deg, #ff4b4b 0%, #e63939 100%) !important;
    color: white !important;
    border: 1px solid #e63939 !important;
    box-shadow: 0 6px 15px rgba(255, 75, 75, 0.4) !important;
    font-weight: 800;
    font-size: 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .stButton > button[key="logout_btn"]:hover {
    background: linear-gradient(135deg, #e63939 0%, #d63333 100%) !important;
    border-color: #d63333 !important;
    box-shadow: 0 8px 20px rgba(255, 75, 75, 0.5) !important;
    transform: translateY(-2px);
  }
  
  /* Add subtle animation for button press */
  .stButton > button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
</style>
""", unsafe_allow_html=True)

rerun = getattr(st, "experimental_rerun", lambda: None)
st.set_page_config(page_title="回路構成可否判定シート", layout="wide")

st.markdown(
    """
    <style>
      /* hide ONLY the GitHub repo/fork icon in the header */
      header a[href*="github.com"] {
        display: none !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── INIT DATABASE ───
init_db()

# ─── AUTHENTICATION ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")

    # — Login form —
    user = st.text_input("ユーザー名", key="login_usr")
    pwd  = st.text_input("パスワード", type="password", key="login_pwd")
    if st.button("ログイン", key="btn_login"):
        if check_login(user, pwd):
            st.session_state.authenticated = True
            rerun()
        else:
            st.error("❌ ユーザー名またはパスワードが無効です")

    st.stop()

# ─── HEADER WITH LOGOUT & MENU ───
# Tabbed interface with collapsible content
st.markdown("""
<style>
/* Hide Streamlit default elements */
header > div:nth-child(2) { display: none !important; }
.css-1d391kg { padding: 1rem !important; }
.css-1lcbmhc { gap: 0.5rem !important; }

/* AGGRESSIVE ORANGE HIGHLIGHTING - FORCE STYLING */
div[data-testid="stExpander"] > div[data-testid="stExpanderHeader"] {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    color: #495057 !important;
    border: 2px solid #dee2e6 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    font-weight: normal !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
    padding: 15px 20px !important;
    transition: all 0.3s ease !important;
}

/* FORCE ORANGE BACKGROUND FOR SELECTED TABS */
div[data-testid="stExpander"] > div[data-testid="stExpanderHeader"][aria-expanded="true"],
.streamlit-expanderHeader[aria-expanded="true"],
[data-testid="stExpanderHeader"][aria-expanded="true"],
div[data-testid="stExpander"] [data-testid="stExpanderHeader"][aria-expanded="true"] {
    background: linear-gradient(135deg, #ff8c00 0%, #ff6b35 100%) !important;
    color: white !important;
    border: 3px solid #ff6b35 !important;
    box-shadow: 0 6px 15px rgba(255, 140, 0, 0.4) !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
    padding: 15px 20px !important;
    transform: translateY(-2px) !important;
}

/* FORCE BOLD ORANGE BORDERS FOR ENTIRE CONTENT AREA - NOT INDIVIDUAL ELEMENTS */
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] {
    border: 4px solid #ff8c00 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin-top: 10px !important;
    background: white !important;
    box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3) !important;
}

/* Remove borders from individual elements inside the content area */
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] * {
    border: none !important;
    box-shadow: none !important;
}

/* Ensure tables and other elements don't have borders */
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] table,
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] .stDataFrame,
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] .stSelectbox,
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] .stButton {
    border: none !important;
    box-shadow: none !important;
}

/* Hover effects */
div[data-testid="stExpander"] > div[data-testid="stExpanderHeader"][aria-expanded="true"]:hover,
.streamlit-expanderHeader[aria-expanded="true"]:hover {
    background: linear-gradient(135deg, #ff6b35 0%, #ff5722 100%) !important;
    box-shadow: 0 8px 20px rgba(255, 140, 0, 0.5) !important;
    transform: translateY(-3px) !important;
}

div[data-testid="stExpander"] > div[data-testid="stExpanderHeader"][aria-expanded="false"]:hover {
    background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
    color: #212529 !important;
    border-color: #adb5bd !important;
    box-shadow: 0 6px 15px rgba(0,0,0,0.15) !important;
    transform: translateY(-2px) !important;
}

/* Force orange header styling with maximum specificity */
[data-testid="stExpander"] [data-testid="stExpanderHeader"][aria-expanded="true"] {
    background: linear-gradient(135deg, #ff8c00 0%, #ff6b35 100%) !important;
    color: white !important;
    border: 3px solid #ff6b35 !important;
    box-shadow: 0 6px 15px rgba(255, 140, 0, 0.4) !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
    padding: 15px 20px !important;
    transform: translateY(-2px) !important;
}

/* Target the entire expander container for content borders */
div[data-testid="stExpander"] {
    border: 4px solid #ff8c00 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin-top: 10px !important;
    background: white !important;
    box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3) !important;
}

/* Remove borders from collapsed expanders */
div[data-testid="stExpander"]:not([data-testid*="expanded"]) {
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
</style>

<script>
// JavaScript to force styling after page load
document.addEventListener('DOMContentLoaded', function() {
    function applyStyling() {
        // Force orange background for expanded headers
        const expandedHeaders = document.querySelectorAll('[data-testid="stExpanderHeader"][aria-expanded="true"]');
        expandedHeaders.forEach(header => {
            header.style.background = 'linear-gradient(135deg, #ff8c00 0%, #ff6b35 100%)';
            header.style.color = 'white';
            header.style.border = '3px solid #ff6b35';
            header.style.boxShadow = '0 6px 15px rgba(255, 140, 0, 0.4)';
            header.style.fontWeight = 'bold';
            header.style.borderRadius = '12px';
            header.style.marginBottom = '10px';
            header.style.padding = '15px 20px';
            header.style.transform = 'translateY(-2px)';
        });
        
        // Force orange borders for the entire expander container (not individual elements)
        const expanders = document.querySelectorAll('[data-testid="stExpander"]');
        expanders.forEach(expander => {
            const isExpanded = expander.querySelector('[data-testid="stExpanderHeader"][aria-expanded="true"]');
            if (isExpanded) {
                expander.style.border = '4px solid #ff8c00';
                expander.style.borderRadius = '12px';
                expander.style.padding = '20px';
                expander.style.marginTop = '10px';
                expander.style.background = 'white';
                expander.style.boxShadow = '0 4px 15px rgba(255, 140, 0, 0.3)';
                
                // Remove borders from all child elements
                const childElements = expander.querySelectorAll('*');
                childElements.forEach(child => {
                    if (child !== expander) {
                        child.style.border = 'none';
                        child.style.boxShadow = 'none';
                    }
                });
            } else {
                expander.style.border = 'none';
                expander.style.boxShadow = 'none';
                expander.style.padding = '0';
                expander.style.margin = '0';
            }
        });
    }
    
    // Apply styling immediately
    applyStyling();
    
    // Apply styling after a short delay to catch dynamic content
    setTimeout(applyStyling, 100);
    setTimeout(applyStyling, 500);
    setTimeout(applyStyling, 1000);
    
    // Watch for changes and reapply styling
    const observer = new MutationObserver(applyStyling);
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# ─── PCS SETTINGS TAB ───
with st.expander("【➀PCS入力】※タブを展開/最小化するにはここをタップ", expanded=st.session_state.get("menu_page", "PCS Settings") == "PCS Settings"):
    # PCS Settings content
    st.header("⚙️ インバータの追加・管理")

    # — Add New PCS —
    with st.expander("➕ 新しいPCSを追加"):
        name  = st.text_input("PCS名称", key="new_pcs_name")
        c1,c2 = st.columns(2, gap="small")
        max_v = c1.number_input("最大電圧 (V)", key="new_pcs_max")
        min_v = c2.number_input("MPPT最小電圧 (V)", key="new_pcs_min")
        c3,c4 = st.columns(2, gap="small")
        count = c3.number_input("MPPT入力数", key="new_pcs_count", min_value=1, step=1)
        max_i = c4.number_input("MPPT最大電流 (A)", key="new_pcs_cur", format="%.1f")
        if st.button("PCS保存", key="btn_save_pcs"):
            if not name.strip():
                st.error("名称は必須です")
            else:
                save_pcs(name, max_v, min_v, int(count), max_i)
                st.success(f"✅ 保存しました → {name}")

    # — Responsive PCS Table —
    pcs_list = load_pcs()
    if pcs_list:
        st.subheader("■ 保存済みPCS/インバータ")
        df_pcs = (
            pd.DataFrame.from_dict(pcs_list, orient="index")
              .reset_index()
              .rename(columns={
                  "index":"名称",
                  "max_voltage":"最大電圧 (V)",
                  "mppt_min_voltage":"最小電圧 (V)",
                  "mppt_count":"MPPT数",
                  "mppt_max_current":"最大電流 (A)"
              })
        )
        st.dataframe(df_pcs, use_container_width=True)

        choice = st.selectbox(
            "編集・削除するPCSを選択",
            df_pcs["名称"],
            key="pcs_choice"
        )
        
        # Show confirmation buttons if delete is requested
        if st.session_state.get("show_delete_confirm_pcs", False) and st.session_state.get("delete_target_pcs") == choice:
            st.warning(f"🗑️ '{choice}' を削除してもよろしいですか？この操作は取り消せません。")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                col_yes, col_cancel = st.columns(2)
                with col_yes:
                    if st.button("✅ はい、削除", key="confirm_delete_pcs"):
                        delete_pcs(choice)
                        st.session_state.pop("show_delete_confirm_pcs", None)
                        st.session_state.pop("delete_target_pcs", None)
                        st.success(f"✅ 削除しました → {choice}")
                        rerun()
                with col_cancel:
                    if st.button("❌ キャンセル", key="cancel_delete_pcs"):
                        st.session_state.pop("show_delete_confirm_pcs", None)
                        st.session_state.pop("delete_target_pcs", None)
                        rerun()
        else:
            e1,e2 = st.columns(2, gap="small")
            if e1.button("✏️ 編集", key="pcs_edit_btn"):
                if st.session_state.get("edit_pcs") == choice:
                    st.error("既にこのPCSを編集中です。保存またはキャンセルしてください。")
                else:
                    st.session_state["edit_pcs"] = choice
                    rerun()
            if e2.button("🗑️ 削除", key="pcs_del_btn"):
                if st.session_state.get("edit_pcs") == choice:
                    st.error("編集中は削除できません。保存またはキャンセルしてください。")
                else:
                    st.session_state.show_delete_confirm_pcs = True
                    st.session_state.delete_target_pcs = choice

    # — Edit PCS Form —
    if "edit_pcs" in st.session_state:
        nm = st.session_state["edit_pcs"]
        p  = pcs_list[nm]
        st.subheader(f"✏️ PCS編集: {nm}")
        new_name = st.text_input("PCS名称", value=nm, key="edit_pcs_name")
        max_v    = st.number_input("最大電圧 (V)",       value=p["max_voltage"], key="edit_pcs_max")
        min_v    = st.number_input("MPPT最小電圧 (V)",  value=p["mppt_min_voltage"], key="edit_pcs_min")
        count    = st.number_input("MPPT入力数",           value=p["mppt_count"], key="edit_pcs_count", min_value=1, step=1)
        max_i    = st.number_input("MPPT最大電流 (A)",  value=p["mppt_max_current"], key="edit_pcs_cur")
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("変更保存", key="btn_save_pcs_edit"):
                if not new_name.strip():
                    st.error("名称は必須です")
                else:
                    # Delete old entry if name changed
                    if new_name != nm:
                        delete_pcs(nm)
                    # Save new entry
                    save_pcs(new_name, max_v, min_v, int(count), max_i)
                    st.success(f"✅ 更新しました → {new_name}")
                    st.session_state.pop("edit_pcs", None)
                    rerun()
        with col2:
            if st.button("キャンセル", key="btn_cancel_pcs_edit"):
                st.session_state.pop("edit_pcs", None)
                rerun()

# ─── MODULES TAB ───
with st.expander("【➁モジュール入力】※タブを展開/最小化するにはここをタップ", expanded=st.session_state.get("menu_page") == "Modules"):
    # Modules content
    st.header("📱 モジュールの追加・管理")

    # — Add New Module —
    with st.expander("➕ 新しいモジュールを追加"):
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
        if st.button("モジュール保存", key="btn_save_mod"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.success(f"✅ 保存しました → {model_no}")

    # — Responsive Module Table —
    mods = load_modules()
    if mods:
        st.subheader("■ モジュールリスト")
        df_mod = pd.DataFrame([
            {
              "型番": mn,
              "メーカー名": m["manufacturer"],
              "Pmax (W)":   m["pmax_stc"],
              "Voc (V)":    m["voc_stc"],
              "Vmpp (V)":   m["vmpp_noc"],
              "Isc (A)":    m["isc_noc"],
              "温度係数":  m["temp_coeff"],
            }
            for mn,m in mods.items()
        ])
        st.dataframe(df_mod, use_container_width=True)

        choice = st.selectbox("編集・削除するモジュールを選択",
                              df_mod["型番"], key="mod_choice")
        
        # Show confirmation buttons if delete is requested
        if st.session_state.get("show_delete_confirm_mod", False) and st.session_state.get("delete_target_mod") == choice:
            st.warning(f"🗑️ '{choice}' を削除してもよろしいですか？この操作は取り消せません。")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                col_yes, col_cancel = st.columns(2)
                with col_yes:
                    if st.button("✅ はい、削除", key="confirm_delete_mod"):
                        delete_module(choice)
                        st.session_state.pop("show_delete_confirm_mod", None)
                        st.session_state.pop("delete_target_mod", None)
                        st.success(f"✅ 削除しました → {choice}")
                        rerun()
                with col_cancel:
                    if st.button("❌ キャンセル", key="cancel_delete_mod"):
                        st.session_state.pop("show_delete_confirm_mod", None)
                        st.session_state.pop("delete_target_mod", None)
                        rerun()
        else:
            m1,m2 = st.columns(2, gap="small")
            if m1.button("✏️ 編集", key="mod_edit_btn"):
                if st.session_state.get("edit_mod") == choice:
                    st.error("既にこのモジュールを編集中です。保存またはキャンセルしてください。")
                else:
                    st.session_state["edit_mod"] = choice
                    rerun()
            if m2.button("🗑️ 削除", key="mod_del_btn"):
                if st.session_state.get("edit_mod") == choice:
                    st.error("編集中は削除できません。保存またはキャンセルしてください。")
                else:
                    st.session_state.show_delete_confirm_mod = True
                    st.session_state.delete_target_mod = choice

    # — Edit Module Form —
    if "edit_mod" in st.session_state:
        mn = st.session_state["edit_mod"]
        d  = mods[mn]
        st.subheader(f"✏️ モジュール編集: {mn}")
        mf = st.text_input("メーカー名", value=d["manufacturer"], key="edit_mod_mfr")
        new_model_no = st.text_input("型番", value=mn, key="edit_mod_no")
        pm = st.number_input("STC Pmax (W)",      value=d["pmax_stc"], key="edit_mod_pmax")
        vc = st.number_input("STC Voc (V)",       value=d["voc_stc"],  key="edit_mod_voc")
        vm = st.number_input("NOC Vmpp (V)",      value=d["vmpp_noc"], key="edit_mod_vmpp")
        ic = st.number_input("NOC Isc (A)",       value=d["isc_noc"],  key="edit_mod_isc")
        tc = st.number_input("温度係数 (%/℃)",     value=d["temp_coeff"],key="edit_mod_tc")
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("変更保存", key="btn_save_mod_edit"):
                if not mf.strip() or not new_model_no.strip():
                    st.error("メーカー名と型番は必須です。")
                else:
                    # Delete old entry if model number changed
                    if new_model_no != mn:
                        delete_module(mn)
                    # Save new entry
                    save_module(mf, new_model_no, pm, vc, vm, ic, tc)
                    st.success(f"✅ 更新しました → {new_model_no}")
                    st.session_state.pop("edit_mod", None)
                    rerun()
        with col2:
            if st.button("キャンセル", key="btn_cancel_mod_edit"):
                st.session_state.pop("edit_mod", None)
                rerun()

# ─── CIRCUIT CONFIG TAB ───
with st.expander("【➂回路構成】※タブを展開/最小化するにはここをタップ", expanded=st.session_state.get("menu_page") == "Circuit Config"):
    # Circuit Config content
    st.header("🔢 回路構成判定")

    # 1) select a saved PCS spec
    pcs_list = load_pcs()
    if not pcs_list:
        st.warning("⚠️ 先に「PCS入力」タブで PCS/インバータを追加してください。")
        st.stop()
    spec = st.selectbox("PCSを選択", list(pcs_list.keys()), key="cfg_pcs")
    pcs  = pcs_list[spec]

    # 2) select a module
    mods = load_modules()
    if not mods:
        st.warning("⚠️ 先に「モジュール入力」タブでモジュールを追加してください。")
        st.stop()
    mod_name = st.selectbox("モジュールを選択", list(mods.keys()), key="cfg_mod")
    m = mods[mod_name]

    # 3) temps
    t_min = st.selectbox("設置場所の最低温度（℃）", 
                        options=[0, -5, -10, -15, -20, -25, -30], 
                        key="cfg_tmin", 
                        index=1)  # Default to -5°C (index 1)
    t_max = 50  # Fixed maximum temperature

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
        st.subheader(f"MPPT入力 {i+1}")
        ref_s = None
        vals  = []

        for j in range(3):
            c1, c2 = st.columns([3,1], gap="small")
            label = f"回路{j+1} の直列枚数 (0=未使用)"
            c1.write(label)
            key = f"ser_{i}_{j}"
            default = min_s if j==0 else 0
            s = c2.number_input("直列枚数", key=key,
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
        
        # Enhanced success section with better styling
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 2px solid #28a745;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.2);
            text-align: center;
        ">
            <h2 style="color: #155724; margin: 0 0 20px 0; font-size: 24px;">
                ✅ 全 MPPT 構成は有効です
            </h2>
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 0 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    min-width: 200px;
                ">
                    <div style="font-size: 14px; color: #6c757d; margin-bottom: 8px;">合計モジュール数</div>
                    <div style="font-size: 32px; font-weight: bold; color: #1f77b4;">{total_mods} 枚</div>
                </div>
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 0 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    min-width: 200px;
                ">
                    <div style="font-size: 14px; color: #6c757d; margin-bottom: 8px;">合計PV出力</div>
                    <div style="font-size: 32px; font-weight: bold; color: #28a745;">{power_kw:.2f} kW</div>
                </div>
            </div>
        </div>
        """.format(total_mods=total_mods, power_kw=power/1000), unsafe_allow_html=True)

# ─── LOGOUT TAB ───
# Simple logout confirmation (not expandable)
logout_selected = st.button("🔓 ログアウト", key="logout_btn")
if logout_selected:
    st.session_state.show_logout_confirm = True

# Show logout confirmation if requested
if st.session_state.get("show_logout_confirm", False):
    st.markdown("---")
    
    # Create a centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Dialog box styling
        st.markdown("""
        <div style="
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        ">
        """, unsafe_allow_html=True)
        
        # Header with icon and title
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ff4b4b 0%, #e63939 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: -20px -20px 20px -20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        ">
            <span style="font-size: 20px;">🚪</span>
            <span style="font-size: 16px; font-weight: bold;">ログアウト</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Question text
        st.markdown("**ログアウトしますか？**")
        st.markdown("")
        
        # Buttons
        col_yes, col_cancel = st.columns(2)
        with col_yes:
            if st.button("✅ はい", key="confirm_logout", 
                        help="Confirm logout", 
                        use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.pop("show_logout_confirm", None)
                rerun()
        with col_cancel:
            if st.button("✘ いいえ", key="cancel_logout", 
                        help="Cancel logout", 
                        use_container_width=True):
                st.session_state.pop("show_logout_confirm", None)
                rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")

# Set default page if not set
if "menu_page" not in st.session_state:
    st.session_state.menu_page = "PCS Settings"
