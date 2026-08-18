import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ClassesPage from '../app/classes/page';
import ClassDetailPage from '../app/classes/[classId]/page';
import * as classesLib from '@/lib/classes';
import * as usersLib from '@/lib/users';

const routerPush = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
  useParams: () => ({ classId: 'class-1' }),
}));

vi.mock('@/app/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('@/app/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { email: 'admin@cola-zero.edu', role: 'admin' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

describe('Classes frontend flow', () => {
  beforeEach(() => {
    routerPush.mockReset();
    vi.restoreAllMocks();
  });

  it('lists classes and creates a new class', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      {
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 24,
        created_at: now,
        updated_at: now,
      },
    ]);
    const createSpy = vi.spyOn(classesLib, 'createClass').mockResolvedValue({
      id: 'class-2',
      teacher_id: 'teacher-1',
      name: '3º Ano B',
      academic_period: '2026',
      description: 'Nova turma',
      is_active: true,
      archived_at: null,
      student_count: 0,
      created_at: now,
      updated_at: now,
    });

    render(<ClassesPage />);

    expect(await screen.findByText('2º Ano A')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Nome'), {
      target: { value: '3º Ano B' },
    });
    fireEvent.change(screen.getByLabelText('Período letivo'), {
      target: { value: '2026' },
    });
    fireEvent.change(screen.getByLabelText('Descrição'), {
      target: { value: 'Nova turma' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Criar turma' }));

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith({
        name: '3º Ano B',
        academic_period: '2026',
        description: 'Nova turma',
      });
      expect(screen.getByText('3º Ano B')).toBeInTheDocument();
    });
  });

  it('renders the class detail with teachers and students and archives the class', async () => {
    const now = new Date().toISOString();
    const archivedNow = new Date(Date.now() + 1000).toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      {
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 2,
        created_at: now,
        updated_at: now,
      },
      {
        id: 'class-2',
        teacher_id: 'teacher-2',
        name: '3º Ano B',
        academic_period: '2026',
        description: 'Destino',
        is_active: true,
        archived_at: null,
        student_count: 0,
        created_at: now,
        updated_at: now,
      },
    ]);
    vi.spyOn(classesLib, 'getClass')
      .mockResolvedValueOnce({
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 2,
        created_at: now,
        updated_at: now,
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
            created_at: now,
            updated_at: now,
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
            created_at: now,
            updated_at: now,
          },
        ],
      })
      .mockResolvedValueOnce({
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: false,
        archived_at: archivedNow,
        student_count: 2,
        created_at: now,
        updated_at: archivedNow,
        memberships: [],
        teachers: [],
      })
      .mockResolvedValueOnce({
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 2,
        created_at: now,
        updated_at: now,
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
            created_at: now,
            updated_at: now,
          },
          {
            id: 'membership-2',
            class_id: 'class-1',
            student_id: 'student-2',
            academic_period: '2026',
            student: {
              id: 'student-2',
              email: 'student2@cola-zero.edu',
              role: 'student',
              student_code: '54321',
              is_active: true,
            },
            is_active: true,
            archived_at: null,
            created_at: now,
            updated_at: now,
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
            created_at: now,
            updated_at: now,
          },
          {
            id: 'teacher-membership-2',
            class_id: 'class-1',
            teacher_id: 'teacher-2',
            teacher: {
              id: 'teacher-2',
              email: 'co-teacher@cola-zero.edu',
              role: 'teacher',
              student_code: null,
              is_active: true,
            },
            is_active: true,
            archived_at: null,
            created_at: now,
            updated_at: now,
          },
        ],
      })
      .mockResolvedValueOnce({
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 2,
        created_at: now,
        updated_at: now,
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
            created_at: now,
            updated_at: now,
          },
          {
            id: 'membership-2',
            class_id: 'class-1',
            student_id: 'student-2',
            academic_period: '2026',
            student: {
              id: 'student-2',
              email: 'student2@cola-zero.edu',
              role: 'student',
              student_code: '54321',
              is_active: true,
            },
            is_active: true,
            archived_at: null,
            created_at: now,
            updated_at: now,
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
            created_at: now,
            updated_at: now,
          },
          {
            id: 'teacher-membership-2',
            class_id: 'class-1',
            teacher_id: 'teacher-2',
            teacher: {
              id: 'teacher-2',
              email: 'co-teacher@cola-zero.edu',
              role: 'teacher',
              student_code: null,
              is_active: true,
            },
            is_active: true,
            archived_at: null,
            created_at: now,
            updated_at: now,
          },
        ],
      });
    const archiveSpy = vi.spyOn(classesLib, 'archiveClass').mockResolvedValue({
      id: 'class-1',
      teacher_id: 'teacher-1',
      name: '2º Ano A',
      academic_period: '2026',
      description: 'Turma principal',
      is_active: false,
      archived_at: archivedNow,
      student_count: 2,
      created_at: now,
      updated_at: archivedNow,
    });

    render(<ClassDetailPage />);

    expect(await screen.findByText('2º Ano A')).toBeInTheDocument();
    expect(screen.getByText('student@cola-zero.edu (12345)', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByText('teacher@cola-zero.edu', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByText('Transferir estudante')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Arquivar turma' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Confirmar arquivamento' }));

    await waitFor(() => {
      expect(archiveSpy).toHaveBeenCalledWith('class-1');
      expect(screen.getAllByText('Arquivada')).toHaveLength(2);
    });
  });

  it('links and unlinks teachers and students by id', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      {
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 1,
        created_at: now,
        updated_at: now,
      },
    ]);
    let classSnapshot = {
      id: 'class-1',
      teacher_id: 'teacher-1',
      name: '2º Ano A',
      academic_period: '2026',
      description: 'Turma principal',
      is_active: true,
      archived_at: null,
      student_count: 1,
      created_at: now,
      updated_at: now,
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
          created_at: now,
          updated_at: now,
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
          created_at: now,
          updated_at: now,
        },
      ],
    };

    vi.spyOn(classesLib, 'getClass').mockImplementation(async () => classSnapshot);
    vi.spyOn(usersLib, 'searchUsers').mockImplementation(async ({ q, role }) => {
      const normalized = q.toLowerCase();
      if (role === 'teacher' && normalized.includes('teacher') && normalized.includes('2')) {
        return [
          {
            id: 'teacher-2',
            email: 'co-teacher@cola-zero.edu',
            role: 'teacher',
            student_code: null,
            is_active: true,
          },
        ];
      }
      return [];
    });
    const addTeachersSpy = vi.spyOn(classesLib, 'addTeachersToClass').mockImplementation(async () => {
      classSnapshot = {
        ...classSnapshot,
        teachers: [
          ...classSnapshot.teachers,
          {
            id: 'teacher-membership-2',
            class_id: 'class-1',
            teacher_id: 'teacher-2',
            teacher: {
              id: 'teacher-2',
              email: 'co-teacher@cola-zero.edu',
              role: 'teacher',
              student_code: null,
              is_active: true,
            },
            is_active: true,
            archived_at: null,
            created_at: now,
            updated_at: now,
          },
        ],
      };
      return [];
    });
    const removeStudentSpy = vi.spyOn(classesLib, 'removeStudentFromClass').mockImplementation(
      async () => {
        classSnapshot = {
          ...classSnapshot,
          memberships: classSnapshot.memberships.filter(
            (membership) => membership.student_id !== 'student-1',
          ),
          student_count: 1,
        };
      },
    );
    const removeTeacherSpy = vi.spyOn(classesLib, 'removeTeacherFromClass').mockImplementation(
      async () => {
        classSnapshot = {
          ...classSnapshot,
          teachers: classSnapshot.teachers.filter((membership) => membership.teacher_id !== 'teacher-1'),
        };
      },
    );

    render(<ClassDetailPage />);

    expect(
      await screen.findByText('student@cola-zero.edu (12345)', { selector: 'p' }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getAllByRole('searchbox')[0], {
      target: { value: 'teacher-2' },
    });

    expect(await screen.findByText('co-teacher@cola-zero.edu')).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole('button', { name: 'Adicionar' })[0]);

    fireEvent.click(screen.getByRole('button', { name: 'Vincular professores' }));

    await waitFor(() => {
      expect(addTeachersSpy).toHaveBeenCalledWith('class-1', ['teacher-2']);
    });

    fireEvent.click(screen.getAllByRole('button', { name: 'Remover vínculo do estudante' })[0]);

    await waitFor(() => {
      expect(removeStudentSpy).toHaveBeenCalledWith('class-1', 'student-1');
    });

    fireEvent.click(screen.getAllByRole('button', { name: 'Remover vínculo do professor' })[0]);

    await waitFor(() => {
      expect(removeTeacherSpy).toHaveBeenCalledWith('class-1', 'teacher-1');
    });
  });

  it('transfers a student to another class and refreshes the detail', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      {
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 1,
        created_at: now,
        updated_at: now,
      },
      {
        id: 'class-2',
        teacher_id: 'teacher-2',
        name: '3º Ano B',
        academic_period: '2026',
        description: 'Destino',
        is_active: true,
        archived_at: null,
        student_count: 0,
        created_at: now,
        updated_at: now,
      },
    ]);
    vi.spyOn(classesLib, 'getClass')
      .mockResolvedValueOnce({
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 1,
        created_at: now,
        updated_at: now,
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
            created_at: now,
            updated_at: now,
          },
        ],
        teachers: [],
      })
      .mockResolvedValueOnce({
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 1,
        created_at: now,
        updated_at: now,
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
            is_active: false,
            archived_at: now,
            created_at: now,
            updated_at: now,
          },
        ],
        teachers: [],
      });
    const transferSpy = vi.spyOn(classesLib, 'transferStudentBetweenClasses').mockResolvedValue({
      student_id: 'student-1',
      source_class_id: 'class-1',
      target_class_id: 'class-2',
      source_membership: {
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
        is_active: false,
        archived_at: now,
        created_at: now,
        updated_at: now,
      },
      target_membership: {
        id: 'membership-2',
        class_id: 'class-2',
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
        created_at: now,
        updated_at: now,
      },
    });

    render(<ClassDetailPage />);

    expect(await screen.findByText('Transferir estudante')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Estudante'), {
      target: { value: 'student-1' },
    });
    fireEvent.change(screen.getByLabelText('Turma destino'), {
      target: { value: 'class-2' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Transferir aluno' }));

    await waitFor(() => {
      expect(transferSpy).toHaveBeenCalledWith('class-1', 'student-1', 'class-2');
      expect(screen.getByText('Aluno transferido com sucesso.')).toBeInTheDocument();
    });
  });
});
