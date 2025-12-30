/**
 * Authentication types
 * Converted from Python studio_core/auth/session.py
 */

/** 사용자 정보 */
export interface User {
  id: string;
  email: string;
  name?: string;
  avatarUrl?: string;
  provider?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

/** 세션 정보 */
export interface Session {
  accessToken: string;
  refreshToken: string;
  user: User;
  expiresAt?: number;
}

/** OAuth 프로바이더 */
export type OAuthProvider = 'google' | 'github' | 'kakao' | 'apple';

/** 인증 상태 */
export interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

/** 인증 에러 */
export interface AuthError {
  message: string;
  code?: string;
}

/** Supabase 사용자 데이터를 User로 변환 */
export function userFromSupabase(userData: Record<string, unknown>): User {
  const metadata = (userData.user_metadata || {}) as Record<string, unknown>;
  const appMetadata = (userData.app_metadata || {}) as Record<string, unknown>;

  return {
    id: (userData.id as string) || '',
    email: (userData.email as string) || '',
    name: (metadata.full_name as string) || (metadata.name as string) || undefined,
    avatarUrl: (metadata.avatar_url as string) || (metadata.picture as string) || undefined,
    provider: appMetadata.provider as string | undefined,
    createdAt: userData.created_at ? new Date(userData.created_at as string) : undefined,
    updatedAt: userData.updated_at ? new Date(userData.updated_at as string) : undefined,
  };
}

/** 세션 만료 확인 */
export function isSessionExpired(session: Session): boolean {
  if (!session.expiresAt) return false;
  return Date.now() / 1000 > session.expiresAt;
}
