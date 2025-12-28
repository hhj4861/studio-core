"""
studio_core/auth/streamlit.py
Streamlit 전용 인증 헬퍼
"""

from functools import wraps
from typing import Optional, Callable
import streamlit as st

from studio_core.auth.supabase import SupabaseAuth
from studio_core.auth.session import Session, User


# 세션 상태 키
_AUTH_KEY = "_studio_auth"
_SESSION_KEY = "_studio_session"
_USER_KEY = "_studio_user"


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
