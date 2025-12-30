'use client';

import { useAuthContext } from '../context/auth-context';

/**
 * 인증 상태와 메서드에 접근하는 훅
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { user, isAuthenticated, signIn, signOut } = useAuth();
 *
 *   if (!isAuthenticated) {
 *     return <LoginForm onSubmit={signIn} />;
 *   }
 *
 *   return (
 *     <div>
 *       Welcome, {user?.name}!
 *       <button onClick={signOut}>Logout</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useAuth() {
  return useAuthContext();
}
