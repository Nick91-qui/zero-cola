import { apiFetch } from '@/lib/api';

export interface Consent {
  id: string;
  user_id: string;
  consent_type: string;
  purpose: string;
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
  policy_version: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface MonitoringConsentPayload {
  purpose?: string;
  granted?: boolean;
  policy_version?: string | null;
  details?: Record<string, unknown> | null;
}

export function listMyConsents() {
  return apiFetch<Consent[]>('/me/consents');
}

export function listAdminConsents(params: {
  skip?: number;
  limit?: number;
  user_id?: string;
  consent_type?: string;
  granted?: boolean;
} = {}) {
  const search = new URLSearchParams();
  if (typeof params.skip === 'number') search.set('skip', String(params.skip));
  if (typeof params.limit === 'number') search.set('limit', String(params.limit));
  if (params.user_id) search.set('user_id', params.user_id);
  if (params.consent_type) search.set('consent_type', params.consent_type);
  if (typeof params.granted === 'boolean') search.set('granted', String(params.granted));
  const query = search.toString();
  return apiFetch<Consent[]>(`/admin/consents${query ? `?${query}` : ''}`);
}

export function upsertMonitoringConsent(payload: MonitoringConsentPayload = {}) {
  return apiFetch<Consent>('/consents/monitoring', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function revokeConsent(consentType: string) {
  return apiFetch<Consent>(`/consents/${consentType}`, {
    method: 'DELETE',
  });
}
