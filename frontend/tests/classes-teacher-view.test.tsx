import type { ReactNode } from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import ClassDetailPage from '../app/classes/[classId]/page';
import * as classesLib from '@/lib/classes';

vi.mock('next/navigation', () => ({
  useParams: () => ({ classId: 'class-1' }),
}));

vi.mock('@/app/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('@/app/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { email: 'teacher@cola-zero.edu', role: 'teacher' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

describe('Teacher class detail view', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(classesLib, 'getClass').mockResolvedValue({
      id: 'class-1',
      teacher_id: 'teacher-1',
      name: '2º Ano A',
      academic_period: '2026',
      description: 'Turma principal',
      is_active: true,
      archived_at: null,
      student_count: 2,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      memberships: [
        {
          id: 'membership-1',
          class_id: 'class-1',
          student_id: 'student-1',
          academic_period: '2026',
          student: {
            id: 'student-1',
            email: 'student@cola-zero.edu',
            role: 'student',
            student_code: '12345',
            is_active: true,
          },
          is_active: true,
          archived_at: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      teachers: [
        {
          id: 'teacher-membership-1',
          class_id: 'class-1',
          teacher_id: 'teacher-1',
          teacher: {
            id: 'teacher-1',
            email: 'teacher@cola-zero.edu',
            role: 'teacher',
            student_code: null,
            is_active: true,
          },
          is_active: true,
          archived_at: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    });
  });

  it('hides administrative membership details from teachers', async () => {
    render(<ClassDetailPage />);

    expect(await screen.findByText('2º Ano A')).toBeInTheDocument();
    expect(screen.getByText('student@cola-zero.edu')).toBeInTheDocument();
    expect(screen.queryByText('student@cola-zero.edu (12345)')).not.toBeInTheDocument();
    expect(screen.queryByText('Professores ativos')).not.toBeInTheDocument();
    expect(screen.queryByText('Transferir estudante')).not.toBeInTheDocument();
    expect(screen.queryByText('Vincular professor(es)')).not.toBeInTheDocument();
    expect(screen.getByText('Alunos ativos')).toBeInTheDocument();
  });
});
