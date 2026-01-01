import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';

export interface CreateServerClientOptions {
  supabaseUrl?: string;
  supabaseAnonKey?: string;
}

interface CookieToSet {
  name: string;
  value: string;
  options: CookieOptions;
}

/**
 * Supabase 서버 클라이언트 생성 (Next.js Server Components / Route Handlers 용)
 *
 * @example
 * ```ts
 * // Server Component에서
 * const supabase = await createServerSupabaseClient();
 * const { data } = await supabase.from('users').select();
 *
 * // Route Handler에서
 * export async function GET() {
 *   const supabase = await createServerSupabaseClient();
 *   // ...
 * }
 * ```
 */
export async function createServerSupabaseClient<Database = Record<string, unknown>>(
  options?: CreateServerClientOptions
) {
  const supabaseUrl = options?.supabaseUrl ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = options?.supabaseAnonKey ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Supabase URL and Anon Key are required. ' +
      'Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables, ' +
      'or pass them directly to createServerSupabaseClient().'
    );
  }

  const cookieStore = await cookies();

  return createServerClient<Database>(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet: CookieToSet[]) {
        try {
          cookiesToSet.forEach(({ name, value, options: cookieOptions }) =>
            cookieStore.set(name, value, cookieOptions)
          );
        } catch {
          // Ignore - called from Server Component where cookies can't be set
        }
      },
    },
  });
}
