import { apiFetch, apiFetchBlob } from '@/lib/api';

export interface Skill {
  id: string;
  code: string;
  description: string;
  subject: string | null;
  grade_level: string | null;
  curriculum: string | null;
}

export type QuestionOptions = Record<string, string>;

export interface Question {
  id: string;
  statement: string;
  type: string;
  options: QuestionOptions | null;
  correct_answer: string | QuestionOptions;
  explanation: string | null;
  image_url: string | null;
  subject: string | null;
  difficulty: string | null;
  tags: string[] | null;
  parent_id?: string | null;
  version?: number;
  is_active?: boolean;
  created_by?: string;
  skills: Skill[];
  created_at: string;
  updated_at: string;
}

export interface ExamQuestionInput {
  display_order: number;
  weight?: string | number;
  question_id?: string;
  question?: {
    statement: string;
    type?: string;
    options?: QuestionOptions | null;
    correct_answer: string | QuestionOptions;
    explanation?: string | null;
    image_url?: string | null;
    subject?: string | null;
    difficulty?: string | null;
    tags?: string[] | null;
    skill_ids?: string[] | null;
  };
}

export interface ExamCreatePayload {
  title: string;
  description?: string | null;
  class_id?: string | null;
  class_ids?: string[];
  omr_template_id?: string | null;
  total_questions?: number;
  total_time_seconds?: number | null;
  max_attempts?: number;
  randomization_enabled?: boolean;
  max_score?: string | number;
  correct_answers?: Record<string, string>;
  layout_version?: string;
  questions?: ExamQuestionInput[];
}

export interface Exam {
  id: string;
  title: string;
  description: string | null;
  teacher_id: string;
  class_id: string | null;
  class_ids?: string[];
  omr_template_id: string | null;
  total_questions: number;
  total_time_seconds: number | null;
  max_attempts: number;
  randomization_enabled: boolean;
  max_score: string | number;
  status?: string;
  is_active: boolean;
  deleted_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExamSummary extends Exam {
  status: string;
  total_time_seconds: number | null;
  max_attempts: number;
  randomization_enabled: boolean;
}

export interface ExamQuestionDetail {
  id: string;
  exam_id: string;
  question_id: string;
  display_order: number;
  weight: string | number;
  question: Question;
  created_at: string;
  updated_at: string;
}

export interface ExamDetail extends Exam {
  questions: Question[];
  exam_questions: ExamQuestionDetail[];
}

export interface QuestionStatistic {
  question_number: number;
  statement: string | null;
  correct_option: string | null;
  skills: Skill[];
  total_responses: number;
  correct_count: number;
  incorrect_count: number;
  accuracy_percentage: number;
  error_percentage: number;
}

export interface ExamStatistics {
  exam_id: string;
  exam_title: string;
  total_attempts: number;
  class_id: string | null;
  average_score: number;
  max_score: number;
  question_statistics: QuestionStatistic[];
}

export function listExams(classId?: string) {
  const query = classId ? `?class_id=${encodeURIComponent(classId)}` : '';
  return apiFetch<Exam[]>(`/exams${query}`);
}

export function getExam(examId: string) {
  return apiFetch<ExamDetail>(`/exams/${examId}`);
}

export function getExamSummary(examId: string) {
  return apiFetch<ExamSummary>(`/exams/${examId}`);
}

export function createExam(payload: ExamCreatePayload) {
  return apiFetch<Exam>(`/exams`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function publishExam(examId: string) {
  return apiFetch<Exam>(`/exams/${examId}/publish`, {
    method: 'POST',
  });
}

export function returnExamToDraft(examId: string) {
  return apiFetch<Exam>(`/exams/${examId}/draft`, {
    method: 'POST',
  });
}

export function archiveExam(examId: string) {
  return apiFetch<Exam>(`/exams/${examId}/archive`, {
    method: 'POST',
  });
}

export function getExamStatistics(examId: string) {
  return apiFetch<ExamStatistics>(`/exams/${examId}/statistics`);
}

export function exportExamPdf(examId: string) {
  return apiFetchBlob(`/exams/${examId}/export/pdf`);
}

export function exportExamXlsx(examId: string) {
  return apiFetchBlob(`/exams/${examId}/export/xlsx`);
}

export function deleteExam(examId: string) {
  return apiFetch<void>(`/exams/${examId}`, {
    method: 'DELETE',
  });
}
