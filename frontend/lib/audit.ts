import { apiFetch } from '@/lib/api';

export interface AuditLog {
  id: string;
  user_id: string | null;
  event_type: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  updated_at: string;
}

export interface SecurityEvent {
  id: string;
  attempt_id: string;
  event_type: string;
  details: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export function listAuditLogs(params: {
  skip?: number;
  limit?: number;
  user_id?: string;
  event_type?: string;
  resource_type?: string;
} = {}) {
  const search = new URLSearchParams();
  if (typeof params.skip === 'number') search.set('skip', String(params.skip));
  if (typeof params.limit === 'number') search.set('limit', String(params.limit));
  if (params.user_id) search.set('user_id', params.user_id);
  if (params.event_type) search.set('event_type', params.event_type);
  if (params.resource_type) search.set('resource_type', params.resource_type);
  const query = search.toString();
  return apiFetch<AuditLog[]>(`/audit-logs${query ? `?${query}` : ''}`);
}

export function listSecurityEvents(attemptId: string) {
  return apiFetch<SecurityEvent[]>(`/attempts/${attemptId}/security-events`);
}
