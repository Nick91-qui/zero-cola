import { apiFetch } from '@/lib/api';

export interface ClassSummary {
  id: string;
  teacher_id: string;
  name: string;
  academic_period: string | null;
  description: string | null;
  is_active: boolean;
  archived_at: string | null;
  student_count: number;
  created_at: string;
  updated_at: string;
}

export function listClasses(includeArchived = false) {
  const query = includeArchived ? '?include_archived=true' : '';
  return apiFetch<ClassSummary[]>(`/classes${query}`);
}
