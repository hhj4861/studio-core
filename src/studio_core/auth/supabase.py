"""
studio_core/auth/supabase.py
Supabase Auth 연동
"""

import os
from typing import Optional
from supabase import create_client, Client

from studio_core.auth.session import Session, User


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
