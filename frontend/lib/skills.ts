import { apiFetch } from '@/lib/api';

export interface SkillSummary {
  id: string;
  code: string;
  description: string;
  subject: string | null;
  grade_level: string | null;
  curriculum: string | null;
}

export function listSkills() {
  return apiFetch<SkillSummary[]>('/skills');
}
