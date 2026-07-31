import { apiFetch } from '@/lib/api';

export interface AttemptQuestion {
  question_number: number;
  question_id: string | null;
  statement: string | null;
  options: Record<string, unknown> | null;
  selected_option: string | null;
  answered_at: string | null;
}

export interface AttemptProgress {
  id: string;
  exam_id: string;
  student_id: string | null;
  student_code: string | null;
  omr_scan_id: string | null;
  attempt_number: number;
  source: string;
  status: string;
  total_questions: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  answers: AttemptQuestion[];
}

export interface AttemptSession {
  attempt: AttemptProgress;
  current_question: AttemptQuestion | null;
  total_questions: number;
}

export interface AttemptAnswer {
  id: string;
  attempt_id: string;
  question_number: number;
  question_id: string | null;
  selected_option: string | null;
  is_correct: boolean;
  answered_at: string | null;
}

export interface Grade {
  id: string;
  student_id: string;
  source_type: 'ONLINE' | 'OMR';
  source_id: string;
  score: string;
  teacher_id: string;
  created_at: string;
  updated_at: string;
}

export interface AttemptResult {
  attempt: {
    id: string;
    exam_id: string;
    student_id: string | null;
    student_code: string | null;
    omr_scan_id: string | null;
    attempt_number: number;
    source: string;
    status: string;
    total_questions: number;
    correct_answers: number;
    incorrect_answers: number;
    accuracy_percentage: string;
    raw_score: string;
    final_score: string;
    started_at: string | null;
    completed_at: string | null;
    created_at: string;
    updated_at: string;
    answers: AttemptAnswer[];
  };
  grade: Grade | null;
}

export interface StartAttemptPayload {
  exam_id: string;
}

export function startOnlineAttempt(examId: string) {
  return apiFetch<AttemptSession>('/attempts/start', {
    method: 'POST',
    body: JSON.stringify({ exam_id: examId } satisfies StartAttemptPayload),
  });
}

export function getAttemptSession(attemptId: string) {
  return apiFetch<AttemptSession>(`/attempts/${attemptId}/current`);
}

export function saveAttemptAnswer(
  attemptId: string,
  questionNumber: number,
  selectedOption: string | null,
) {
  return apiFetch<AttemptSession>(`/attempts/${attemptId}/answers/${questionNumber}`, {
    method: 'PUT',
    body: JSON.stringify({ selected_option: selectedOption }),
  });
}

export function nextAttemptQuestion(attemptId: string, questionNumber: number) {
  return apiFetch<AttemptSession>(`/attempts/${attemptId}/next/${questionNumber}`, {
    method: 'POST',
  });
}

export function previousAttemptQuestion(attemptId: string, questionNumber: number) {
  return apiFetch<AttemptSession>(`/attempts/${attemptId}/previous/${questionNumber}`, {
    method: 'POST',
  });
}

export function submitAttempt(attemptId: string) {
  return apiFetch<AttemptResult>(`/attempts/${attemptId}/submit`, {
    method: 'POST',
  });
}

export function getAttemptResult(attemptId: string) {
  return apiFetch<AttemptResult>(`/attempts/${attemptId}/result`);
}
