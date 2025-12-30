'use client';

import * as React from 'react';
import type { User, Session, AuthState, OAuthProvider } from '../types/auth';

export interface AuthContextType extends AuthState {
  /** 이메일/비밀번호 로그인 */
  signIn: (email: string, password: string) => Promise<void>;
  /** 회원가입 */
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  /** 로그아웃 */
  signOut: () => Promise<void>;
  /** OAuth 로그인 */
  signInWithOAuth: (provider: OAuthProvider) => Promise<void>;
  /** 세션 새로고침 */
  refreshSession: () => Promise<void>;
  /** 에러 메시지 */
  error: string | null;
  /** 에러 초기화 */
  clearError: () => void;
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function useAuthContext(): AuthContextType {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
