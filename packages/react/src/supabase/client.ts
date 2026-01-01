import { createBrowserClient } from '@supabase/ssr';

export interface CreateBrowserClientOptions {
  supabaseUrl?: string;
  supabaseAnonKey?: string;
}

/**
 * Supabase 브라우저 클라이언트 생성
 *
 * @example
 * ```ts
 * // 환경 변수 사용 (기본)
 * const supabase = createClient();
 *
 * // 직접 URL/Key 전달
 * const supabase = createClient({
 *   supabaseUrl: 'https://xxx.supabase.co',
 *   supabaseAnonKey: 'your-anon-key'
 * });
 * ```
 */
export function createClient<Database = Record<string, unknown>>(
  options?: CreateBrowserClientOptions
) {
  const supabaseUrl = options?.supabaseUrl ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = options?.supabaseAnonKey ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Supabase URL and Anon Key are required. ' +
      'Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables, ' +
      'or pass them directly to createClient().'
    );
  }

  return createBrowserClient<Database>(supabaseUrl, supabaseAnonKey);
}
