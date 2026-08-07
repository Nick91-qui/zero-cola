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

export interface SkillCreatePayload {
  code: string;
  description: string;
  subject?: string | null;
  grade_level?: string | null;
  curriculum?: string | null;
}

export function createSkill(payload: SkillCreatePayload) {
  return apiFetch<SkillSummary>('/skills', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
