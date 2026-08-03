import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { MemberSearchField } from '../app/classes/[classId]/member-search-field';
import * as usersLib from '@/lib/users';

describe('MemberSearchField', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('searches and submits selected students', async () => {
    const submitSpy = vi.fn().mockResolvedValue(undefined);

    vi.spyOn(usersLib, 'searchUsers').mockResolvedValue([
      {
        id: 'student-2',
        email: 'student2@cola-zero.edu',
        role: 'student',
        student_code: '54321',
        is_active: true,
      },
    ]);

    render(
      <MemberSearchField
        role="student"
        title="Vincular estudante(s)"
        helperText="Busque estudantes por e-mail ou código para adicionar à turma."
        placeholder="Ex: aluno@cola-zero.edu ou 12345"
        actionLabel="Vincular estudantes"
        onSubmit={submitSpy}
      />,
    );

    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: 'student-2' },
    });

    expect(await screen.findByText('student2@cola-zero.edu (54321)')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Adicionar' }));
    fireEvent.click(screen.getByRole('button', { name: 'Vincular estudantes' }));

    await waitFor(() => {
      expect(submitSpy).toHaveBeenCalledWith(['student-2']);
    });
  });
});
