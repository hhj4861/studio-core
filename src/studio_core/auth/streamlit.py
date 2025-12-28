"""
studio_core/auth/streamlit.py
Streamlit 전용 인증 헬퍼 (이메일/비밀번호 + OAuth)
"""

from functools import wraps
from typing import Optional, Callable, Literal
import streamlit as st

from studio_core.auth.supabase import SupabaseAuth, OAuthProvider, generate_pkce_pair
from studio_core.auth.session import Session, User


# 세션 상태 키
_AUTH_KEY = "_studio_auth"
_SESSION_KEY = "_studio_session"
_USER_KEY = "_studio_user"
_PKCE_VERIFIER_KEY = "_studio_pkce_verifier"


def get_auth() -> SupabaseAuth:
    """Supabase Auth 클라이언트 가져오기 (싱글톤)"""
    if _AUTH_KEY not in st.session_state:
        st.session_state[_AUTH_KEY] = SupabaseAuth()
    return st.session_state[_AUTH_KEY]


def get_session() -> Optional[Session]:
    """현재 세션 가져오기"""
    return st.session_state.get(_SESSION_KEY)


def get_user() -> Optional[User]:
    """현재 사용자 가져오기"""
    return st.session_state.get(_USER_KEY)


def is_authenticated() -> bool:
    """인증 여부 확인"""
    session = get_session()
    return session is not None and not session.is_expired()


def set_session(session: Session) -> None:
    """세션 저장"""
    st.session_state[_SESSION_KEY] = session
    st.session_state[_USER_KEY] = session.user


def clear_session() -> None:
    """세션 삭제"""
    st.session_state.pop(_SESSION_KEY, None)
    st.session_state.pop(_USER_KEY, None)


