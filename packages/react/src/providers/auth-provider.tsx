'use client';

import * as React from 'react';
import type { SupabaseClient, AuthChangeEvent } from '@supabase/supabase-js';
import { AuthContext, type AuthContextType } from '../context/auth-context';
import type { User, Session, OAuthProvider } from '../types/auth';
import { userFromSupabase } from '../types/auth';

export interface AuthProviderProps {
  children: React.ReactNode;
  /** Supabase 클라이언트 인스턴스 */
  supabaseClient: SupabaseClient;
  /** OAuth 리다이렉트 URL */
  redirectUrl?: string;
}

export function AuthProvider({
  children,
  supabaseClient,
  redirectUrl,
}: AuthProviderProps) {
  const [user, setUser] = React.useState<User | null>(null);
  const [session, setSession] = React.useState<Session | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // 초기 세션 로드
  React.useEffect(() => {
    const initSession = async () => {
      try {
        const { data: { session: currentSession } } = await supabaseClient.auth.getSession();

        if (currentSession) {
          setSession({
            accessToken: currentSession.access_token,
            refreshToken: currentSession.refresh_token,
            user: userFromSupabase(currentSession.user as unknown as Record<string, unknown>),
            expiresAt: currentSession.expires_at,
          });
          setUser(userFromSupabase(currentSession.user as unknown as Record<string, unknown>));
        }
      } catch (err) {
        console.error('Failed to initialize session:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initSession();

    // Auth 상태 변경 리스너
    const { data: { subscription } } = supabaseClient.auth.onAuthStateChange(
      async (event: AuthChangeEvent, currentSession) => {
        if (currentSession) {
          const userData = userFromSupabase(currentSession.user as unknown as Record<string, unknown>);
          setUser(userData);
          setSession({
            accessToken: currentSession.access_token,
            refreshToken: currentSession.refresh_token,
            user: userData,
            expiresAt: currentSession.expires_at,
          });
        } else {
          setUser(null);
          setSession(null);
        }
        setIsLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [supabaseClient]);

  const signIn = React.useCallback(
    async (email: string, password: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const { error: signInError } = await supabaseClient.auth.signInWithPassword({
          email,
          password,
        });

        if (signInError) {
          throw signInError;
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : '로그인에 실패했습니다';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [supabaseClient]
  );

  const signUp = React.useCallback(
    async (email: string, password: string, name?: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const { error: signUpError } = await supabaseClient.auth.signUp({
          email,
          password,
          options: {
            data: name ? { full_name: name } : undefined,
          },
        });

        if (signUpError) {
          throw signUpError;
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : '회원가입에 실패했습니다';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [supabaseClient]
  );

  const signOut = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { error: signOutError } = await supabaseClient.auth.signOut();

      if (signOutError) {
        throw signOutError;
      }

      setUser(null);
      setSession(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : '로그아웃에 실패했습니다';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [supabaseClient]);

  const signInWithOAuth = React.useCallback(
    async (provider: OAuthProvider) => {
      setIsLoading(true);
      setError(null);

      try {
        const { error: oauthError } = await supabaseClient.auth.signInWithOAuth({
          provider,
          options: {
            redirectTo: redirectUrl,
          },
        });

        if (oauthError) {
          throw oauthError;
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'OAuth 로그인에 실패했습니다';
        setError(message);
        setIsLoading(false);
        throw err;
      }
    },
    [supabaseClient, redirectUrl]
  );

  const refreshSession = React.useCallback(async () => {
    try {
      const { data: { session: refreshedSession }, error: refreshError } =
        await supabaseClient.auth.refreshSession();

      if (refreshError) {
        throw refreshError;
      }

      if (refreshedSession) {
        const userData = userFromSupabase(refreshedSession.user as unknown as Record<string, unknown>);
        setUser(userData);
        setSession({
          accessToken: refreshedSession.access_token,
          refreshToken: refreshedSession.refresh_token,
          user: userData,
          expiresAt: refreshedSession.expires_at,
        });
      }
    } catch (err) {
      console.error('Failed to refresh session:', err);
    }
  }, [supabaseClient]);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextType = {
    user,
    session,
    isLoading,
    isAuthenticated: !!user,
    error,
    signIn,
    signUp,
    signOut,
    signInWithOAuth,
    refreshSession,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
