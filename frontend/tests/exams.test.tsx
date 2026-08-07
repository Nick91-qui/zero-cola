import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { vi } from 'vitest';
import ExamsListPage from '../app/exams/page';
import NewExamPage from '../app/exams/new/page';
import ExamDetailPage from '../app/exams/[examId]/page';
import * as examsLib from '@/lib/exams';
import * as classesLib from '@/lib/classes';
import * as questionsLib from '@/lib/questions';

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

  const classroom = {
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
  };

  it('creates a workflow A exam with classes and question bank items', async () => {
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      classroom,
    ]);
    vi.spyOn(questionsLib, 'listQuestions').mockResolvedValue([
      {
        id: 'question-1',
        statement: 'Quanto é 2 + 2?',
        type: 'multiple_choice',
        options: { A: '3', B: '4', C: '5' },
        correct_answer: 'B',
        explanation: null,
        image_url: null,
        subject: 'Matemática',
        difficulty: 'easy',
        tags: ['aritmética'],
        parent_id: null,
        version: 1,
        is_active: true,
        created_by: 'teacher-1',
        skills: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
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
    await screen.findByText('Quanto é 2 + 2?');
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar' }));

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
              question_id: 'question-1',
            }),
          ],
        }),
      );
      expect(routerPush).toHaveBeenCalledWith('/exams/exam-1');
    });
  }, 10000);

  it('shows exam status actions and publishes a draft exam', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([classroom]);
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

  it('downloads personalized omr sheets for the exam', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([classroom]);
    const downloadSpy = vi.spyOn(examsLib, 'exportExamOmrPackage').mockResolvedValue(
      new Blob(['zip-bytes'], { type: 'application/zip' }),
    );
    const createObjectUrlSpy = vi.fn(() => 'blob:omr-package');
    const revokeObjectUrlSpy = vi.fn();
    Object.defineProperty(window.URL, 'createObjectURL', {
      value: createObjectUrlSpy,
      configurable: true,
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      value: revokeObjectUrlSpy,
      configurable: true,
    });

    vi.spyOn(examsLib, 'getExam')
      .mockResolvedValueOnce({
        id: 'exam-1',
        title: 'Prova integradora',
        description: 'Avaliação criada pelo frontend',
        teacher_id: 'teacher-1',
        class_id: '2º Ano A',
        class_ids: ['class-1'],
        omr_template_id: null,
        total_questions: 2,
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
      })
      .mockResolvedValueOnce({
        id: 'exam-1',
        title: 'Prova integradora',
        description: 'Avaliação criada pelo frontend',
        teacher_id: 'teacher-1',
        class_id: '2º Ano A',
        class_ids: ['class-1'],
        omr_template_id: null,
        total_questions: 2,
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

    render(<ExamDetailPage />);

    await screen.findByText('Prova integradora');
    fireEvent.click(screen.getByRole('button', { name: 'Baixar folhas OMR' }));

    await waitFor(() => {
      expect(downloadSpy).toHaveBeenCalledWith('exam-1');
      expect(createObjectUrlSpy).toHaveBeenCalled();
      expect(revokeObjectUrlSpy).toHaveBeenCalled();
    });
  });

  it('downloads a preview without exposing the answer key', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([classroom]);
    const downloadSpy = vi.spyOn(examsLib, 'exportExamPreviewPdf').mockResolvedValue(
      new Blob(['preview-bytes'], { type: 'application/pdf' }),
    );
    const createObjectUrlSpy = vi.fn(() => 'blob:preview');
    const revokeObjectUrlSpy = vi.fn();
    Object.defineProperty(window.URL, 'createObjectURL', {
      value: createObjectUrlSpy,
      configurable: true,
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      value: revokeObjectUrlSpy,
      configurable: true,
    });

    vi.spyOn(examsLib, 'getExam')
      .mockResolvedValueOnce({
        id: 'exam-1',
        title: 'Prova integradora',
        description: 'Avaliação criada pelo frontend',
        teacher_id: 'teacher-1',
        class_id: '2º Ano A',
        class_ids: ['class-1'],
        omr_template_id: null,
        total_questions: 2,
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
            statement: 'Questao 1',
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
              statement: 'Questao 1',
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
        total_questions: 2,
        total_time_seconds: 900,
        max_attempts: 2,
        randomization_enabled: true,
        max_score: '10.00',
        status: 'draft',
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

    render(<ExamDetailPage />);

    await screen.findByText('Prova integradora');
    const previewSection = screen.getByTestId('exam-preview-section');
    expect(within(previewSection).getByText('Questao 1')).toBeInTheDocument();
    expect(within(previewSection).getByText('A.')).toBeInTheDocument();
    expect(within(previewSection).getByText('B.')).toBeInTheDocument();
    expect(within(previewSection).queryByText('Gabarito')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Pré-visualizar prova' }));

    await waitFor(() => {
      expect(downloadSpy).toHaveBeenCalledWith('exam-1');
      expect(createObjectUrlSpy).toHaveBeenCalled();
      expect(revokeObjectUrlSpy).toHaveBeenCalled();
    });
  });

  it('allows updating the classes linked to an existing exam', async () => {
    const now = new Date().toISOString();
    vi.spyOn(classesLib, 'listClasses').mockResolvedValue([
      classroom,
      {
        ...classroom,
        id: 'class-2',
        name: '2º Ano B',
      },
    ]);

    vi.spyOn(examsLib, 'getExam')
      .mockResolvedValueOnce({
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
        created_at: now,
        updated_at: now,
        questions: [],
        exam_questions: [],
      })
      .mockResolvedValueOnce({
        id: 'exam-1',
        title: 'Prova integradora',
        description: 'Avaliação criada pelo frontend',
        teacher_id: 'teacher-1',
        class_id: null,
        class_ids: ['class-1', 'class-2'],
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
        questions: [],
        exam_questions: [],
      });
    vi.spyOn(examsLib, 'getExamStatistics').mockResolvedValue({
      exam_id: 'exam-1',
      exam_title: 'Prova integradora',
      total_attempts: 0,
      class_id: null,
      average_score: 0,
      max_score: 10,
      question_statistics: [],
    });
    const updateSpy = vi.spyOn(examsLib, 'updateExam').mockResolvedValue({
      id: 'exam-1',
      title: 'Prova integradora',
      description: 'Avaliação criada pelo frontend',
      teacher_id: 'teacher-1',
      class_id: null,
      class_ids: ['class-1', 'class-2'],
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
    });

    render(<ExamDetailPage />);

    await screen.findByText('Prova integradora');
    expect(screen.getByRole('checkbox', { name: /2º Ano A/ })).toBeChecked();
    fireEvent.click(screen.getByRole('checkbox', { name: /2º Ano B/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Salvar turmas' }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith('exam-1', {
        class_ids: ['class-1', 'class-2'],
      });
    });
  });

  it('publishes an exam directly from the exam list', async () => {
    const now = new Date().toISOString();
    vi.spyOn(examsLib, 'listExams')
      .mockResolvedValueOnce([
        {
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
        },
      ])
      .mockResolvedValueOnce([
        {
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
        },
      ]);
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

    render(<ExamsListPage />);

    await screen.findByText('Prova integradora');
    fireEvent.click(screen.getByRole('button', { name: 'Publicar' }));

    await waitFor(() => {
      expect(publishSpy).toHaveBeenCalledWith('exam-1');
      expect(screen.queryByRole('button', { name: 'Publicar' })).not.toBeInTheDocument();
    });
  });
});
