"""
studio-core + studio-ui 연동 테스트 (OAuth 포함)
실행: cd /Users/honghyeonjong/home/IdeaProjects/studio-core && streamlit run examples/test_auth.py --server.port 8503
"""

import streamlit as st
import sys
import os

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv("/Users/honghyeonjong/home/IdeaProjects/studio-core/.env")

# 로컬 패키지 경로 추가 (절대 경로)
sys.path.insert(0, "/Users/honghyeonjong/home/IdeaProjects/studio-core/src")
sys.path.insert(0, "/Users/honghyeonjong/home/IdeaProjects/studio-ui/src")

from studio_ui import apply_theme
from studio_ui.components import login_form, signup_form, logout_button, user_menu

# studio-core auth 함수들
from studio_core.auth.streamlit import (
    init_auth,
    login,
    login_with_google,
    logout,
    is_authenticated,
    get_user,
    get_session,
)

# 테마 적용
apply_theme()

st.title("🔐 인증 테스트")

# ⚠️ [중요] OAuth 콜백 처리 - 페이지 로드 시 최초 실행
# Google OAuth 리다이렉트 후 URL 파라미터(code, access_token)를 처리
session = init_auth()

# 디버그: 현재 상태 확인
with st.expander("🔧 디버그 정보", expanded=False):
    st.write("session:", session)
    st.write("is_authenticated:", is_authenticated())
    st.write("query_params:", dict(st.query_params))

# 인증된 사용자 화면
if session or is_authenticated():
    user = get_user()

    # 디버그: user 객체 확인
    st.write("DEBUG user:", user)

    st.success(f"✅ Google OAuth 로그인 성공!")

    # 프로필 카드
    st.markdown("""
    <style>
    .profile-card {
        background: linear-gradient(135deg, #fffdfb 0%, #f8f5f0 100%);
        border: 1px solid #e8e2d9;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .profile-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
    }
    .profile-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 3px solid #c9a87c;
    }
    .profile-info h2 {
        margin: 0;
        color: #2d251f;
        font-size: 1.5rem;
    }
    .profile-info p {
        margin: 4px 0 0 0;
        color: #8b7355;
        font-size: 0.9rem;
    }
    .profile-badge {
        display: inline-block;
        background: #e8f5ed;
        color: #4a9d6b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .profile-details {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #e8e2d9;
    }
    .detail-item {
        background: #fffdfb;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #f0ebe5;
    }
    .detail-label {
        font-size: 0.7rem;
        color: #8b7355;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .detail-value {
        font-size: 0.9rem;
        color: #2d251f;
        font-weight: 500;
        word-break: break-all;
    }
    </style>
    """, unsafe_allow_html=True)

    if user:
        avatar_html = f'<img src="{user.avatar_url}" class="profile-avatar" />' if user.avatar_url else '<div class="profile-avatar" style="background:#c9a87c;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;">👤</div>'

        st.markdown(f"""
        <div class="profile-card">
            <div class="profile-header">
                {avatar_html}
                <div class="profile-info">
                    <h2>{user.name or user.email.split('@')[0]}</h2>
                    <p>{user.email}</p>
                    <span class="profile-badge">✓ {user.provider.upper() if user.provider else 'EMAIL'} 인증</span>
                </div>
            </div>
            <div class="profile-details">
                <div class="detail-item">
                    <div class="detail-label">사용자 ID</div>
                    <div class="detail-value">{user.id[:8]}...</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">인증 방식</div>
                    <div class="detail-value">{user.provider or 'email'}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 로그아웃 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if logout_button(label="로그아웃", key="main_logout"):
            logout()
            st.rerun()

    st.divider()

    # 세션 상세 정보 (접기)
    with st.expander("📋 세션 상세 정보"):
        if session and session.user:
            st.json({
                "user_id": session.user.id,
                "email": session.user.email,
                "name": session.user.name,
                "avatar_url": session.user.avatar_url,
                "provider": session.user.provider,
                "expires_at": str(session.expires_at) if session.expires_at else None,
                "is_expired": session.is_expired(),
            })

else:
    # 미인증 사용자 - 로그인/회원가입 폼

    # OAuth 환경 확인
    import os
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        st.warning("""
        ⚠️ **환경변수 설정 필요**

        Google OAuth를 사용하려면 다음 환경변수를 설정하세요:
        ```bash
        export SUPABASE_URL="https://xxx.supabase.co"
        export SUPABASE_KEY="your-anon-key"
        ```

        그리고 Supabase 대시보드에서:
        1. Authentication > Providers > Google 활성화
        2. Google Cloud Console에서 OAuth 클라이언트 생성
        3. Redirect URL: `https://xxx.supabase.co/auth/v1/callback`
        """)

    # 탭으로 로그인/회원가입 분리
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        st.subheader("로그인")

        result = login_form(key="test_login")

        # ⚠️ [사용중 - 수정주의] Google OAuth 실제 실행
        if result.oauth_provider == "google":
            st.info("🔵 Google 로그인 페이지로 이동 중...")
            login_with_google(redirect_url="http://localhost:8503")

        # 이메일/비밀번호 로그인
        if result.submitted:
            if result.email and result.password:
                if login(result.email, result.password):
                    st.success("✅ 로그인 성공!")
                    st.rerun()
            else:
                st.error("이메일과 비밀번호를 입력하세요")

    with tab2:
        st.subheader("회원가입")

        result = signup_form(key="test_signup")

        # ⚠️ [사용중 - 수정주의] Google OAuth 회원가입 실제 실행
        if result.oauth_provider == "google":
            st.info("🔵 Google 로그인 페이지로 이동 중...")
            login_with_google(redirect_url="http://localhost:8503")

        # 이메일/비밀번호 회원가입
        if result.submitted:
            if not result.passwords_match:
                st.error("비밀번호가 일치하지 않습니다")
            elif result.email and result.password:
                from studio_core.auth.streamlit import signup
                if signup(result.email, result.password):
                    st.success("✅ 회원가입 성공! 이메일을 확인하세요.")
            else:
                st.error("모든 필드를 입력하세요")

st.divider()

# 사용법 안내
with st.expander("📖 사용법 보기"):
    st.code("""
# 1. 패키지 설치
pip install -e /path/to/studio-core
pip install -e /path/to/studio-ui

# 2. 환경변수 설정
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-anon-key"

# 3. 앱에서 사용
from studio_ui import apply_theme
from studio_ui.components import login_form
from studio_core.auth.streamlit import (
    init_auth,
    login,
    login_with_google,
    logout,
    is_authenticated,
    get_user,
)

# 테마 적용
apply_theme()

# ⚠️ [필수] 인증 초기화 - OAuth 콜백 자동 처리
session = init_auth()

if session:
    # 로그인된 상태
    user = get_user()
    st.write(f"환영합니다, {user.email}")
    if st.button("로그아웃"):
        logout()
        st.rerun()
else:
    # 로그인 폼
    result = login_form()

    # Google OAuth 클릭 시 실제 OAuth 시작
    if result.oauth_provider == "google":
        login_with_google()

    # 이메일/비밀번호 로그인
    if result.submitted:
        if login(result.email, result.password):
            st.rerun()
""", language="python")
