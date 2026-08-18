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

export interface PrivacyRequest {
  id: string;
  user_id: string;
  requested_by_id: string | null;
  request_type: 'anonymization';
  status: 'pending' | 'approved' | 'rejected';
  reason: string | null;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  resolution_note: string | null;
  created_at: string;
  updated_at: string;
  user: {
    id: string;
    email: string;
    role: 'student' | 'teacher' | 'admin';
    student_code: string | null;
    is_active: boolean;
  };
  reviewed_by: {
    id: string;
    email: string;
    role: 'student' | 'teacher' | 'admin';
    student_code: string | null;
    is_active: boolean;
  } | null;
}

export function getPrivacyPolicy() {
  return apiFetch<PrivacyPolicy>('/privacy-policy');
}

export function exportMyData() {
  return apiFetch<DataExportResult>('/me/data-export');
}

export function requestAnonymization() {
  return apiFetch<PrivacyRequest>('/me/request-anonymization', {
    method: 'POST',
  });
}

export function getMyPrivacyRequest() {
  return apiFetch<PrivacyRequest | null>('/me/privacy-request');
}

export function listPrivacyRequests() {
  return apiFetch<PrivacyRequest[]>('/privacy-requests');
}

export function approvePrivacyRequest(requestId: string) {
  return apiFetch<PrivacyRequest>(`/privacy-requests/${requestId}/approve`, {
    method: 'POST',
  });
}

export function rejectPrivacyRequest(requestId: string) {
  return apiFetch<PrivacyRequest>(`/privacy-requests/${requestId}/reject`, {
    method: 'POST',
  });
}
