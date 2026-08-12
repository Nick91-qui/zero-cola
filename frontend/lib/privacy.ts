import { apiFetch } from '@/lib/api';

export interface PrivacyPolicy {
  title: string;
  version: string;
  summary: string;
  monitoring_events: string[];
  data_categories: string[];
  updated_at: string;
}

export interface DataExportResult {
  data: Record<string, unknown>;
}

export function getPrivacyPolicy() {
  return apiFetch<PrivacyPolicy>('/privacy-policy');
}

export function exportMyData() {
  return apiFetch<DataExportResult>('/me/data-export');
}

export function requestAnonymization() {
  return apiFetch<{ status: string; user_id: string }>('/me/request-anonymization', {
    method: 'POST',
  });
}
