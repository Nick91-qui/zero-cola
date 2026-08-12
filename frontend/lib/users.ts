import { apiFetch } from '@/lib/api';

export interface UserSearchResult {
  id: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
  student_code: string | null;
  is_active: boolean;
}

export interface AdminUserCreatePayload {
  email: string;
  password: string;
  role: 'student' | 'teacher';
  student_code?: string | null;
}

export interface UserSearchParams {
  q: string;
  role?: 'student' | 'teacher' | 'admin';
  limit?: number;
}

export function searchUsers(params: UserSearchParams) {
  const search = new URLSearchParams();
  search.set('q', params.q);
  if (params.role) {
    search.set('role', params.role);
  }
  search.set('limit', String(params.limit ?? 10));
  return apiFetch<UserSearchResult[]>(`/users/search?${search.toString()}`);
}

export function createUser(payload: AdminUserCreatePayload) {
  return apiFetch<UserSearchResult>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
