import { apiFetch, apiFetchBlob } from '@/lib/api';

export interface Skill {
  id: string;
  code: string;
  description: string;
  subject: string | null;
  grade_level: string | null;
  curriculum: string | null;
}

export interface Question {
  id: string;
  question_number: int;
  statement: string | null;
  correct_option: string | null;
  weight: string | number;
  skills: Skill[];
}

export interface Exam {
  id: string;
  title: string;
  description: string | null;
  teacher_id: string;
  class_id: string | null;
  omr_template_id: string | null;
  total_questions: number;
  max_score: string | number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
  return apiFetch<Exam & { questions: Question[] }>(`/exams/${examId}`);
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
