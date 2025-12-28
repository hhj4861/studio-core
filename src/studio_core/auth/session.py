"""
studio_core/auth/session.py
세션 및 사용자 모델
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """사용자 정보"""
    id: str
    email: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_supabase(cls, user_data: dict) -> "User":
        """Supabase 응답에서 User 생성"""
        return cls(
            id=user_data.get("id", ""),
            email=user_data.get("email", ""),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at"),
        )


@dataclass
class Session:
    """세션 정보"""
    access_token: str
    refresh_token: str
    user: User
    expires_at: Optional[int] = None

    @classmethod
    def from_supabase(cls, session_data: dict) -> "Session":
        """Supabase 응답에서 Session 생성"""
        user_data = session_data.get("user", {})
        return cls(
            access_token=session_data.get("access_token", ""),
            refresh_token=session_data.get("refresh_token", ""),
            user=User.from_supabase(user_data),
            expires_at=session_data.get("expires_at"),
        )

    def is_expired(self) -> bool:
        """세션 만료 여부"""
        if self.expires_at is None:
            return False
        return datetime.now().timestamp() > self.expires_at
