import streamlit as st
import math
import pandas as pd
import qrcode
from io import BytesIO

from auth import check_login, create_user, update_password
from db   import (
    init_db,
    save_module, load_modules, delete_module,
    save_pcs,    load_pcs,    delete_pcs
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
  
  /* Hide GitHub elements */
  [data-testid="stDecoration"] { display: none !important; }
  .stDeployButton { display: none !important; }
  .stApp > header { display: none !important; }
  .stApp > footer { display: none !important; }
  .stApp > div[data-testid="stToolbar"] { display: none !important; }
  .stApp > div[data-testid="stStatusWidget"] { display: none !important; }
  
  /* Hide GitHub and Fork elements more comprehensively */
  div:contains("Fork"), 
  a[href*="github.com"],
  [data-testid="stDeployButton"],
  .stDeployButton,
  .stApp > div:has-text("Fork"),
  .stApp > div:has-text("GitHub"),
  /* Additional selectors for GitHub elements */
  .stApp > div[data-testid="stDecoration"],
  .stApp > div[data-testid="stDeployButton"],
  .stApp > div[data-testid="stStatusWidget"],
  .stApp > div[data-testid="stToolbar"],
  /* Hide elements with GitHub-related text */
  div:contains("Fork"),
  div:contains("GitHub"),
  span:contains("Fork"),
  span:contains("GitHub"),
  a:contains("Fork"),
  a:contains("GitHub"),
  /* Hide elements with GitHub icons */
  svg[data-testid="GitHub"],
  img[src*="github"],
  svg[aria-label*="GitHub"],
  /* Hide Streamlit's default header elements */
  .stApp > header,
  .stApp > footer,
  /* Hide any element with GitHub-related classes */
  .github,
  .fork,
  [class*="github"],
  [class*="fork"],
  /* Hide elements by attribute */
  [data-testid*="github"],
  [data-testid*="fork"],
  [aria-label*="GitHub"],
  [aria-label*="Fork"] { 
    display: none !important; 
    visibility: hidden !important;
    opacity: 0 !important;
  }
  
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
    
    # Create two columns for login button and QR code
    col_login, col_qr = st.columns([1, 1])
    
    with col_login:
        if st.button("ログイン", key="btn_login"):
            if check_login(user, pwd):
                st.session_state.authenticated = True
                rerun()
            else:
                st.error("❌ ユーザー名またはパスワードが無効です")
    
    with col_qr:
        qr_expanded = st.button("📱 QRコード", key="qr_btn", help="アプリをQRコードで共有")
        if qr_expanded:
            st.session_state.show_qr_code = True
    
    # Show QR code when button is clicked
    if st.session_state.get("show_qr_code", False):
        # QR Code generation function
        def generate_qr_code(url):
            """Generate QR code for the given URL"""
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            return img
        
        # Get current app URL
        current_url = st.query_params.get('_stcore', None)
        if current_url is None:
            # Try to get the URL from Streamlit's session state or use a default
            current_url = "https://solar-series-app-c5pizf5htsctsruqq9li2k.streamlit.app/"  # Default local URL
        
        st.markdown("**アプリのQRコード**")
        st.markdown("このQRコードをスキャンしてアプリにアクセスできます。")
        
        # Generate QR code
        qr_img = generate_qr_code(current_url)
        
        # Convert PIL image to bytes
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Display QR code
        st.image(img_buffer, width=200, caption="アプリのQRコード")
        
        # Display URL
        st.markdown(f"**URL:** {current_url}")
        
        # Download button for QR code
        st.download_button(
            label="📥 QRコードをダウンロード",
            data=img_buffer.getvalue(),
            file_name="solar_app_qr.png",
            mime="image/png"
        )
        
        # Close button
        if st.button("✖️ 閉じる", key="close_qr"):
            st.session_state.pop("show_qr_code", None)
            rerun()

    st.stop()

# ─── HEADER WITH LOGOUT & MENU ───
# Tabbed interface with collapsible content
st.markdown("""
<style>
/* Hide Streamlit default elements */
header > div:nth-child(2) { display: none !important; }
.css-1d391kg { padding: 1rem !important; }
.css-1lcbmhc { gap: 0.5rem !important; }

/* DARK MODE TEXT VISIBILITY FIXES */
/* Ensure all text is visible in dark mode */
.stMarkdown, .stText, .stHeader, .stSubheader, .stTitle {
    color: inherit !important;
}

/* Force text visibility for all content */
div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] {
    color: #262730 !important; /* Dark text for light background */
}

/* Ensure headers are visible */
h1, h2, h3, h4, h5, h6 {
    color: #262730 !important;
}

/* Ensure form elements have proper contrast */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    color: #262730 !important;
    background-color: white !important;
}

/* Ensure buttons have proper text color */
.stButton > button {
    color: #262730 !important;
}

/* Ensure dataframes have proper text color */
.stDataFrame {
    color: #262730 !important;
}

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
    color: #262730 !important; /* Ensure dark text on white background */
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
    color: #262730 !important; /* Ensure dark text on white background */
}

/* Remove borders from collapsed expanders */
div[data-testid="stExpander"]:not([data-testid*="expanded"]) {
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Ensure logout button text is visible */
.stButton > button[data-baseweb="button"] {
    color: #262730 !important;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    border: 2px solid #dee2e6 !important;
}

/* Ensure error and success messages are visible */
.stAlert {
    color: #262730 !important;
}

/* DARK MODE COMPREHENSIVE FIXES */
@media (prefers-color-scheme: dark) {
    /* Main container dark mode */
    .main .block-container {
        background-color: #0f1419 !important;
        color: #ffffff !important;
    }
    
    /* All text elements in dark mode */
    .stMarkdown, .stText, .stHeader, .stSubheader, .stTitle,
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #ffffff !important;
    }
    
    /* Content areas in dark mode */
    div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] {
        color: #ffffff !important;
        background-color: #1a1d21 !important;
    }
    
    /* Form elements in dark mode */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        color: #ffffff !important;
        background-color: #2d3748 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Number input buttons in dark mode */
    .stNumberInput button {
        background-color: #2d3748 !important;
        color: #ffffff !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Dataframes in dark mode */
    .stDataFrame {
        color: #ffffff !important;
        background-color: #1a1d21 !important;
    }
    
    /* Tables in dark mode */
    .stDataFrame table,
    .stDataFrame th,
    .stDataFrame td {
        color: #ffffff !important;
        background-color: #1a1d21 !important;
        border: 1px solid #4a5568 !important;
    }
    
    .stDataFrame th {
        background-color: #2d3748 !important;
    }
    
    /* Tab headers in dark mode (collapsed) */
    div[data-testid="stExpander"] > div[data-testid="stExpanderHeader"] {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%) !important;
        color: #ffffff !important;
        border: 2px solid #4a5568 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }
    
    /* Content area borders in dark mode */
    div[data-testid="stExpander"] > div[data-testid="stExpanderContent"] {
        background: #1a1d21 !important;
        color: #ffffff !important;
    }
    
    /* Target the entire expander container in dark mode */
    div[data-testid="stExpander"] {
        background: #1a1d21 !important;
        color: #ffffff !important;
    }
    
    /* Hover effects in dark mode */
    div[data-testid="stExpander"] > div[data-testid="stExpanderHeader"][aria-expanded="false"]:hover {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
        color: #ffffff !important;
        border-color: #718096 !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.3) !important;
    }
    
    /* Logout button in dark mode */
    .stButton > button[data-baseweb="button"] {
        color: #ffffff !important;
        background: #2d3748 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* General buttons in dark mode */
    .stButton > button {
        color: #ffffff !important;
        background: #2d3748 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Alert messages in dark mode */
    .stAlert {
        color: #ffffff !important;
        background-color: #1a1d21 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Success messages in dark mode */
    .stAlert:contains("✅"),
    .stSuccess {
        background-color: #1a202c !important;
        color: #68d391 !important;
        border: 1px solid #68d391 !important;
    }
    
    /* Error messages in dark mode */
    .stAlert:contains("❌"),
    .stError {
        background-color: #1a202c !important;
        color: #fc8181 !important;
        border: 1px solid #fc8181 !important;
    }
    
    /* Warning messages in dark mode */
    .stAlert:contains("⚠️"),
    .stWarning {
        background-color: #1a202c !important;
        color: #f6ad55 !important;
        border: 1px solid #f6ad55 !important;
    }
    
    /* Info messages in dark mode */
    .stAlert:contains("ℹ️"),
    .stInfo {
        background-color: #1a202c !important;
        color: #68d391 !important;
        border: 1px solid #68d391 !important;
    }
}
</script>
""", unsafe_allow_html=True)

# ─── 操作方法 ───
st.markdown("\U0001F449 タブ\u2780\u2192\u2781\u2192\u2782を順番に確認し、回路構成可否を判定してください。")

# ─── Cautions TAB ───
with st.expander("**⚠️ 注意** ※タブを展開/最小化するにはここをタップ", expanded=False):
    st.markdown("""
        注1：本判定結果は回路構成の可否を判断するもので、設置可否を判断するものではありません。  
        注2：回路可能判定結果はモジュール・インバータリストに登録された電気特性を基に判定しています。  
        注3：モジュールの経年劣化による影響は考慮していません。  
    """)

# ─── PCS SETTINGS TAB ───
with st.expander("**【➀インバータ入力】**", expanded=st.session_state.get("menu_page", "PCS Settings") == "PCS Settings"):
    # PCS Settings content
    st.markdown(
        "<h4 style='margin-bottom: 10px;'>⚙️ インバータの追加・管理</h4>",
        unsafe_allow_html=True
    )
    # Inverter addition instruction text in red
    st.markdown(
        '<p style="color:red; margin-bottom: 0.4rem;">'
        '※必要なインバータがリストにない場合は、追加してください。'
        '</p>',
        unsafe_allow_html=True
    )

    # — Add New PCS —
    with st.expander("➕ 新しいPCSを追加"):
        c1,c2 = st.columns(2, gap="small")
        name  = c1.text_input("PCS名称", key="new_pcs_name")
        model_number = c2.text_input("型番", key="new_pcs_model")
        c3,c4 = st.columns(2, gap="small")
        max_v = c3.number_input("最大電圧 (V)", key="new_pcs_max")
        min_v = c4.number_input("MPPT最小電圧 (V)", key="new_pcs_min")
        c5,c6 = st.columns(2, gap="small")
        count = c5.number_input("MPPT入力数", key="new_pcs_count", min_value=1, step=1)
        max_i = c6.number_input("MPPT最大電流 (A)", key="new_pcs_cur", format="%.1f")
        if st.button("PCS保存", key="btn_save_pcs"):
            if not name.strip():
                st.error("名称は必須です")
            else:
                save_pcs(name, model_number, max_v, min_v, int(count), max_i)
                st.success(f"✅ 保存しました → {name}")

    # — Responsive PCS Table —
    pcs_list = load_pcs()
    if pcs_list:
        st.markdown(
            "<h4 style='margin-bottom: 10px;'>❖ インバータリスト</h4>",
            unsafe_allow_html=True
        )
        df_pcs = (
            pd.DataFrame.from_dict(pcs_list, orient="index")
              .reset_index()
              .rename(columns={
                  "index":"名称",
                  "model_number":"型番",
                  "max_voltage":"最大電圧 (V)",
                  "mppt_min_voltage":"最小電圧 (V)",
                  "mppt_count":"MPPT数",
                  "mppt_max_current":"最大電流 (A)"
              })
        )
        st.dataframe(df_pcs, use_container_width=True)

        choice = st.selectbox(
            "🔽編集・削除するインバータを選択",
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
            # Check if selected PCS is default
            is_default_pcs = pcs_list[choice].get("is_default", False)
            
            e1, e2 = st.columns(2, gap="small")
            
            # Edit button - disabled for default PCS
            if is_default_pcs:
                e1.button("✏️ 編集", key="pcs_edit_btn", disabled=True, help="デフォルトPCSは編集できません")
            else:
                if e1.button("✏️ 編集", key="pcs_edit_btn"):
                    if st.session_state.get("edit_pcs") == choice:
                        st.error("既にこのPCSを編集中です。保存またはキャンセルしてください。")
                    else:
                        st.session_state["edit_pcs"] = choice
                        rerun()
            
            # Delete button - disabled for default PCS
            if is_default_pcs:
                e2.button("🗑️ 削除", key="pcs_del_btn", disabled=True, help="デフォルトPCSは削除できません")
            else:
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
        model_number = st.text_input("型番", value=p.get("model_number", ""), key="edit_pcs_model")
        max_v    = st.number_input("最大電圧 (V)",       value=p["max_voltage"], key="edit_pcs_max")
        min_v    = st.number_input("MPPT最小電圧 (V)",  value=p["mppt_min_voltage"], key="edit_pcs_min")
        count    = st.number_input("MPPT入力数",           value=p["mppt_count"], key="edit_pcs_count", min_value=1, step=1)
        max_i    = st.number_input("MPPT最大電流 (A)",  value=p["mppt_max_current"], key="edit_pcs_cur")
        
        # Preserve default status when editing
        is_currently_default = p.get("is_default", False)
        
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("変更保存", key="btn_save_pcs_edit"):
                if not new_name.strip():
                    st.error("名称は必須です")
                else:
                    # Delete old entry if name changed
                    if new_name != nm:
                        delete_pcs(nm)
                    # Save new entry with preserved default status
                    save_pcs(new_name, model_number, max_v, min_v, int(count), max_i, is_currently_default)
                    st.success(f"✅ 更新しました → {new_name}")
                    st.session_state.pop("edit_pcs", None)
                    rerun()
        with col2:
            if st.button("キャンセル", key="btn_cancel_pcs_edit"):
                st.session_state.pop("edit_pcs", None)
                rerun()

# ─── MODULES TAB ───
with st.expander("**【➁モジュール入力】**", expanded=st.session_state.get("menu_page") == "Modules"):
    # Modules content
    st.markdown(
        "<h4 style='margin-bottom: 10px;'>📱 モジュールの追加・管理</h4>",
        unsafe_allow_html=True
    )

     # Module addition instruction text in red
    st.markdown(
        '<p style="color:red; margin-bottom: 0.4rem;">'
        '※検討したいモジュールがリストにない場合は、追加してください。'
        '</p>',
        unsafe_allow_html=True
    )

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
        tc   = st.number_input("開放電圧の温度係数 (%/℃)", key="new_mod_tc", value=-0.3)
        if st.button("モジュール保存", key="btn_save_mod"):
            if not manufacturer.strip() or not model_no.strip():
                st.error("メーカー名と型番は必須です。")
            else:
                save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc)
                st.success(f"✅ 保存しました → {model_no}")

    # — Responsive Module Table —
    mods = load_modules()
    if mods:
        st.markdown(
            "<h4 style='margin-bottom: 10px;'>❖ モジュールリスト</h4>",
            unsafe_allow_html=True
        )
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

        choice = st.selectbox("🔽編集・削除するモジュールを選択",
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
        tc = st.number_input("開放電圧の温度係数 (%/℃)",     value=d["temp_coeff"],key="edit_mod_tc")
        
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
with st.expander("**【➂回路構成判定】**", expanded=st.session_state.get("menu_page") == "Circuit Config"):
    
    # SECTION 1: 直列可能枚数
    st.markdown(
        "<h4 style='margin-bottom: 10px;'>📊 1. 直列可能枚数</h4>",
        unsafe_allow_html=True
        )
    st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
    
    # Compact selection section
    col1, col2, col3 = st.columns(3, gap="small")
    
    # PCS selection
    with col1:
        pcs_list = load_pcs()
        if not pcs_list:
            st.warning("⚠️ 先に「PCS入力」タブで PCS/インバータを追加してください。")
            st.stop()
        options = [pcs["model_number"] for pcs in pcs_list.values()]
        model = st.selectbox("PCSを選択", options, key="cfg_pcs")
        pcs = next(p for p in pcs_list.values() if p["model_number"] == model)

    # Module selection
    with col2:
        mods = load_modules()
        if not mods:
            st.warning("⚠️ 先に「モジュール入力」タブでモジュールを追加してください。")
            st.stop()
        mod_name = st.selectbox("モジュールを選択", list(mods.keys()), key="cfg_mod")
        m = mods[mod_name]

    # Temperature selection
    with col3:
        t_min = st.selectbox("設置場所の最低温度（℃）", 
                            options=[0, -5, -10, -15, -20, -25, -30], 
                            key="cfg_tmin", 
                            index=1)  # Default to -5°C (index 1)
        t_max = 50  # Fixed maximum temperature

    # Calculate series bounds
    v_max    = pcs["max_voltage"]
    v_mp_min = pcs["mppt_min_voltage"]
    mppt_n   = pcs["mppt_count"]
    i_mppt   = pcs["mppt_max_current"]

    voc_a   = m["voc_stc"]*(1 + m["temp_coeff"]/100*(t_min-25))
    vmpp_a  = m["vmpp_noc"]*(1 + m["temp_coeff"]/100*(t_max-25))
    max_s   = math.floor(v_max    / voc_a)  if voc_a>0   else 0
    min_s   = math.ceil (v_mp_min / vmpp_a) if vmpp_a>0 else 0

    st.info(f"直列可能枚数：最小 **{min_s}** 枚 ～ 最大 **{max_s}** 枚", icon="ℹ️")
    
    st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
    
    # SECTION 2: モジュールの回路構成
    st.markdown(
        "<h4 style='margin-bottom: 10px;'>🔧 2. モジュールの回路構成</h4>",
        unsafe_allow_html=True
        )
        
   # MPPT instruction text in red
    st.markdown(
        '<p style="color:red; margin-bottom: 0.3rem;">'
        '※直列可能枚数の範囲内でシステム構成してください。'
        '</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color:red; margin-bottom: 0.1rem;">'
        '※モジュールがない場合は"0"にしてください。'
        '</p>',
        unsafe_allow_html=True
    )
    st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

    # MPPT configuration loop
    any_err    = False
    total_mods = 0

    for i in range(mppt_n):
        st.markdown(f"**🔷MPPT入力 {i+1}**")
        ref_s = None
        vals  = []

        # Compact 3-column layout for circuits
        cols = st.columns(3, gap="small")
        for j in range(3):
            with cols[j]:
                st.markdown(f"**回路{j+1}**")
                key = f"ser_{i}_{j}"
                default = min_s if j==0 else 0
                s = st.number_input("直列枚数", key=key,
                                     min_value=0, max_value=max_s,
                                     value=default, step=1, label_visibility="collapsed")
                vals.append(s)

                if s>0:
                    # range check
                    if s<min_s or s>max_s:
                        st.error(f"{s} 枚は範囲外です。{min_s}～{max_s} 枚で入力してください。", icon="🚫")
                        any_err = True
                    # consistency check
                    if ref_s is None:
                        ref_s = s
                    elif s!=ref_s:
                        st.error("この MPPT内の全回路で同じ枚数を設定してください。", icon="🚫")
                        any_err = True
                    total_mods += s

        # current‐sum check
        used = sum(1 for v in vals if v>0)
        if used>0:
            cur = used * m["isc_noc"]
            if cur>i_mppt:
                st.error(f"合計入力電流 {cur:.1f}A が PCS 許容 {i_mppt}A を超えています。\n"
                         "直列枚数または使用回路数を減らしてください。", icon="🚫")
                any_err = True
        
        if i < mppt_n - 1:  # Add separator between MPPT sections
            st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
    
    # SECTION 3: 回路構成可否判定結果
    st.markdown("### ✅ 3. 判定結果")
    st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
    
    # Final summary / error
    if any_err:
        st.error("⚠️ 構成にエラーがあります。上記メッセージをご確認ください。")
    elif total_mods == 0:
        st.error("少なくとも1つの回路で直列枚数を入力してください。")
    else:
        power = total_mods * m["pmax_stc"]
        
        # Success section
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 2px solid #28a745;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
            text-align: center;
        ">
            <h3 style="color: #155724; margin: 0 0 15px 0; font-size: 18px;">
                ✅ 回路構成可能です。
            </h3>
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div style="
                    background: white;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 0 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    min-width: 120px;
                ">
                    <div style="font-size: 12px; color: #6c757d; margin-bottom: 4px;">合計モジュール数</div>
                    <div style="font-size: 24px; font-weight: bold; color: #1f77b4;">{total_mods} 枚</div>
                </div>
                <div style="
                    background: white;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 0 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    min-width: 120px;
                ">
                    <div style="font-size: 12px; color: #6c757d; margin-bottom: 4px;">合計PV出力</div>
                    <div style="font-size: 24px; font-weight: bold; color: #28a745;">{power_kw:.2f} kW</div>
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
       
    # Create a centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Dialog box styling
        st.markdown("""
        <div style="
            border-radius: 12px;
            padding: 5px;
            text-align: center;
            margin: 1x 0;
        ">
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
    
    st.markdown("<hr style='margin: 0.3rem 0; border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

# Set default page if not set
if "menu_page" not in st.session_state:
    st.session_state.menu_page = "PCS Settings"

# JavaScript for enhanced styling
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Hide GitHub and Fork elements
    function hideGitHubElements() {
        // Hide elements containing "Fork" or "GitHub" text
        const allElements = document.querySelectorAll('*');
        allElements.forEach(element => {
            if (element.textContent && (
                element.textContent.includes('Fork') || 
                element.textContent.includes('GitHub') ||
                element.textContent.includes('fork') ||
                element.textContent.includes('github')
            )) {
                element.style.display = 'none';
                element.style.visibility = 'hidden';
                element.style.opacity = '0';
            }
        });
        
        // Hide elements with GitHub-related attributes
        const githubElements = document.querySelectorAll('[data-testid*="github"], [data-testid*="fork"], [aria-label*="GitHub"], [aria-label*="Fork"], [href*="github.com"]');
        githubElements.forEach(element => {
            element.style.display = 'none';
            element.style.visibility = 'hidden';
            element.style.opacity = '0';
        });
        
        // Hide Streamlit decoration elements
        const decorationElements = document.querySelectorAll('[data-testid="stDecoration"], .stDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"]');
        decorationElements.forEach(element => {
            element.style.display = 'none';
            element.style.visibility = 'hidden';
            element.style.opacity = '0';
        });
    }
    
    // Run immediately and also set up a mutation observer to catch dynamically added elements
    hideGitHubElements();
    
    // Set up observer to catch dynamically added elements
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                hideGitHubElements();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    function updateRowNumbers() {
        const tables = document.querySelectorAll('div[data-testid="stDataFrame"] table, div[data-testid="stTable"] table');
        tables.forEach(table => {
            const headerCell = table.querySelector('thead th:first-child');
            if (headerCell) {
                headerCell.textContent = 'No.';
                headerCell.style.pointerEvents = 'none';
                headerCell.style.cursor = 'default';
                const sortIcons = headerCell.querySelectorAll('svg');
                sortIcons.forEach(icon => icon.style.display = 'none');
            }

            const rows = table.querySelectorAll('tbody tr');
            rows.forEach((row, idx) => {
                const firstCell = row.querySelector('th, td');
                if (firstCell) {
                    firstCell.textContent = idx + 1;
                    firstCell.textContent = idx;
                }
            });
        });
    }

    function applyStyling() {
        const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
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
        
        const expanders = document.querySelectorAll('[data-testid="stExpander"]');
        expanders.forEach(expander => {
            const isExpanded = expander.querySelector('[data-testid="stExpanderHeader"][aria-expanded="true"]');
            if (isExpanded) {
                expander.style.border = '4px solid #ff8c00';
                expander.style.borderRadius = '12px';
                expander.style.padding = '20px';
                expander.style.marginTop = '10px';
                
                if (isDarkMode) {
                    expander.style.background = '#1a1d21';
                    expander.style.color = '#ffffff';
                } else {
                    expander.style.background = 'white';
                    expander.style.color = '#262730';
                }
                
                expander.style.boxShadow = '0 4px 15px rgba(255, 140, 0, 0.3)';
                
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
        
        if (isDarkMode) {
            // Enhanced dark mode color palette
            const darkTheme = {
                // Background colors
                primaryBg: '#0a0e17',      // Deep dark blue-black
                secondaryBg: '#1a1f2e',    // Slightly lighter dark blue
                cardBg: '#252b3d',         // Card/component background
                surfaceBg: '#2d3748',      // Form elements background
                
                // Text colors
                primaryText: '#e2e8f0',    // Soft white for primary text
                secondaryText: '#a0aec0',  // Muted gray for secondary text
                accentText: '#63b3ed',     // Blue accent for links/highlights
                mutedText: '#718096',      // Very muted text
                
                // Accent colors
                primaryAccent: '#4299e1',  // Blue accent
                successAccent: '#48bb78',  // Green accent
                warningAccent: '#ed8936',  // Orange accent
                errorAccent: '#f56565',    // Red accent
                
                // Borders and dividers
                borderColor: '#4a5568',    // Subtle borders
                dividerColor: '#2d3748',   // Section dividers
                
                // Special elements
                headerBg: '#1a1f2e',       // Header background
                sidebarBg: '#0a0e17',      // Sidebar background
                buttonBg: '#2d3748',       // Button background
                buttonHover: '#4a5568'     // Button hover state
            };
            
            // Function to determine text color based on background with enhanced logic
            function getTextColorForBackground(bgColor) {
                if (!bgColor) return darkTheme.primaryText;
                
                // Convert hex to RGB for better color analysis
                let hex = bgColor.replace('#', '');
                if (hex.length === 3) {
                    hex = hex.split('').map(char => char + char).join('');
                }
                
                const r = parseInt(hex.substr(0, 2), 16);
                const g = parseInt(hex.substr(2, 2), 16);
                const b = parseInt(hex.substr(4, 2), 16);
                
                // Calculate brightness
                const brightness = (r * 299 + g * 587 + b * 114) / 1000;
                
                // Check for specific background colors
                const bgColorLower = bgColor.toLowerCase();
                
                // Light backgrounds -> dark text
                if (bgColorLower.includes('white') || 
                    bgColorLower.includes('light') || 
                    bgColorLower.includes('fff') ||
                    bgColorLower.includes('f8f9fa') ||
                    bgColorLower.includes('e9ecef') ||
                    bgColorLower.includes('dee2e6') ||
                    bgColorLower.includes('68d391') || // light green
                    bgColorLower.includes('fc8181') || // light red
                    bgColorLower.includes('f6ad55') || // light orange
                    brightness > 180) {
                    return '#1a202c'; // Dark text on light backgrounds
                }
                
                // Dark backgrounds -> light text
                if (bgColorLower.includes('black') || 
                    bgColorLower.includes('dark') || 
                    bgColorLower.includes('000') ||
                    bgColorLower.includes('1a1d21') ||
                    bgColorLower.includes('0f1419') ||
                    bgColorLower.includes('2d3748') ||
                    bgColorLower.includes('1a202c') ||
                    bgColorLower.includes('ff8c00') || // orange
                    bgColorLower.includes('ff6b35') || // dark orange
                    brightness < 100) {
                    return darkTheme.primaryText; // Light text on dark backgrounds
                }
                
                // Default to primary text color
                return darkTheme.primaryText;
            }
            
            // Apply enhanced dark theme to main container
            const mainContainer = document.querySelector('.main .block-container');
            if (mainContainer) {
                mainContainer.style.backgroundColor = darkTheme.primaryBg;
                mainContainer.style.color = darkTheme.primaryText;
                mainContainer.style.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
            }
            
            // Apply enhanced styling to headers and titles
            const headers = document.querySelectorAll('h1, h2, h3, h4, h5, h6, .stHeader, .stSubheader, .stTitle');
            headers.forEach(header => {
                if (!header.closest('[data-testid="stTabs"]') && 
                    !header.closest('[data-testid="stTab"]') &&
                    !header.closest('[role="tabpanel"]') &&
                    !header.closest('.stTabs')) {
                    header.style.color = darkTheme.primaryText;
                    header.style.fontWeight = '600';
                    header.style.letterSpacing = '-0.025em';
                }
            });
            
            // Apply enhanced styling to paragraphs and text
            const paragraphs = document.querySelectorAll('p, .stText, .stMarkdown');
            paragraphs.forEach(p => {
                if (!p.closest('[data-testid="stTabs"]') && 
                    !p.closest('[data-testid="stTab"]') &&
                    !p.closest('[role="tabpanel"]') &&
                    !p.closest('.stTabs')) {
                    p.style.color = darkTheme.secondaryText;
                    p.style.lineHeight = '1.6';
                }
            });
            
            // Apply smart text coloring to all text elements, but exclude tab content
            const allTextElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, .stMarkdown, .stText, .stHeader, .stSubheader, .stTitle');
            allTextElements.forEach(element => {
                // Skip elements inside tabs to maintain consistent colors
                if (element.closest('[data-testid="stTabs"]') || 
                    element.closest('[data-testid="stTab"]') ||
                    element.closest('[role="tabpanel"]') ||
                    element.closest('.stTabs')) {
                    return; // Skip this element - don't change its color
                }
                
                if (!element.closest('[data-testid="stExpanderHeader"][aria-expanded="true"]')) {
                    const bgColor = window.getComputedStyle(element).backgroundColor;
                    const hexColor = rgbToHex(bgColor);
                    element.style.color = getTextColorForBackground(hexColor);
                }
            });
            
            // Enhanced form elements styling
            const formElements = document.querySelectorAll('input, select, textarea, .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div');
            formElements.forEach(element => {
                element.style.backgroundColor = darkTheme.surfaceBg;
                element.style.color = darkTheme.primaryText;
                element.style.border = `1px solid ${darkTheme.borderColor}`;
                element.style.borderRadius = '8px';
                element.style.padding = '8px 12px';
                element.style.fontSize = '14px';
                element.style.transition = 'all 0.2s ease';
            });
            
            // Enhanced number input buttons
            const numberButtons = document.querySelectorAll('.stNumberInput button');
            numberButtons.forEach(button => {
                button.style.backgroundColor = darkTheme.buttonBg;
                button.style.color = darkTheme.primaryText;
                button.style.border = `1px solid ${darkTheme.borderColor}`;
                button.style.borderRadius = '6px';
                button.style.transition = 'all 0.2s ease';
            });
            
            // Enhanced table styling
            const tableElements = document.querySelectorAll('table, .stDataFrame, .stDataFrame th, .stDataFrame td');
            tableElements.forEach(element => {
                element.style.backgroundColor = darkTheme.cardBg;
                element.style.color = darkTheme.primaryText;
                element.style.border = `1px solid ${darkTheme.borderColor}`;
                element.style.borderRadius = '8px';
            });
            
            // Enhanced button styling
            const buttons = document.querySelectorAll('button:not([data-testid="logout_btn"]):not(.stNumberInput button)');
            buttons.forEach(button => {
                if (!button.closest('[data-testid="stTabs"]') && 
                    !button.closest('[data-testid="stTab"]') &&
                    !button.closest('[role="tabpanel"]') &&
                    !button.closest('.stTabs')) {
                    button.style.backgroundColor = darkTheme.buttonBg;
                    button.style.color = darkTheme.primaryText;
                    button.style.border = `1px solid ${darkTheme.borderColor}`;
                    button.style.borderRadius = '8px';
                    button.style.padding = '8px 16px';
                    button.style.fontWeight = '500';
                    button.style.transition = 'all 0.2s ease';
                }
            });
            
            // Enhanced logout button styling
            const logoutButton = document.querySelector('button[data-testid="logout_btn"]');
            if (logoutButton) {
                logoutButton.style.background = darkTheme.errorAccent;
                logoutButton.style.color = '#ffffff';
                logoutButton.style.border = `1px solid ${darkTheme.errorAccent}`;
                logoutButton.style.borderRadius = '8px';
                logoutButton.style.padding = '8px 16px';
                logoutButton.style.fontWeight = '500';
                logoutButton.style.transition = 'all 0.2s ease';
            }
            
            // Ensure tab content maintains consistent colors regardless of mode
            const tabContent = document.querySelectorAll('[data-testid="stTabs"] [role="tabpanel"], .stTabs [role="tabpanel"]');
            tabContent.forEach(tab => {
                // Reset any dark mode styling for tab content
                tab.style.color = '#262730'; // Default light mode text color
                tab.style.backgroundColor = 'transparent';
                
                // Ensure all child elements in tabs maintain their original colors
                const tabChildren = tab.querySelectorAll('*');
                tabChildren.forEach(child => {
                    // Reset color to default if it was changed by dark mode
                    if (child.style.color === '#ffffff' || child.style.color === 'rgb(255, 255, 255)') {
                        child.style.color = '#262730'; // Default text color
                    }
                    // Reset background to transparent if it was changed
                    if (child.style.backgroundColor === '#1a1d21' || child.style.backgroundColor === '#0f1419') {
                        child.style.backgroundColor = 'transparent';
                    }
                });
            });
            
            // Enhanced alert boxes with modern styling
            const alertBoxes = document.querySelectorAll('.stAlert, .stInfo, .stWarning, .stError, .stSuccess, div[data-testid="stAlert"]');
            alertBoxes.forEach(box => {
                const text = box.textContent || '';
                box.style.borderRadius = '12px';
                box.style.padding = '16px 20px';
                box.style.fontWeight = '500';
                box.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                box.style.border = 'none';
                box.style.margin = '8px 0';
                
                if (text.includes('✅') || text.includes('success')) {
                    box.style.backgroundColor = `${darkTheme.successAccent}20`; // Semi-transparent green
                    box.style.color = darkTheme.successAccent;
                    box.style.borderLeft = `4px solid ${darkTheme.successAccent}`;
                } else if (text.includes('❌') || text.includes('error')) {
                    box.style.backgroundColor = `${darkTheme.errorAccent}20`; // Semi-transparent red
                    box.style.color = darkTheme.errorAccent;
                    box.style.borderLeft = `4px solid ${darkTheme.errorAccent}`;
                } else if (text.includes('⚠️') || text.includes('warning')) {
                    box.style.backgroundColor = `${darkTheme.warningAccent}20`; // Semi-transparent orange
                    box.style.color = darkTheme.warningAccent;
                    box.style.borderLeft = `4px solid ${darkTheme.warningAccent}`;
                } else if (text.includes('ℹ️') || text.includes('info')) {
                    box.style.backgroundColor = `${darkTheme.primaryAccent}20`; // Semi-transparent blue
                    box.style.color = darkTheme.primaryAccent;
                    box.style.borderLeft = `4px solid ${darkTheme.primaryAccent}`;
                } else {
                    box.style.backgroundColor = darkTheme.cardBg;
                    box.style.color = darkTheme.secondaryText;
                    box.style.borderLeft = `4px solid ${darkTheme.borderColor}`;
                }
            });
            
            // Helper function to convert RGB to Hex
            function rgbToHex(rgb) {
                if (!rgb || rgb === 'rgba(0, 0, 0, 0)' || rgb === 'transparent') return '#1a1d21';
                // Simple parsing without complex regex
                const rgbMatch = rgb.replace(/[rgba()]/g, '').split(',');
                if (rgbMatch.length < 3) return '#1a1d21';
                const r = parseInt(rgbMatch[0]);
                const g = parseInt(rgbMatch[1]);
                const b = parseInt(rgbMatch[2]);
                if (isNaN(r) || isNaN(g) || isNaN(b)) return '#1a1d21';
                return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
            }
        } else {
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div');
            textElements.forEach(element => {
                if (element.closest('[data-testid="stExpanderContent"]')) {
                    element.style.color = '#262730';
                }
            });
        }
        updateRowNumbers();
    }
    
    applyStyling();
    setTimeout(applyStyling, 100);
    setTimeout(applyStyling, 500);
    setTimeout(applyStyling, 1000);
    
    const observer = new MutationObserver(applyStyling);
    observer.observe(document.body, { childList: true, subtree: true });
    
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyStyling);
    }
});
</script>
""", unsafe_allow_html=True)
