'use client';

import { useAuthContext } from '../context/auth-context';
import { isSessionExpired } from '../types/auth';

/**
 * 세션 정보에 접근하는 훅
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { session, isExpired, refresh } = useSession();
 *
 *   if (isExpired) {
 *     refresh();
 *   }
 *
 *   return <div>Token: {session?.accessToken}</div>;
 * }
 * ```
 */
export function useSession() {
  const { session, refreshSession } = useAuthContext();

  return {
    session,
    isExpired: session ? isSessionExpired(session) : false,
    refresh: refreshSession,
    accessToken: session?.accessToken ?? null,
    refreshToken: session?.refreshToken ?? null,
  };
}
