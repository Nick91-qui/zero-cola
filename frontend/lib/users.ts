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
  q?: string;
  role?: 'student' | 'teacher' | 'admin';
  limit?: number;
  skip?: number;
  include_inactive?: boolean;
}

export interface UserListParams {
  q?: string;
  role?: 'student' | 'teacher' | 'admin';
  limit?: number;
  skip?: number;
  include_inactive?: boolean;
}

export function searchUsers(params: UserSearchParams) {
  const search = new URLSearchParams();
  if (params.q) {
    search.set('q', params.q);
  }
  if (params.role) {
    search.set('role', params.role);
  }
  search.set('limit', String(params.limit ?? 10));
  if (params.skip) {
    search.set('skip', String(params.skip));
  }
  if (params.include_inactive) {
    search.set('include_inactive', 'true');
  }
  return apiFetch<UserSearchResult[]>(`/users/search?${search.toString()}`);
}

export function listUsers(params: UserListParams = {}) {
  const search = new URLSearchParams();
  if (params.q) {
    search.set('q', params.q);
  }
  if (params.role) {
    search.set('role', params.role);
  }
  search.set('limit', String(params.limit ?? 100));
  if (params.skip) {
    search.set('skip', String(params.skip));
  }
  if (params.include_inactive !== undefined) {
    search.set('include_inactive', params.include_inactive ? 'true' : 'false');
  }
  const query = search.toString();
  return apiFetch<UserSearchResult[]>(`/users${query ? `?${query}` : ''}`);
}

export function createUser(payload: AdminUserCreatePayload) {
  return apiFetch<UserSearchResult>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function archiveUser(userId: string) {
  return apiFetch<UserSearchResult>(`/users/${userId}/archive`, {
    method: 'POST',
  });
}

export function deleteUser(userId: string) {
  return apiFetch<UserSearchResult>(`/users/${userId}`, {
    method: 'DELETE',
  });
}
