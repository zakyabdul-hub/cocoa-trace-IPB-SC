"""
style_adminhmd.py - Centralized Theme & Design System berbasis adminHMD
Sistem Ketertelusuran Kakao (CacaoTrace)
"""

import streamlit as st

def inject_adminhmd_theme():
    """
    Suntikkan Custom CSS System yang mengadopsi token warna, layout, 
    dan gaya komponen dari template adminHMD (adminhmd-1.0.0).
    """
    st.markdown("""
    <style>
        /* Import Google Fonts & Bootstrap Icons */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
        @import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css');
        
        /* Design Tokens adminHMD */
        :root {
            --admin-bg: #f5f7fb;
            --admin-surface: #ffffff;
            --admin-surface-soft: #f8fafc;
            --admin-border: #dbe4ef;
            --admin-text: #1f2937;
            --admin-muted: #6b7280;
            --admin-primary: #2563eb;
            --admin-primary-dark: #1d4ed8;
            --admin-cocoa: #6C3D14;
            --admin-cocoa-light: #8B5E34;
            --admin-success: #0f766e;
            --admin-warning: #d97706;
            --admin-danger: #dc2626;
            --admin-sidebar: #111827;
            --admin-sidebar-soft: #1f2937;
            --admin-sidebar-hover: #374151;
            --admin-shadow-sm: 0 4px 14px rgba(15, 23, 42, 0.04);
            --admin-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            --admin-shadow-lg: 0 18px 46px rgba(15, 23, 42, 0.09);
            --admin-ring: 0 0 0 4px rgba(37, 99, 235, 0.12);
        }
        
        /* Global Canvas Style */
        .stApp {
            background-color: var(--admin-bg) !important;
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
            color: var(--admin-text) !important;
        }
        
        /* Override Main Block Containers */
        .stAppViewMainContainer > .main {
            background-color: var(--admin-bg) !important;
        }
        
        /* Hide Default Headers & Footers */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100 !important;
        }
        
        /* ============================================================
           SIDEBAR STYLING - adminHMD (.admin-sidebar)
           ============================================================ */
        [data-testid="stSidebar"] {
            background-color: var(--admin-sidebar) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 18px 0 42px rgba(15, 23, 42, 0.18) !important;
        }
        
        [data-testid="stSidebar"] * {
            color: #e5e7eb !important;
        }
        
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 700 !important;
        }
        
        /* Navigation Links in Sidebar */
        [data-testid="stSidebarNav"] {
            padding-top: 1rem !important;
        }
        
        [data-testid="stSidebarNav"] a {
            border-radius: 8px !important;
            padding: 0.65rem 1rem !important;
            margin: 0.2rem 0.5rem !important;
            transition: all 0.2s ease !important;
        }
        
        [data-testid="stSidebarNav"] a:hover {
            background-color: var(--admin-sidebar-soft) !important;
            color: #ffffff !important;
        }
        
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: var(--admin-primary) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }

        /* Sidebar Brand & Footer Widgets */
        .sidebar-brand-box {
            padding: 1.25rem 1rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }
        
        .sidebar-brand-icon {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--admin-primary), var(--admin-cocoa-light));
            display: grid;
            place-items: center;
            font-size: 1.4rem;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        }

        .sidebar-user-card {
            background: var(--admin-sidebar-soft);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px;
            margin: 1rem 0;
        }

        /* ============================================================
           FULL-SCREEN DEDICATED LOGIN PAGE (adminHMD Auth)
           ============================================================ */
        .login-wrapper {
            max-width: 520px;
            margin: 30px auto;
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 16px;
            padding: 40px;
            box-shadow: var(--admin-shadow-lg);
        }
        
        .login-brand-header {
            text-align: center;
            margin-bottom: 28px;
        }
        
        .login-brand-logo {
            width: 64px;
            height: 64px;
            margin: 0 auto 16px auto;
            background: linear-gradient(135deg, var(--admin-primary), var(--admin-cocoa));
            border-radius: 16px;
            display: grid;
            place-items: center;
            font-size: 2.2rem;
            color: #ffffff;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
        }
        
        .login-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--admin-text);
            margin: 0 0 6px 0;
        }
        
        .login-subtitle {
            font-size: 0.9rem;
            color: var(--admin-muted);
            margin: 0;
        }

        /* ============================================================
           TOPBAR NAVBAR - adminHMD (.admin-navbar)
           ============================================================ */
        .admin-topbar {
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 14px;
            padding: 14px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--admin-shadow-sm);
        }
        
        .admin-topbar-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--admin-text);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .admin-topbar-meta {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        /* ============================================================
           CARDS & CONTAINERS - adminHMD (.card, .metric-card)
           ============================================================ */
        .admin-card {
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: var(--admin-shadow-sm);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .admin-card:hover {
            box-shadow: var(--admin-shadow);
        }

        .admin-page-header {
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-left: 5px solid var(--admin-primary);
            border-radius: 14px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: var(--admin-shadow-sm);
        }
        
        .admin-page-header h1 {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 800 !important;
            font-size: 1.8rem !important;
            color: var(--admin-text) !important;
            margin-bottom: 6px !important;
        }
        
        .admin-page-header p {
            color: var(--admin-muted);
            margin: 0;
            font-size: 0.95rem;
        }

        /* Metric Widgets */
        .metric-widget {
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 14px;
            padding: 20px;
            box-shadow: var(--admin-shadow-sm);
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .metric-icon-box {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            font-size: 1.4rem;
            flex-shrink: 0;
        }
        
        .metric-icon-blue { background: #dbeafe; color: #1d4ed8; }
        .metric-icon-green { background: #ccfbf1; color: #0f766e; }
        .metric-icon-amber { background: #fef3c7; color: #d97706; }
        .metric-icon-purple { background: #f3e8ff; color: #7e22ce; }

        .metric-val {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--admin-text);
            line-height: 1.2;
        }
        
        .metric-lbl {
            font-size: 0.82rem;
            color: var(--admin-muted);
            font-weight: 500;
        }

        /* ============================================================
           STATUS BADGES - adminHMD (.badge)
           ============================================================ */
        .admin-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        
        .badge-admin { background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
        .badge-penangkar { background: #ccfbf1; color: #0f766e; border: 1px solid #99f6e4; }
        .badge-petani { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
        .badge-pengepul { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .badge-perusahaan { background: #ffe4e6; color: #9f1239; border: 1px solid #fecdd3; }
        .badge-connected { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .badge-disconnected { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

        /* ============================================================
           INPUT CONTROLS & BUTTONS - adminHMD Form Style
           ============================================================ */
        .stTextInput input, 
        .stNumberInput input, 
        .stSelectbox > div > div {
            background-color: var(--admin-surface) !important;
            border: 1px solid var(--admin-border) !important;
            border-radius: 8px !important;
            color: var(--admin-text) !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem !important;
            box-shadow: none !important;
        }
        
        .stTextInput input:focus, 
        .stNumberInput input:focus {
            border-color: var(--admin-primary) !important;
            box-shadow: var(--admin-ring) !important;
        }

        .stButton > button {
            background-color: var(--admin-primary) !important;
            color: #ffffff !important;
            border: 1px solid var(--admin-primary) !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 0.55rem 1.4rem !important;
            transition: all 0.2s ease !important;
            box-shadow: var(--admin-shadow-sm) !important;
        }
        
        .stButton > button:hover {
            background-color: var(--admin-primary-dark) !important;
            border-color: var(--admin-primary-dark) !important;
            color: #ffffff !important;
            box-shadow: var(--admin-shadow) !important;
            transform: translateY(-1px) !important;
        }

        /* Streamlit Dataframe / Table Overrides */
        [data-testid="stTable"], .stDataFrame {
            background-color: var(--admin-surface) !important;
            border: 1px solid var(--admin-border) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background-color: var(--admin-surface) !important;
            border: 1px solid var(--admin-border) !important;
            border-radius: 10px !important;
            padding: 4px !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px !important;
            color: var(--admin-muted) !important;
            font-weight: 600 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--admin-primary) !important;
            color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)
