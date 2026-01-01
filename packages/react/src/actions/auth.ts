'use server';

import { redirect } from 'next/navigation';
import { createServerSupabaseClient } from '../supabase/server';

export interface SignUpData {
  email: string;
  password: string;
  fullName?: string;
  metadata?: Record<string, unknown>;
}

export interface SignInData {
  email: string;
  password: string;
}

export interface AuthActionResult {
  error?: string;
  success?: boolean;
}

/**
 * 이메일/비밀번호로 회원가입
 *
 * @example
 * ```tsx
 * // Form Action으로 사용
 * <form action={signUp}>
 *   <input name="email" type="email" />
 *   <input name="password" type="password" />
 *   <input name="fullName" type="text" />
 *   <button type="submit">가입</button>
 * </form>
 *
 * // 또는 직접 호출
 * const formData = new FormData();
 * formData.set('email', 'user@example.com');
 * formData.set('password', 'password123');
 * await signUp(formData);
 * ```
 */
export async function signUp(formData: FormData): Promise<AuthActionResult> {
  const supabase = await createServerSupabaseClient();

  const email = formData.get('email') as string;
  const password = formData.get('password') as string;
  const fullName = formData.get('fullName') as string | null;

  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: fullName ? { full_name: fullName } : undefined,
    },
  });

  if (error) {
    return { error: error.message };
  }

  redirect('/dashboard');
}

/**
 * 이메일/비밀번호로 로그인
 *
 * @example
 * ```tsx
 * <form action={signIn}>
 *   <input name="email" type="email" />
 *   <input name="password" type="password" />
 *   <button type="submit">로그인</button>
 * </form>
 * ```
 */
export async function signIn(formData: FormData): Promise<AuthActionResult> {
  const supabase = await createServerSupabaseClient();

  const email = formData.get('email') as string;
  const password = formData.get('password') as string;

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return { error: error.message };
  }

  redirect('/dashboard');
}

/**
 * 로그아웃
 *
 * @example
 * ```tsx
 * <form action={signOut}>
 *   <button type="submit">로그아웃</button>
 * </form>
 * ```
 */
export async function signOut(): Promise<void> {
  const supabase = await createServerSupabaseClient();
  await supabase.auth.signOut();
  redirect('/');
}

/**
 * 현재 로그인된 사용자 정보 조회 (Server Component용)
 *
 * @example
 * ```tsx
 * // Server Component에서
 * export default async function ProfilePage() {
 *   const user = await getUser();
 *   if (!user) redirect('/login');
 *   return <div>Hello, {user.email}</div>;
 * }
 * ```
 */
export async function getUser() {
  const supabase = await createServerSupabaseClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return user;
}

/**
 * 현재 세션 정보 조회 (Server Component용)
 */
export async function getSession() {
  const supabase = await createServerSupabaseClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session;
}
