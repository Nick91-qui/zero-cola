import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import StartAttemptPage from '../app/attempts/start/page';
import AttemptPage from '../app/attempts/[attemptId]/page';
import DashboardPage from '../app/dashboard/page';
import * as attemptsLib from '@/lib/attempts';
import * as examsLib from '@/lib/exams';

const routerPush = vi.fn();
const searchParams = new URLSearchParams('examId=exam-123');

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
  useParams: () => ({ attemptId: 'attempt-1' }),
  useSearchParams: () => searchParams,
}));

vi.mock('@/app/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('@/app/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { email: 'student@cola-zero.edu', role: 'student' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

describe('Online attempt frontend flow', () => {
  beforeEach(() => {
    routerPush.mockReset();
    vi.restoreAllMocks();
  });

  it('starts an online attempt from the student landing page', async () => {
    vi.spyOn(attemptsLib, 'startOnlineAttempt').mockResolvedValue({
      attempt: {
        id: 'attempt-1',
        exam_id: 'exam-123',
        student_id: 'student-1',
        student_code: '12345',
        omr_scan_id: null,
        attempt_number: 1,
        source: 'ONLINE',
        status: 'in_progress',
        total_questions: 2,
        started_at: new Date().toISOString(),
        completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        answers: [],
      },
      current_question: null,
      total_questions: 2,
    });

    render(<StartAttemptPage />);

    expect(screen.getByDisplayValue('exam-123')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Iniciar tentativa' }));

    await waitFor(() => {
      expect(attemptsLib.startOnlineAttempt).toHaveBeenCalledWith('exam-123');
      expect(routerPush).toHaveBeenCalledWith('/attempts/attempt-1');
    });
  });

  it('renders one question at a time and supports autosave, navigation and submission', async () => {
    const now = new Date();
    const startedAt = new Date(Date.now() - 1000).toISOString();

    const session = {
      attempt: {
        id: 'attempt-1',
        exam_id: 'exam-123',
        student_id: 'student-1',
        student_code: '12345',
        omr_scan_id: null,
        attempt_number: 1,
        source: 'ONLINE',
        status: 'in_progress',
        total_questions: 2,
        started_at: startedAt,
        completed_at: null,
        created_at: now.toISOString(),
        updated_at: now.toISOString(),
        answers: [
          {
            id: 'answer-1',
            attempt_id: 'attempt-1',
            question_number: 1,
            question_id: 'question-1',
            statement: null,
            options: null,
            selected_option: null,
            answered_at: null,
          },
          {
            id: 'answer-2',
            attempt_id: 'attempt-1',
            question_number: 2,
            question_id: 'question-2',
            statement: null,
            options: null,
            selected_option: null,
            answered_at: null,
          },
        ],
      },
      current_question: {
        question_number: 1,
        question_id: 'question-1',
        statement: 'Primeira questão',
        options: {
          A: 'Alternativa A',
          B: 'Alternativa B',
        },
        selected_option: null,
        answered_at: null,
      },
      total_questions: 2,
    };

    const updatedSession = {
      ...session,
      current_question: {
        ...session.current_question,
        selected_option: 'A',
        answered_at: now.toISOString(),
      },
      attempt: {
        ...session.attempt,
        answers: session.attempt.answers.map((answer) =>
          answer.question_number === 1
            ? {
                ...answer,
                selected_option: 'A',
                answered_at: now.toISOString(),
              }
            : answer,
        ),
      },
    };

    const nextSession = {
      ...session,
      current_question: {
        question_number: 2,
        question_id: 'question-2',
        statement: 'Segunda questão',
        options: {
          A: 'Outra opção',
        },
        selected_option: null,
        answered_at: null,
      },
    };

    const result = {
      attempt: {
        ...session.attempt,
        status: 'graded',
        correct_answers: 1,
        incorrect_answers: 1,
        accuracy_percentage: '50.00',
        raw_score: '1.00',
        final_score: '5.00',
        completed_at: now.toISOString(),
      },
      grade: {
        id: 'grade-1',
        student_id: 'student-1',
        source_type: 'ONLINE' as const,
        source_id: 'attempt-1',
        score: '5.00',
        teacher_id: 'teacher-1',
        created_at: now.toISOString(),
        updated_at: now.toISOString(),
      },
    };

    vi.spyOn(attemptsLib, 'getAttemptSession').mockResolvedValue(session);
    vi.spyOn(examsLib, 'getExamSummary').mockResolvedValue({
      id: 'exam-123',
      title: 'Avaliação Online',
      description: 'Descrição',
      class_id: '301',
      total_time_seconds: 300,
      is_active: true,
      created_at: now.toISOString(),
      updated_at: now.toISOString(),
    });
    vi.spyOn(attemptsLib, 'saveAttemptAnswer').mockResolvedValue(updatedSession);
    vi.spyOn(attemptsLib, 'nextAttemptQuestion').mockResolvedValue(nextSession);
    vi.spyOn(attemptsLib, 'previousAttemptQuestion').mockResolvedValue(session);
    vi.spyOn(attemptsLib, 'submitAttempt').mockResolvedValue(result);
    vi.spyOn(attemptsLib, 'getAttemptResult').mockResolvedValue(result);

    render(<AttemptPage />);

    expect(await screen.findByText('Primeira questão')).toBeInTheDocument();
    expect(screen.getByText('Questão 1 de 2')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Alternativa A/ }));

    await waitFor(() => {
      expect(attemptsLib.saveAttemptAnswer).toHaveBeenCalledWith('attempt-1', 1, 'A');
    });

    fireEvent.click(screen.getByRole('button', { name: 'Próxima →' }));

    await waitFor(() => {
      expect(attemptsLib.nextAttemptQuestion).toHaveBeenCalledWith('attempt-1', 1);
      expect(screen.getByText('Segunda questão')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: '← Anterior' }));

    await waitFor(() => {
      expect(attemptsLib.previousAttemptQuestion).toHaveBeenCalledWith('attempt-1', 2);
      expect(screen.getByText('Primeira questão')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Submeter prova' }));

    await waitFor(() => {
      expect(screen.getByText('Tentativa concluída')).toBeInTheDocument();
      expect(screen.getByText('Acertos')).toBeInTheDocument();
      expect(screen.getByText('Grade')).toBeInTheDocument();
    });
  });

  it('exposes a student entry point in the dashboard', () => {
    render(<DashboardPage />);

    expect(screen.getByText('Provas Online')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Iniciar Prova Online/i })).toHaveAttribute(
      'href',
      '/attempts/start',
    );
  });
});
