import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import QuestionsPage from '../app/questions/page';
import * as questionsLib from '@/lib/questions';
import * as skillsLib from '@/lib/skills';

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

  it('lists reusable questions and creates a new bank item', async () => {
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
    vi.spyOn(skillsLib, 'listSkills').mockResolvedValue([
      {
        id: 'skill-1',
        code: 'EF05MA01',
        description: 'Resolver adições simples',
        subject: 'Matemática',
        grade_level: '5',
        curriculum: 'BNCC',
      },
    ]);
    const createSpy = vi.spyOn(questionsLib, 'createQuestion').mockResolvedValue({
      id: 'question-2',
      statement: 'Quanto é 2 + 3?',
      type: 'multiple_choice',
      options: { A: '4', B: '5' },
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
    });

    render(<QuestionsPage />);

    await screen.findByText('Questões reutilizáveis');
    expect(screen.getByText('Questão existente')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Enunciado'), {
      target: { value: 'Quanto é 2 + 3?' },
    });
    fireEvent.change(screen.getByLabelText('Matéria'), {
      target: { value: 'Matemática' },
    });
    fireEvent.change(screen.getByLabelText('Dificuldade'), {
      target: { value: 'easy' },
    });
    fireEvent.change(screen.getByLabelText('Tags'), {
      target: { value: 'aritmética' },
    });
    fireEvent.change(screen.getByLabelText('Gabarito correto'), {
      target: { value: 'B' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa A'), {
      target: { value: '4' },
    });
    fireEvent.change(screen.getByPlaceholderText('Texto da alternativa B'), {
      target: { value: '5' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: /EF05MA01/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Criar questão' }));

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          statement: 'Quanto é 2 + 3?',
          subject: 'Matemática',
          difficulty: 'easy',
          tags: ['aritmética'],
          skill_ids: ['skill-1'],
        }),
      );
      expect(screen.getByText('Quanto é 2 + 3?')).toBeInTheDocument();
    });
  });

  it('loads question bank pages through backend filters and pagination', async () => {
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
    vi.spyOn(skillsLib, 'listSkills').mockResolvedValue([
      {
        id: 'skill-1',
        code: 'EF05MA01',
        description: 'Resolver adições simples',
        subject: 'Matemática',
        grade_level: '5',
        curriculum: 'BNCC',
      },
    ]);

    render(<QuestionsPage />);

    await screen.findByText('Questões reutilizáveis');
    expect(listSpy).toHaveBeenCalledWith({
      q: undefined,
      skill_id: undefined,
      include_inactive: false,
      skip: 0,
      limit: 8,
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
        skip: 0,
        limit: 8,
      });
    });

    fireEvent.click(screen.getByRole('button', { name: 'Próxima' }));

    await waitFor(() => {
      expect(listSpy).toHaveBeenLastCalledWith({
        q: 'frações',
        skill_id: 'skill-1',
        include_inactive: true,
        skip: 8,
        limit: 8,
      });
    });
  });
});
