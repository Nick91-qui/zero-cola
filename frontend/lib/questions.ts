import { apiFetch } from '@/lib/api';
import type { Question } from '@/lib/exams';

export interface QuestionCreatePayload {
  statement: string;
  type?: string;
  options?: Record<string, string> | null;
  correct_answer: string | Record<string, string>;
  explanation?: string | null;
  image_url?: string | null;
  subject?: string | null;
  difficulty?: string | null;
  tags?: string[] | null;
  skill_ids?: string[] | null;
}

export interface QuestionUpdatePayload {
  statement?: string;
  type?: string;
  options?: Record<string, string> | null;
  correct_answer?: string | Record<string, string>;
  explanation?: string | null;
  image_url?: string | null;
  subject?: string | null;
  difficulty?: string | null;
  tags?: string[] | null;
  skill_ids?: string[] | null;
}

export interface QuestionListParams {
  q?: string;
  skill_id?: string;
  include_inactive?: boolean;
  skip?: number;
  limit?: number;
}

export function listQuestions(params: QuestionListParams = {}) {
  const search = new URLSearchParams();
  if (params.q) search.set('q', params.q);
  if (params.skill_id) search.set('skill_id', params.skill_id);
  if (params.include_inactive) search.set('include_inactive', 'true');
  if (typeof params.skip === 'number') search.set('skip', String(params.skip));
  if (typeof params.limit === 'number') search.set('limit', String(params.limit));
  const query = search.toString();
  return apiFetch<Question[]>(`/questions${query ? `?${query}` : ''}`);
}

export function getQuestion(questionId: string) {
  return apiFetch<Question>(`/questions/${questionId}`);
}

export function createQuestion(payload: QuestionCreatePayload) {
  return apiFetch<Question>('/questions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateQuestion(questionId: string, payload: QuestionUpdatePayload) {
  return apiFetch<Question>(`/questions/${questionId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function deactivateQuestion(questionId: string) {
  return apiFetch<Question>(`/questions/${questionId}`, {
    method: 'DELETE',
  });
}
