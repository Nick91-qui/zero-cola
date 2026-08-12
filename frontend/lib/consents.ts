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
