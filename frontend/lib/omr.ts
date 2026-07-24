import { apiFetch, apiFetchBlob } from '@/lib/api';

export type OMRScanStatus = 'processing' | 'success' | 'review_needed' | 'failed';

export interface OMRTemplate {
  id: string;
  exam_id: string | null;
  layout_version: string;
  total_questions: number;
  options_per_question: number;
  correct_answers: Record<string, string> | null;
  created_at: string;
  updated_at: string;
}

export interface OMRScan {
  id: string;
  omr_template_id: string;
  student_code: string | null;
  student_id: string | null;
  status: OMRScanStatus;
  image_url: string;
  detected_answers: Record<string, string | null> | null;
  raw_confidence: Record<string, unknown> | null;
  score: string | number | null;
  error_message: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Grade {
  id: string;
  student_id: string;
  source_type: string;
  source_id: string;
  score: string | number;
  teacher_id: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTemplateInput {
  layout_version: string;
  total_questions: number;
  options_per_question?: number;
  correct_answers: Record<string, string>;
  exam_id?: string | null;
}

export function listTemplates() {
  return apiFetch<OMRTemplate[]>('/omr/templates');
}

export function getTemplate(templateId: string) {
  return apiFetch<OMRTemplate>(`/omr/templates/${templateId}`);
}

export function createTemplate(input: CreateTemplateInput) {
  return apiFetch<OMRTemplate>('/omr/templates', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export function downloadTemplatePdf(templateId: string, studentCode: string) {
  const query = studentCode ? `?student_code=${encodeURIComponent(studentCode)}` : '';
  return apiFetchBlob(`/omr/templates/${templateId}/pdf${query}`);
}

export function downloadTemplatePreview(templateId: string, studentCode: string) {
  const query = studentCode ? `?student_code=${encodeURIComponent(studentCode)}` : '';
  return apiFetchBlob(`/omr/templates/${templateId}/preview.png${query}`);
}

export async function uploadScan(templateId: string, file: File) {
  const form = new FormData();
  form.append('omr_template_id', templateId);
  form.append('file', file);
  return apiFetch<OMRScan>('/omr/scans/upload', {
    method: 'POST',
    body: form,
  });
}

export function getScan(scanId: string) {
  return apiFetch<OMRScan>(`/omr/scans/${scanId}`);
}

export function updateScan(
  scanId: string,
  payload: { student_code?: string; detected_answers?: Record<string, string | null> },
) {
  return apiFetch<OMRScan>(`/omr/scans/${scanId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function confirmScan(scanId: string) {
  return apiFetch<Grade>(`/omr/scans/${scanId}/confirm`, {
    method: 'POST',
  });
}
