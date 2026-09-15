import contextlib

import streamlit as st
from supabase import Client, create_client

from config import APP_URL, SUPABASE_KEY, SUPABASE_URL

# Lazy Supabase client initialization (so app works before real credentials)
_auth_client: Client | None = None


def get_auth_client() -> Client:
    """Lazily create and return the Supabase auth client"""
    global _auth_client
    if _auth_client is None:
        _auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _auth_client


def init_session_state():
    """Initialize session state variables"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "auth_error" not in st.session_state:
        st.session_state.auth_error = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None


def _user_to_dict(user) -> dict | None:
    """Convert a supabase User (pydantic model) to a plain dict for session storage"""
    if user is None:
        return None
    if isinstance(user, dict):
        return user
    for method in ("model_dump", "dict"):
        converter = getattr(user, method, None)
        if callable(converter):
            with contextlib.suppress(Exception):
                return converter()
    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "user_metadata": getattr(user, "user_metadata", {}) or {},
    }


def get_current_user() -> dict | None:
    """Get the current logged-in user"""
    if st.session_state.get("is_authenticated"):
        return st.session_state.get("user")
    return None


def sign_up_with_email(email: str, password: str, name: str = None) -> dict:
    """Sign up a new user with email/password"""
    try:
        user_data = {"email": email, "password": password, "options": {}}
        if name:
            user_data["options"]["data"] = {"full_name": name}
        result = get_auth_client().auth.sign_up(user_data)
        return {"success": True, "user": _user_to_dict(result.user), "session": result.session}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in_with_email(email: str, password: str) -> dict:
    """Sign in existing user with email/password"""
    try:
        result = get_auth_client().auth.sign_in_with_password({"email": email, "password": password})
        if result.session:
            st.session_state.access_token = result.session.access_token
            st.session_state.refresh_token = result.session.refresh_token
        return {"success": True, "user": _user_to_dict(result.user), "session": result.session}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in_with_google():
    """Get Google OAuth URL for login"""
    try:
        # This returns a URL the user must visit to authenticate
        result = get_auth_client().auth.sign_in_with_oauth(
            {"provider": "google", "options": {"redirect_to": APP_URL}}
        )
        return {"success": True, "url": result.url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_oauth_callback():
    """Handle OAuth callback (for Streamlit Cloud hosting)"""
    query_params = st.query_params
    if "code" in query_params:
        try:
            result = get_auth_client().auth.exchange_code_for_session({"auth_code": query_params.get("code")})
            if result.session:
                st.session_state.access_token = result.session.access_token
                st.session_state.refresh_token = result.session.refresh_token
                st.session_state.user = _user_to_dict(result.user)
                st.session_state.is_authenticated = True
                st.query_params.clear()
                return True
        except Exception as e:
            st.session_state.auth_error = str(e)
    return False


def sign_out():
    """Sign out the current user"""
    with contextlib.suppress(Exception):
        get_auth_client().auth.sign_out()
    st.session_state.user = None
    st.session_state.is_authenticated = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None


def render_login_page():
    """Render the login page UI"""
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            background: #1E2130;
            border-radius: 16px;
            border: 1px solid #3A3F5C;
        }
        .login-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            color: #AAAAAA;
            margin-bottom: 2rem;
        }
        .divider {
            text-align: center;
            margin: 20px 0;
            color: #666;
            border-bottom: 1px solid #3A3F5C;
            line-height: 0.1em;
        }
        .divider span {
            background: #1E2130;
            padding: 0 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-container">
            <div class="login-title">🔮 AI Price Predictor</div>
            <div class="login-subtitle">Know when to buy. Save money.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", type="primary", use_container_width=True):
                if email and password:
                    result = sign_in_with_email(email, password)
                    if result["success"]:
                        st.session_state.user = result["user"]
                        st.session_state.is_authenticated = True
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result['error']}")
                else:
                    st.warning("Please enter email and password")
        with col2:
            google_result = sign_in_with_google()
            google_url = google_result.get("url") if google_result.get("success") else None
            if google_url:
                st.link_button("Login with Google", google_url, use_container_width=True)
            else:
                st.markdown(
                    '<a href="https://accounts.google.com" target="_blank" '
                    'style="display:block;text-align:center;padding:0.5rem;'
                    "border:1px solid #FF6B6B;border-radius:8px;text-decoration:none;"
                    'color:#FF6B6B;">Login with Google</a>',
                    unsafe_allow_html=True,
                )

    with tab2:
        st.text_input("👤 Full Name", key="signup_name")
        st.text_input("📧 Email", key="signup_email")
        st.text_input("🔒 Password", type="password", key="signup_password")
        st.text_input("🔒 Confirm Password", type="password", key="signup_confirm_password")

        if st.button("Create Account", type="primary", use_container_width=True):
            name = st.session_state.get("signup_name", "")
            email = st.session_state.get("signup_email", "")
            password = st.session_state.get("signup_password", "")
            confirm = st.session_state.get("signup_confirm_password", "")

            if not email or not password:
                st.warning("Please fill all fields")
            elif password != confirm:
                st.error("Passwords don't match")
            elif len(password) < 6:
                st.warning("Password must be at least 6 characters")
            else:
                result = sign_up_with_email(email, password, name)
                if result["success"]:
                    st.success("Account created! Check your email to confirm.")
                    st.session_state.user = result["user"]
                    st.session_state.is_authenticated = True
                    st.rerun()
                else:
                    st.error(f"Sign up failed: {result['error']}")


def require_auth():
    """Require authentication - show login if not authenticated"""
    init_session_state()

    if not st.session_state.get("is_authenticated"):
        render_login_page()
        return False
    return True
