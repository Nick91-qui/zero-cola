import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import QuestionsPage from '../app/questions/page';
import * as questionsLib from '@/lib/questions';

const routerPush = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
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

describe('Question bank frontend flow', () => {
  beforeEach(() => {
    routerPush.mockReset();
    vi.restoreAllMocks();
  });

  it('lists reusable questions and exposes explicit creation links', async () => {
    vi.spyOn(questionsLib, 'listQuestions').mockResolvedValue([
      {
        id: 'question-1',
        statement: 'Questão existente',
        type: 'multiple_choice',
        options: { A: '1', B: '2' },
        correct_answer: 'B',
        explanation: null,
        image_url: null,
        subject: 'Matemática',
        difficulty: 'easy',
        tags: ['básico'],
        parent_id: null,
        version: 1,
        is_active: true,
        created_by: 'teacher-1',
        skills: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    render(<QuestionsPage />);

    await screen.findByText('Banco de questões');
    expect(screen.getByText('Questão existente')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Criar habilidades' })).toHaveAttribute(
      'href',
      '/questions/skills/new',
    );
    expect(screen.getByRole('link', { name: 'Criar questões' })).toHaveAttribute(
      'href',
      '/questions/new',
    );
  });

  it('shows a question card with an explicit edit link', async () => {
    vi.spyOn(questionsLib, 'listQuestions').mockResolvedValue([
      {
        id: 'question-1',
        statement: 'Questão existente',
        type: 'multiple_choice',
        options: { A: '1', B: '2' },
        correct_answer: 'B',
        explanation: null,
        image_url: null,
        subject: 'Matemática',
        difficulty: 'easy',
        tags: ['básico'],
        parent_id: null,
        version: 1,
        is_active: true,
        created_by: 'teacher-1',
        skills: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    render(<QuestionsPage />);

    await screen.findByText('Banco de questões');
    expect(screen.getByRole('link', { name: 'Editar / Versionar' })).toHaveAttribute(
      'href',
      '/questions/question-1',
    );
  });

  it('loads question bank pages through backend filters', async () => {
    const questionData = Array.from({ length: 8 }, (_, index) => ({
      id: `question-${index + 1}`,
      statement: `Questão ${index + 1}`,
      type: 'multiple_choice',
      options: { A: '1', B: '2' },
      correct_answer: 'B',
      explanation: null,
      image_url: null,
      subject: index % 2 === 0 ? 'Matemática' : 'História',
      difficulty: index % 2 === 0 ? 'easy' : 'medium',
      tags: ['aritmética'],
      parent_id: null,
      version: 1,
      is_active: index !== 7,
      created_by: 'teacher-1',
      skills: [
        {
          id: 'skill-1',
          code: 'EF05MA01',
          description: 'Resolver adições simples',
          subject: 'Matemática',
          grade_level: '5',
          curriculum: 'BNCC',
        },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));

    const listSpy = vi.spyOn(questionsLib, 'listQuestions').mockResolvedValue(questionData);

    render(<QuestionsPage />);

    await screen.findByText('Banco de questões');
    expect(listSpy).toHaveBeenCalledWith({
      q: undefined,
      skill_id: undefined,
      include_inactive: false,
      limit: 100,
    });

    fireEvent.change(screen.getByLabelText('Buscar por texto'), {
      target: { value: 'frações' },
    });
    fireEvent.change(screen.getByLabelText('Habilidade'), {
      target: { value: 'skill-1' },
    });
    fireEvent.click(screen.getByLabelText('Incluir inativas'));

    await waitFor(() => {
      expect(listSpy).toHaveBeenLastCalledWith({
        q: 'frações',
        skill_id: 'skill-1',
        include_inactive: true,
        limit: 100,
      });
    });
  });
});
