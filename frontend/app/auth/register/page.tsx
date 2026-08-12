'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { addStudentsToClass, addTeachersToClass, listClasses, type ClassSummary } from '@/lib/classes';
import { createUser } from '@/lib/users';

type AdminUserRole = 'student' | 'teacher';

export default function RegisterPage() {
  const { user, logout, isLoading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [role, setRole] = useState<AdminUserRole>('teacher');
  const [studentCode, setStudentCode] = useState('');
  const [classSearch, setClassSearch] = useState('');
  const [selectedClassIds, setSelectedClassIds] = useState<string[]>([]);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const loadClasses = async () => {
      try {
        setLoadingClasses(true);
        const data = await listClasses(false);
        if (active) {
          setClasses(data);
        }
      } catch (err) {
        if (active) {
          setLocalError(err instanceof Error ? err.message : 'Falha ao carregar turmas');
        }
      } finally {
        if (active) {
          setLoadingClasses(false);
        }
      }
    };

    void loadClasses();

    return () => {
      active = false;
    };
  }, []);

  const filteredClasses = useMemo(() => {
    const search = classSearch.trim().toLowerCase();
    if (!search) return classes;
    return classes.filter((classItem) => {
      const haystack = [
        classItem.name,
        classItem.academic_period ?? '',
        classItem.description ?? '',
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(search);
    });
  }, [classSearch, classes]);

  const toggleClass = (classId: string) => {
    setSelectedClassIds((current) =>
      current.includes(classId)
        ? current.filter((id) => id !== classId)
        : [...current, classId],
    );
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setPasswordConfirm('');
    setStudentCode('');
    setSelectedClassIds([]);
    setClassSearch('');
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);

    if (!email || !password || !passwordConfirm) {
      setLocalError('All fields are required');
      return;
    }

    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters');
      return;
    }

    if (password !== passwordConfirm) {
      setLocalError('Passwords do not match');
      return;
    }

    if (role === 'student' && !/^\d{5}$/.test(studentCode)) {
      setLocalError('Student code must be exactly 5 digits');
      return;
    }

    setIsSubmitting(true);

    try {
      const created = await createUser({
        email,
        password,
        role,
        student_code: role === 'student' ? studentCode : null,
      });

      if (selectedClassIds.length > 0) {
        const payload = [created.id];
        await Promise.all(
          selectedClassIds.map((classId) =>
            role === 'teacher'
              ? addTeachersToClass(classId, payload)
              : addStudentsToClass(classId, payload),
          ),
        );
      }

      const roleLabel = role === 'student' ? 'Aluno' : 'Professor';
      setSuccessMessage(
        selectedClassIds.length > 0
          ? `${roleLabel} ${created.email} criado e vinculado com sucesso.`
          : `${roleLabel} ${created.email} criado com sucesso.`,
      );
      resetForm();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const assignmentLabel =
    role === 'student'
      ? 'Matricular aluno nas turmas selecionadas'
      : 'Vincular professor às turmas selecionadas';

  return (
    <ProtectedRoute requiredRoles={['admin']}>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <div className="flex items-center gap-4">
              <span className="text-lg font-bold text-slate-900">COLA-ZERO</span>
              <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                Cadastro admin
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span>{user?.email}</span>
              <button
                type="button"
                onClick={logout}
                disabled={authLoading}
                className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700 disabled:bg-slate-400"
              >
                Sair
              </button>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-6xl px-4 py-10">
          <div className="mb-8 flex flex-col gap-3">
            <h1 className="text-3xl font-bold text-slate-900">Cadastro de usuários</h1>
            <p className="max-w-3xl text-sm text-slate-600">
              Crie contas de professor ou aluno e já faça o vínculo com as turmas corretas na
              mesma operação.
            </p>
            <p className="max-w-3xl text-xs text-slate-500">
              A disciplina é organizada pelo contexto da turma. Para professor, selecione as
              turmas que representam sua carga; para aluno, selecione a turma de matrícula.
            </p>
          </div>

          {localError && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {localError}
            </div>
          )}

          {successMessage && (
            <div className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {successMessage}
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-5">
                <h2 className="text-lg font-semibold text-slate-900">Novo usuário</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Selecione o papel e cadastre a conta.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isSubmitting}
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                    placeholder="user@email.com"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="role" className="block text-sm font-medium text-slate-700">
                    Papel
                  </label>
                  <select
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value as AdminUserRole)}
                    disabled={isSubmitting}
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  >
                    <option value="teacher">Professor</option>
                    <option value="student">Aluno</option>
                  </select>
                </div>

                {role === 'student' && (
                  <div>
                    <label htmlFor="studentCode" className="block text-sm font-medium text-slate-700">
                      Código do aluno
                    </label>
                    <input
                      id="studentCode"
                      type="text"
                      inputMode="numeric"
                      pattern="\d{5}"
                      maxLength={5}
                      value={studentCode}
                      onChange={(e) => setStudentCode(e.target.value.replace(/\D/g, '').slice(0, 5))}
                      disabled={isSubmitting}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                      placeholder="10234"
                      required
                    />
                    <p className="mt-1 text-xs text-slate-500">
                      Exatamente 5 dígitos, usado na prova OMR.
                    </p>
                  </div>
                )}

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                    Senha
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isSubmitting}
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                    placeholder="••••••••"
                    minLength={8}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="passwordConfirm" className="block text-sm font-medium text-slate-700">
                    Confirmar senha
                  </label>
                  <input
                    id="passwordConfirm"
                    type="password"
                    value={passwordConfirm}
                    onChange={(e) => setPasswordConfirm(e.target.value)}
                    disabled={isSubmitting}
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                    placeholder="••••••••"
                    minLength={8}
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
                >
                  {isSubmitting ? 'Criando...' : 'Criar usuário'}
                </button>
              </form>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">Turmas</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Selecione as turmas que serão vinculadas ao usuário criado.
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  {selectedClassIds.length} selecionada(s)
                </span>
              </div>

              <label className="block text-sm font-medium text-slate-700">
                Buscar turma
                <input
                  type="search"
                  value={classSearch}
                  onChange={(e) => setClassSearch(e.target.value)}
                  placeholder="Nome, período ou descrição"
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                />
              </label>

              <p className="mt-2 text-xs text-slate-500">
                O vínculo será aplicado automaticamente após o cadastro.
              </p>

              {loadingClasses ? (
                <p className="mt-6 text-sm text-slate-500">Carregando turmas...</p>
              ) : filteredClasses.length === 0 ? (
                <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                  <p className="text-sm text-slate-500">
                    Nenhuma turma encontrada. Crie turmas na área de classes antes de vincular
                    usuários.
                  </p>
                </div>
              ) : (
                <div className="mt-5 grid gap-3">
                  {filteredClasses.map((classItem) => {
                    const checked = selectedClassIds.includes(classItem.id);
                    return (
                      <label
                        key={classItem.id}
                        className={[
                          'flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 transition',
                          checked
                            ? 'border-emerald-300 bg-emerald-50'
                            : 'border-slate-200 bg-slate-50 hover:border-emerald-300',
                        ].join(' ')}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleClass(classItem.id)}
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                        />
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-slate-900">{classItem.name}</span>
                            <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                              {classItem.academic_period || 'sem período'}
                            </span>
                          </div>
                          {classItem.description && (
                            <p className="mt-1 text-sm text-slate-600">{classItem.description}</p>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}

              <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Ação final</p>
                <p className="mt-1 text-sm text-slate-600">{assignmentLabel}</p>
              </div>
            </section>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
