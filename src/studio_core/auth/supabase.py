"""
studio_core/auth/supabase.py
Supabase Auth 연동 (이메일/비밀번호 + OAuth)
"""

import os
import secrets
import hashlib
import base64
from typing import Optional, Literal, Tuple
from supabase import create_client, Client

from studio_core.auth.session import Session, User


# 지원하는 OAuth 프로바이더
OAuthProvider = Literal["google", "github", "kakao", "apple"]


def generate_pkce_pair() -> Tuple[str, str]:
    """
    PKCE code_verifier와 code_challenge 생성

    Returns:
        (code_verifier, code_challenge) 튜플
    """
    # code_verifier: 43-128자의 랜덤 문자열
    code_verifier = secrets.token_urlsafe(32)

    # code_challenge: code_verifier의 SHA256 해시를 base64url 인코딩
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    return code_verifier, code_challenge


class AuthError(Exception):
    """인증 관련 에러"""
    pass


class SupabaseAuth:
    """Supabase 인증 클라이언트"""

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """
        Args:
            url: Supabase URL (기본: SUPABASE_URL 환경변수)
            key: Supabase Anon Key (기본: SUPABASE_KEY 환경변수)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise AuthError(
                "Supabase URL과 Key가 필요합니다. "
                "환경변수 SUPABASE_URL, SUPABASE_KEY를 설정하거나 "
                "직접 전달하세요."
            )

        self._client: Client = create_client(self.url, self.key)
        self._session: Optional[Session] = None

    def sign_up(self, email: str, password: str) -> User:
        """
        회원가입

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            생성된 User

        Raises:
            AuthError: 회원가입 실패 시
        """
        try:
            response = self._client.auth.sign_up({
                "email": email,
                "password": password,
            })

            if response.user is None:
                raise AuthError("회원가입에 실패했습니다.")

            return User.from_supabase(response.user.__dict__)

        except Exception as e:
            raise AuthError(f"회원가입 실패: {str(e)}")

    def sign_in(self, email: str, password: str) -> Session:
        """
        로그인

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            Session 객체

        Raises:
            AuthError: 로그인 실패 시
        """
        try:
            response = self._client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            if response.session is None:
                raise AuthError("로그인에 실패했습니다.")

            self._session = Session.from_supabase(response.session.__dict__)
            return self._session

        except Exception as e:
            raise AuthError(f"로그인 실패: {str(e)}")

    def sign_out(self) -> None:
        """로그아웃"""
        try:
            self._client.auth.sign_out()
            self._session = None
        except Exception as e:
            raise AuthError(f"로그아웃 실패: {str(e)}")

    def get_current_user(self) -> Optional[User]:
        """현재 로그인된 사용자 조회"""
        try:
            response = self._client.auth.get_user()
            if response and response.user:
                return User.from_supabase(response.user.__dict__)
            return None
        except Exception:
            return None

    def get_session(self) -> Optional[Session]:
        """현재 세션 조회"""
        return self._session

    def refresh_session(self) -> Optional[Session]:
        """세션 갱신"""
        try:
            response = self._client.auth.refresh_session()
            if response.session:
                self._session = Session.from_supabase(response.session.__dict__)
                return self._session
            return None
        except Exception:
            return None

    def reset_password(self, email: str) -> bool:
        """
        비밀번호 재설정 이메일 발송

        Args:
            email: 이메일

        Returns:
            성공 여부
        """
        try:
            self._client.auth.reset_password_email(email)
            return True
        except Exception:
            return False

    # ============================================================
    # OAuth 인증
    # ============================================================

    def get_oauth_url(
        self,
        provider: OAuthProvider,
        redirect_url: Optional[str] = None,
        scopes: Optional[str] = None,
        code_challenge: Optional[str] = None,
    ) -> str:
        """
        OAuth 로그인 URL 생성

        Args:
            provider: OAuth 프로바이더 ("google", "github", "kakao", "apple")
            redirect_url: 인증 후 리다이렉트 URL (기본: 현재 페이지)
            scopes: 추가 권한 스코프 (예: "email profile")
            code_challenge: PKCE code_challenge (generate_pkce_pair()로 생성)

        Returns:
            OAuth 로그인 URL

        Example:
            >>> auth = SupabaseAuth()
            >>> verifier, challenge = generate_pkce_pair()
            >>> url = auth.get_oauth_url("google", redirect_url="http://localhost:8503", code_challenge=challenge)
            >>> # verifier를 저장하고, 사용자를 url로 리다이렉트
        """
        try:
            # PKCE를 수동으로 처리하기 위해 URL 직접 구성
            from urllib.parse import urlencode

            params = {
                "provider": provider,
                "redirect_to": redirect_url or "",
            }

            if scopes:
                params["scopes"] = scopes

            if code_challenge:
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"

            # Supabase OAuth URL 직접 구성
            oauth_url = f"{self.url}/auth/v1/authorize?{urlencode(params)}"
            return oauth_url

        except Exception as e:
            raise AuthError(f"OAuth URL 생성 실패: {str(e)}")

    def sign_in_with_oauth(
        self,
        provider: OAuthProvider,
        redirect_url: Optional[str] = None,
    ) -> str:
        """
        OAuth 로그인 시작 (URL 반환)

        Args:
            provider: OAuth 프로바이더
            redirect_url: 인증 후 리다이렉트 URL

        Returns:
            OAuth 로그인 URL (이 URL로 리다이렉트 필요)
        """
        return self.get_oauth_url(provider, redirect_url)

    def handle_oauth_callback(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
    ) -> Session:
        """
        OAuth 콜백 처리 (토큰으로 세션 생성)

        Args:
            access_token: OAuth에서 받은 access token
            refresh_token: OAuth에서 받은 refresh token

        Returns:
            Session 객체

        Example:
            >>> # URL에서 토큰 추출 후
            >>> session = auth.handle_oauth_callback(access_token, refresh_token)
        """
        try:
            response = self._client.auth.set_session(access_token, refresh_token or "")

            if response.session is None:
                raise AuthError("OAuth 세션 생성에 실패했습니다.")

            self._session = Session.from_supabase(response.session.__dict__)
            return self._session

        except Exception as e:
            raise AuthError(f"OAuth 콜백 처리 실패: {str(e)}")

    def exchange_code_for_session(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> Session:
        """
        OAuth 인증 코드를 세션으로 교환

        Args:
            code: OAuth 인증 코드 (URL의 code 파라미터)
            code_verifier: PKCE code_verifier (OAuth 시작 시 저장한 값)

        Returns:
            Session 객체

        Example:
            >>> # URL: http://localhost:8503?code=abc123
            >>> code = st.query_params.get("code")
            >>> verifier = st.session_state.get("pkce_verifier")
            >>> if code and verifier:
            ...     session = auth.exchange_code_for_session(code, verifier)
        """
        try:
            # PKCE code_verifier가 있으면 포함
            params = {"auth_code": code}
            if code_verifier:
                params["code_verifier"] = code_verifier

            response = self._client.auth.exchange_code_for_session(params)

            if response.session is None:
                raise AuthError("인증 코드 교환에 실패했습니다.")

            self._session = Session.from_supabase(response.session.__dict__)
            return self._session

        except Exception as e:
            raise AuthError(f"인증 코드 교환 실패: {str(e)}")
