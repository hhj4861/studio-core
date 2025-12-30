/**
 * @studio-core/react
 * React authentication hooks and providers for Studio Core
 */

// Types
export type {
  User,
  Session,
  AuthState,
  AuthError,
  OAuthProvider,
} from './types/auth';

export { userFromSupabase, isSessionExpired } from './types/auth';

// Context
export { AuthContext, useAuthContext, type AuthContextType } from './context/auth-context';

// Providers
export { AuthProvider, type AuthProviderProps } from './providers/auth-provider';

// Hooks
export { useAuth } from './hooks/use-auth';
export { useSession } from './hooks/use-session';
