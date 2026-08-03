import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import NewExamPage from '../app/exams/new/page';
import ExamDetailPage from '../app/exams/[examId]/page';
import * as examsLib from '@/lib/exams';
import * as classesLib from '@/lib/classes';
import * as skillsLib from '@/lib/skills';

const routerPush = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
  useParams: () => ({ examId: 'exam-1' }),
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

describe('Teacher exam frontend flow', () => {
  beforeEach(() => {
    routerPush.mockReset();
    vi.restoreAllMocks();
  });

  it('creates a workflow A exam with classes and question bank items', async () => {
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      {
        id: 'class-1',
        teacher_id: 'teacher-1',
        name: '2º Ano A',
        academic_period: '2026',
        description: 'Turma principal',
        is_active: true,
        archived_at: null,
        student_count: 28,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
    vi.spyOn(skillsLib, 'listSkills').mockResolvedValue([
      {
        id: 'skill-1',
        code: 'EF08MA01',
        description: 'Resolver equações',
        subject: 'Matemática',
        grade_level: '8',
        curriculum: 'BNCC',
      },
    ]);
    const createExamSpy = vi.spyOn(examsLib, 'createExam').mockResolvedValue({
      id: 'exam-1',
      title: 'Prova integradora',
      description: 'Avaliação criada pelo frontend',
      teacher_id: 'teacher-1',
      class_id: null,
      class_ids: ['class-1'],
      omr_template_id: null,
      total_questions: 1,
      total_time_seconds: 900,
      max_attempts: 2,
      randomization_enabled: true,
      max_score: '10.00',
      status: 'draft',
      is_active: true,
      deleted_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    render(<NewExamPage />);

    await screen.findByText('Criar avaliação online');

    fireEvent.change(screen.getByLabelText('Título'), {
      target: { value: 'Prova integradora' },
    });
    fireEvent.change(screen.getByLabelText('Descrição'), {
      target: { value: 'Avaliação criada pelo frontend' },
    });
    fireEvent.change(screen.getByLabelText('Duração total em segundos'), {
      target: { value: '900' },
    });
    fireEvent.change(screen.getByLabelText('Máximo de tentativas'), {
      target: { value: '2' },
    });
    fireEvent.change(screen.getByLabelText('Nota máxima'), {
      target: { value: '10.00' },
    });
    fireEvent.click(screen.getByLabelText('Randomizar ordem das questões por tentativa online'));
    fireEvent.click(screen.getByRole('checkbox', { name: /2º Ano A/ }));

    fireEvent.change(screen.getByPlaceholderText('Digite o enunciado da questão.'), {
      target: { value: 'Quanto é 2 + 2?' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa A'), {
      target: { value: '3' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa B'), {
      target: { value: '4' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa C'), {
      target: { value: '5' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa D'), {
      target: { value: '' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa E'), {
      target: { value: '' },
    });
    fireEvent.change(screen.getByLabelText('Gabarito correto'), {
      target: { value: 'B' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: /EF08MA01/ }));

    fireEvent.click(screen.getByRole('button', { name: 'Criar avaliação' }));

    await waitFor(() => {
      expect(createExamSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Prova integradora',
          class_ids: ['class-1'],
          total_questions: 1,
          total_time_seconds: 900,
          max_attempts: 2,
          randomization_enabled: true,
          questions: [
            expect.objectContaining({
              display_order: 1,
              question: expect.objectContaining({
                statement: 'Quanto é 2 + 2?',
                correct_answer: 'B',
                options: expect.objectContaining({
                  A: '3',
                  B: '4',
                  C: '5',
                }),
                skill_ids: ['skill-1'],
              }),
            }),
          ],
        }),
      );
      expect(routerPush).toHaveBeenCalledWith('/exams/exam-1');
    });
  }, 10000);

  it('shows exam status actions and publishes a draft exam', async () => {
    const now = new Date().toISOString();
    vi.spyOn(examsLib, 'getExam')
      .mockResolvedValueOnce({
        id: 'exam-1',
        title: 'Prova integradora',
        description: 'Avaliação criada pelo frontend',
        teacher_id: 'teacher-1',
        class_id: '2º Ano A',
        class_ids: ['class-1'],
        omr_template_id: null,
        total_questions: 1,
        total_time_seconds: 900,
        max_attempts: 2,
        randomization_enabled: true,
        max_score: '10.00',
        status: 'draft',
        is_active: true,
        deleted_at: null,
        created_at: now,
        updated_at: now,
        questions: [
          {
            id: 'question-1',
            statement: 'Quanto é 2 + 2?',
            type: 'multiple_choice',
            options: { A: '3', B: '4' },
            correct_answer: 'B',
            explanation: null,
            image_url: null,
            subject: null,
            difficulty: null,
            tags: null,
            skills: [],
            created_at: now,
            updated_at: now,
          },
        ],
        exam_questions: [
          {
            id: 'exam-question-1',
            exam_id: 'exam-1',
            question_id: 'question-1',
            display_order: 1,
            weight: '1.00',
            question: {
              id: 'question-1',
              statement: 'Quanto é 2 + 2?',
              type: 'multiple_choice',
              options: { A: '3', B: '4' },
              correct_answer: 'B',
              explanation: null,
              image_url: null,
              subject: null,
              difficulty: null,
              tags: null,
              skills: [],
              created_at: now,
              updated_at: now,
            },
            created_at: now,
            updated_at: now,
          },
        ],
      })
      .mockResolvedValueOnce({
        id: 'exam-1',
        title: 'Prova integradora',
        description: 'Avaliação criada pelo frontend',
        teacher_id: 'teacher-1',
        class_id: '2º Ano A',
        class_ids: ['class-1'],
        omr_template_id: null,
        total_questions: 1,
        total_time_seconds: 900,
        max_attempts: 2,
        randomization_enabled: true,
        max_score: '10.00',
        status: 'published',
        is_active: true,
        deleted_at: null,
        created_at: now,
        updated_at: now,
        questions: [],
        exam_questions: [],
      });
    vi.spyOn(examsLib, 'getExamStatistics').mockResolvedValue({
      exam_id: 'exam-1',
      exam_title: 'Prova integradora',
      total_attempts: 0,
      class_id: '2º Ano A',
      average_score: 0,
      max_score: 10,
      question_statistics: [],
    });
    const publishSpy = vi.spyOn(examsLib, 'publishExam').mockResolvedValue({
      id: 'exam-1',
      title: 'Prova integradora',
      description: 'Avaliação criada pelo frontend',
      teacher_id: 'teacher-1',
      class_id: '2º Ano A',
      class_ids: ['class-1'],
      omr_template_id: null,
      total_questions: 1,
      total_time_seconds: 900,
      max_attempts: 2,
      randomization_enabled: true,
      max_score: '10.00',
      status: 'published',
      is_active: true,
      deleted_at: null,
      created_at: now,
      updated_at: now,
    });

    render(<ExamDetailPage />);

    await screen.findByText('Prova integradora');
    expect(screen.getByText('draft')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Publicar' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Publicar' }));

    await waitFor(() => {
      expect(publishSpy).toHaveBeenCalledWith('exam-1');
      expect(screen.getByText('published')).toBeInTheDocument();
    });
  });
});
