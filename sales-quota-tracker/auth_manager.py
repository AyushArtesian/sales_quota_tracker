"""
Azure AD Authentication Manager with MSAL
Handles OIDC/OAuth2 login with Azure AD
"""

import streamlit as st
from msal import ConfidentialClientApplication
import requests
from datetime import datetime

# ============================================================================
# ✅ ALLOWED USERS - Only these 2 can login
# ============================================================================
ALLOWED_USERS = [
    "ayush.mittal@artesian.io"
]


def get_auth_config():
    """Get Azure AD configuration from secrets"""
    try:
        config = st.secrets["auth"]
        return {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "tenant_id": config["tenant_id"],
            "authority": f"https://login.microsoftonline.com/{config['tenant_id']}",
            "redirect_uri": config["redirect_uri"],
            "scopes": ["User.Read"],
        }
    except KeyError as e:
        st.error(f"❌ Missing auth config in secrets.toml: {e}")
        st.stop()


def get_msal_app():
    """Create and return MSAL ConfidentialClientApplication"""
    config = get_auth_config()
    return ConfidentialClientApplication(
        client_id=config["client_id"],
        client_credential=config["client_secret"],
        authority=config["authority"],
    )


def get_token_from_cache():
    """Get token from session state cache"""
    if "token" in st.session_state:
        return st.session_state.token
    return None


def save_token_to_cache(token):
    """Save token to session state"""
    st.session_state.token = token


def get_user_from_token(token):
    """Extract user info from access token and call Microsoft Graph"""
    try:
        config = get_auth_config()
        
        # Call Microsoft Graph to get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "email": user_data.get("userPrincipalName", user_data.get("mail", "")),
                "name": user_data.get("displayName", "User"),
                "id": user_data.get("id", ""),
                "is_logged_in": True,
            }
    except Exception as e:
        st.error(f"Error getting user info: {e}")
    return None


def is_user_allowed(user_email: str) -> bool:
    """Check if user email is in whitelist"""
    if not user_email:
        return False
    return user_email.lower() in [u.lower() for u in ALLOWED_USERS]


def check_authentication():
    """
    Main authentication flow with Azure AD
    Returns: True if authenticated and allowed, False otherwise
    """
    
    # Initialize session state
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "token" not in st.session_state:
        st.session_state.token = None
    if "auth_code_processed" not in st.session_state:
        st.session_state.auth_code_processed = False

    # Check if we have an authorization code in the URL (from Azure redirect)
    query_params = st.query_params
    if "code" in query_params and not st.session_state.auth_code_processed:
        auth_code = query_params["code"]
        if isinstance(auth_code, list):
            auth_code = auth_code[0]
        
        # Mark as processed BEFORE processing (prevent reuse)
        st.session_state.auth_code_processed = True
        
        handle_auth_code(auth_code)
        
        # Clear the query parameters to prevent reuse
        st.query_params.clear()

    # If not logged in, show login page
    if st.session_state.user_info is None:
        show_login_page()
        return False

    # If logged in but not in allowed list, show access denied
    user_email = st.session_state.user_info.get("email", "")
    if not is_user_allowed(user_email):
        show_access_denied(st.session_state.user_info)
        return False

    # ✅ User is authenticated and allowed
    return True


def show_login_page():
    """Display Azure AD login page"""
    st.set_page_config(
        page_title="Sales Quota Tracker - Login",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown("### 🔐 Sales Quota Tracker")
        st.markdown("#### Azure AD Authentication")
        st.markdown("---")

        st.info(
            "🔑 Use your Artesian Azure AD credentials to login.\n\n"
            "This application is restricted to authorized users only."
        )

        # Login button
        if st.button("🔐 Login with Azure AD", use_container_width=True, type="primary"):
            initiate_login()

        st.markdown("---")
        st.markdown(
            "<small>Allowed users: "
            + ", ".join([f"<code>{u}</code>" for u in ALLOWED_USERS])
            + "</small>",
            unsafe_allow_html=True,
        )


def initiate_login():
    """Initiate Azure AD login flow with JavaScript redirect"""
    try:
        config = get_auth_config()
        app = get_msal_app()
        
        # Get authorization URL (returns tuple: (auth_url, state))
        auth_url_result = app.get_authorization_request_url(
            scopes=config["scopes"],
            redirect_uri=config["redirect_uri"],
        )
        
        # Extract the URL (it's the first element of the tuple)
        auth_url = auth_url_result[0] if isinstance(auth_url_result, tuple) else auth_url_result
        
        # Store in session state so it persists
        st.session_state.auth_url = auth_url
        
        # Use JavaScript to perform the redirect
        st.markdown(
            f"""
            <script>
            window.location.href = "{auth_url}";
            </script>
            """,
            unsafe_allow_html=True,
        )
        
        # Fallback link in case JavaScript doesn't work
        st.info(f"Redirecting to Azure AD login... If you're not redirected, [click here]({auth_url})")
        
    except Exception as e:
        st.error(f"❌ Login error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def handle_auth_code(auth_code: str):
    """Handle authorization code from Azure redirect"""
    try:
        config = get_auth_config()
        app = get_msal_app()
        
        st.info("🔄 Authenticating with Azure AD...")
        
        # Exchange authorization code for token
        result = app.acquire_token_by_authorization_code(
            code=auth_code,
            scopes=config["scopes"],
            redirect_uri=config["redirect_uri"],
        )
        
        if "error" in result:
            error_msg = result.get('error_description', result.get('error', 'Unknown error'))
            st.error(f"❌ Authentication failed: {error_msg}")
            # Reset the processed flag so user can try again
            st.session_state.auth_code_processed = False
            return
        
        if "access_token" in result:
            save_token_to_cache(result["access_token"])
            
            # Get user info from token via Microsoft Graph
            user_info = get_user_from_token(result["access_token"])
            if user_info:
                st.session_state.user_info = user_info
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Could not retrieve user information from Azure AD")
                st.session_state.auth_code_processed = False
        else:
            st.error(f"❌ No access token received: {result}")
            st.session_state.auth_code_processed = False
            
    except Exception as e:
        st.error(f"❌ Error during authentication: {str(e)}")
        st.session_state.auth_code_processed = False


def show_access_denied(user_info):
    """Display access denied page"""
    st.set_page_config(
        page_title="Access Denied",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.error("❌ Access Denied")

        user_email = user_info.get("email", "Unknown")
        user_name = user_info.get("name", "User")

        st.markdown(f"**Name**: {user_name}")
        st.markdown(f"**Email**: `{user_email}`")

        st.markdown("---")

        st.markdown(
            "This application is restricted to authorized users only.\n\n"
            "Contact your administrator to request access."
        )

        st.markdown("**Allowed users:**")
        for email in ALLOWED_USERS:
            st.markdown(f"- `{email}`")

        st.markdown("---")

        if st.button("🚪 Logout"):
            logout_user()


def logout_user():
    """Clear user session"""
    st.session_state.user_info = None
    st.session_state.token = None
    st.rerun()


def get_current_user():
    """Get current logged-in user info"""
    return st.session_state.get("user_info", None)


def show_logout_button():
    """Display user info and logout button in sidebar"""
    if st.session_state.get("user_info"):
        user = st.session_state.user_info
        user_name = user.get("name", "User")
        user_email = user.get("email", "")

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 {user_name}**")
        st.sidebar.caption(f"`{user_email}`")

        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout_user()