def require_auth(func: Callable) -> Callable:
    """
    인증 필수 데코레이터

    인증되지 않은 경우 로그인 페이지로 리다이렉트

    Example:
        >>> @require_auth
        ... def my_protected_page():
        ...     st.write("인증된 사용자만 접근 가능")
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("로그인이 필요합니다.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def login(email: str, password: str) -> bool:
    """
    로그인 수행

    Returns:
        성공 여부
    """
    try:
        auth = get_auth()
        session = auth.sign_in(email, password)
        set_session(session)
        return True
    except Exception as e:
        st.error(f"로그인 실패: {str(e)}")
        return False


def logout() -> None:
    """로그아웃 수행"""
    try:
        auth = get_auth()
        auth.sign_out()
    except Exception:
        pass
    finally:
        clear_session()


def signup(email: str, password: str) -> bool:
    """
    회원가입 수행

    Returns:
        성공 여부
    """
    try:
        auth = get_auth()
        auth.sign_up(email, password)
        return True
    except Exception as e:
        st.error(f"회원가입 실패: {str(e)}")
        return False


# ============================================================
# OAuth 인증
# ============================================================

def get_current_url() -> str:
    """현재 페이지 URL 가져오기"""
    # Streamlit Cloud나 로컬에서 동작
    try:
        # st.context가 있는 경우 (Streamlit 1.31+)
        if hasattr(st, 'context'):
            return st.context.headers.get("origin", "http://localhost:8501")
    except Exception:
        pass

    # 기본값
    return "http://localhost:8501"


def login_with_google(redirect_url: Optional[str] = None) -> None:
    """
    Google OAuth 로그인 시작

    사용자를 Google 로그인 페이지로 리다이렉트합니다.

    Args:
        redirect_url: 인증 후 리다이렉트 URL (기본: 현재 페이지)

    Example:
        >>> if google_oauth_button():
        ...     login_with_google()
    """
    login_with_oauth("google", redirect_url)


def login_with_oauth(
    provider: OAuthProvider,
    redirect_url: Optional[str] = None,
) -> None:
    """
    OAuth 로그인 시작

    사용자를 OAuth 프로바이더 로그인 페이지로 리다이렉트합니다.
    PKCE 없이 implicit flow를 사용합니다.

    Args:
        provider: OAuth 프로바이더 ("google", "github", "kakao", "apple")
        redirect_url: 인증 후 리다이렉트 URL

    Example:
        >>> login_with_oauth("google")
        >>> login_with_oauth("github", redirect_url="http://localhost:8503")
    """
    try:
        auth = get_auth()
        url = redirect_url or get_current_url()

        # Supabase OAuth URL 직접 생성 (implicit flow - 토큰 직접 반환)
        from urllib.parse import urlencode

        params = {
            "provider": provider,
            "redirect_to": url,
            "response_type": "token",  # implicit flow - access_token 직접 반환
        }

        oauth_url = f"{auth.url}/auth/v1/authorize?{urlencode(params)}"

        # JavaScript로 자동 리다이렉트
        st.markdown(
            f'''
            <script>
                window.location.href = "{oauth_url}";
            </script>
            <meta http-equiv="refresh" content="0;url={oauth_url}">
            ''',
            unsafe_allow_html=True,
        )
        st.info(f"{provider.title()} 로그인 페이지로 이동 중...")
        st.stop()

    except Exception as e:
        st.error(f"OAuth 로그인 실패: {str(e)}")


def _get_pkce_verifier_from_cookie() -> Optional[str]:
    """쿠키에서 PKCE verifier 가져오기"""
    try:
        # Streamlit 1.37+ 에서 st.context.cookies 사용 가능
        if hasattr(st, 'context') and hasattr(st.context, 'cookies'):
            return st.context.cookies.get('pkce_verifier')
    except Exception:
        pass
    return None


def handle_oauth_callback() -> bool:
    """
    OAuth 콜백 처리

    URL에서 인증 토큰을 추출하고 세션을 생성합니다.
    implicit flow의 경우 URL hash에서 토큰을 추출합니다.
    페이지 로드 시 자동으로 호출하세요.

    Returns:
        인증 성공 여부

    Example:
        >>> # 앱 시작 부분에서 호출
        >>> if handle_oauth_callback():
        ...     st.success("로그인 성공!")
        ...     st.rerun()
    """
    try:
        # URL 파라미터에서 토큰/코드 확인
        params = st.query_params

        # URL hash에서 토큰 추출을 위한 JavaScript 주입
        # implicit flow는 #access_token=xxx 형태로 반환됨
        # JavaScript로 hash를 query params로 변환하여 페이지 리로드
        st.markdown(
            '''
            <script>
                (function() {
                    if (window.location.hash && window.location.hash.includes('access_token')) {
                        // hash에서 파라미터 추출
                        const hash = window.location.hash.substring(1);
                        const params = new URLSearchParams(hash);
                        const accessToken = params.get('access_token');
                        const refreshToken = params.get('refresh_token');

                        if (accessToken) {
                            // query params로 변환하여 리로드
                            const url = new URL(window.location.href.split('#')[0]);
                            url.searchParams.set('access_token', accessToken);
                            if (refreshToken) {
                                url.searchParams.set('refresh_token', refreshToken);
                            }
                            window.location.href = url.toString();
                        }
                    }
                })();
            </script>
            ''',
            unsafe_allow_html=True,
        )

        # access_token이 있는 경우 (implicit flow - query params로 변환됨)
        access_token = params.get("access_token")
        refresh_token = params.get("refresh_token")

        if access_token:
            auth = get_auth()
            session = auth.handle_oauth_callback(access_token, refresh_token)
            set_session(session)

            # URL 파라미터 정리
            st.query_params.clear()
            return True

        # code가 있는 경우 (authorization code flow)
        code = params.get("code")

        if code:
            # 세션 교환 수행 (Supabase가 PKCE 처리)
            auth = get_auth()
            session = auth.exchange_code_for_session(code)
            set_session(session)

            # PKCE verifier 정리
            st.session_state.pop(_PKCE_VERIFIER_KEY, None)

            # URL 파라미터 정리
            st.query_params.clear()
            return True

        return False

    except Exception as e:
        st.error(f"OAuth 인증 처리 실패: {str(e)}")
        # 에러 시에도 파라미터 정리
        try:
            st.query_params.clear()
            st.session_state.pop(_PKCE_VERIFIER_KEY, None)
        except Exception:
            pass
        return False


def init_auth() -> Optional[Session]:
    """
    인증 초기화

    앱 시작 시 호출하여:
    1. OAuth 콜백 처리
    2. 기존 세션 복원
    3. 세션 유효성 검증

    Returns:
        현재 세션 (없으면 None)

    Example:
        >>> # app.py 시작 부분
        >>> session = init_auth()
        >>> if session:
        ...     st.write(f"환영합니다, {session.user.email}")
        ... else:
        ...     show_login_page()
    """
    # 1. OAuth 콜백 처리
    if handle_oauth_callback():
        st.rerun()

    # 2. 기존 세션 확인
    session = get_session()

    if session:
        # 3. 세션 만료 확인
        if session.is_expired():
            # 세션 갱신 시도
            try:
                auth = get_auth()
                new_session = auth.refresh_session()
                if new_session:
                    set_session(new_session)
                    return new_session
                else:
                    clear_session()
                    return None
            except Exception:
                clear_session()
                return None

        return session

    return None
