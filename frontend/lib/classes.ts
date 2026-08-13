import { apiFetch } from '@/lib/api';

export interface ClassSummary {
  id: string;
  teacher_id: string | null;
  name: string;
  academic_period: string | null;
  description: string | null;
  is_active: boolean;
  archived_at: string | null;
  student_count: number;
  created_at: string;
  updated_at: string;
}

export interface ClassUserSummary {
  id: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
  student_code: string | null;
  is_active: boolean;
}

export interface ClassStudent {
  id: string;
  class_id: string;
  student_id: string;
  academic_period: string;
  student: ClassUserSummary | null;
  is_active: boolean;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClassTeacher {
  id: string;
  class_id: string;
  teacher_id: string;
  teacher: ClassUserSummary | null;
  is_active: boolean;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClassDetail extends ClassSummary {
  memberships: ClassStudent[];
  teachers: ClassTeacher[];
}

export interface ClassCreatePayload {
  name: string;
  academic_period?: string | null;
  description?: string | null;
  teacher_id?: string | null;
}

export interface ClassUpdatePayload {
  name?: string;
  description?: string | null;
}

export function listClasses(includeArchived = false) {
  const query = includeArchived ? '?include_archived=true' : '';
  return apiFetch<ClassSummary[]>(`/classes${query}`);
}

export function listMyClasses(includeArchived = false) {
  const query = includeArchived ? '?include_archived=true' : '';
  return apiFetch<ClassSummary[]>(`/me/classes${query}`);
}

export function getClass(classId: string) {
  return apiFetch<ClassDetail>(`/classes/${classId}`);
}

export function createClass(payload: ClassCreatePayload) {
  return apiFetch<ClassSummary>('/classes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateClass(classId: string, payload: ClassUpdatePayload) {
  return apiFetch<ClassSummary>(`/classes/${classId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function archiveClass(classId: string) {
  return apiFetch<ClassSummary>(`/classes/${classId}/archive`, {
    method: 'POST',
  });
}

export function addStudentsToClass(classId: string, studentIds: string[]) {
  return apiFetch<ClassStudent[]>(`/classes/${classId}/students`, {
    method: 'POST',
    body: JSON.stringify({ student_ids: studentIds }),
  });
}

export function addTeachersToClass(classId: string, teacherIds: string[]) {
  return apiFetch<ClassTeacher[]>(`/classes/${classId}/teachers`, {
    method: 'POST',
    body: JSON.stringify({ teacher_ids: teacherIds }),
  });
}

export function removeStudentFromClass(classId: string, studentId: string) {
  return apiFetch<void>(`/classes/${classId}/students/${studentId}`, {
    method: 'DELETE',
  });
}

export function removeTeacherFromClass(classId: string, teacherId: string) {
  return apiFetch<void>(`/classes/${classId}/teachers/${teacherId}`, {
    method: 'DELETE',
  });
}
