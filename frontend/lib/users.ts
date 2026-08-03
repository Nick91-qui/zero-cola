import { apiFetch } from '@/lib/api';

export interface UserSearchResult {
  id: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
  student_code: string | null;
  is_active: boolean;
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
