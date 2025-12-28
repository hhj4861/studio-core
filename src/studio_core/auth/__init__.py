"""
studio_core/auth - 인증 모듈
"""

from studio_core.auth.supabase import SupabaseAuth
from studio_core.auth.session import Session, User

__all__ = ["SupabaseAuth", "Session", "User"]
