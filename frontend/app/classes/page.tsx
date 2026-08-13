'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import {
  createClass,
  listClasses,
  type ClassCreatePayload,
  type ClassSummary,
} from '@/lib/classes';

export default function ClassesPage() {
  const { user, logout } = useAuth();
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [academicPeriod, setAcademicPeriod] = useState('');
  const [description, setDescription] = useState('');

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await listClasses(includeArchived);
        if (active) {
          setClasses(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar turmas');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, [includeArchived]);

  const handleCreateClass = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = name.trim();

    if (!trimmedName) {
      setError('Informe o nome da turma.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      if (!isAdmin) {
        setError('A criação de turmas é restrita ao administrador.');
        return;
      }
      const payload: ClassCreatePayload = {
        name: trimmedName,
        academic_period: academicPeriod.trim() || null,
        description: description.trim() || null,
      };
      const created = await createClass(payload);
      setClasses((current) => [created, ...current]);
      setName('');
      setAcademicPeriod('');
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar turma');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-lg font-bold text-slate-900">
                COLA-ZERO
              </Link>
              <span className="rounded bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-800">
                Turmas
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span>{user?.email}</span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
              >
                Sair
              </button>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-6xl px-4 py-10">
          <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Turmas</h1>
              <p className="mt-1 max-w-3xl text-sm text-slate-600">
                {isAdmin
                  ? 'Crie turmas vazias, vincule professores e cadastre membros quando fizer sentido.'
                  : 'Consulte as turmas vinculadas à sua conta e abra o detalhe para ver informações e vínculos.'}
              </p>
            </div>

            <label className="inline-flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
              <input
                type="checkbox"
                checked={includeArchived}
                onChange={(event) => setIncludeArchived(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
              Incluir turmas arquivadas
            </label>
          </div>

          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">Turmas cadastradas</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    {loading ? 'Carregando turmas...' : `${classes.length} turma(s) encontradas`}
                  </p>
                </div>
              </div>

              {loading ? (
                <p className="py-12 text-center text-sm text-slate-500">Carregando turmas...</p>
              ) : classes.length === 0 ? (
                <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                  <p className="text-sm text-slate-500">Nenhuma turma encontrada.</p>
                </div>
              ) : (
                <div className="mt-6 grid gap-4">
                  {classes.map((classItem) => (
                    <article
                      key={classItem.id}
                      className="rounded-xl border border-slate-200 bg-slate-50 p-5 transition hover:border-emerald-400 hover:bg-emerald-50/40"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-lg font-semibold text-slate-900">{classItem.name}</h3>
                            <span
                              className={[
                                'rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-[0.15em]',
                                classItem.is_active
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-slate-200 text-slate-700',
                              ].join(' ')}
                            >
                              {classItem.is_active ? 'Ativa' : 'Arquivada'}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-slate-600">
                            {classItem.academic_period || 'Sem período informado'}
                          </p>
                          <p className="mt-1 text-sm text-slate-700">
                            Professor:{' '}
                            {classItem.teacher_id ? 'vinculado' : 'sem professor vinculado'}
                          </p>
                          {classItem.description && (
                            <p className="mt-2 max-w-2xl text-sm text-slate-700">
                              {classItem.description}
                            </p>
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm">
                            {classItem.student_count} estudante(s)
                          </span>
                          <Link
                            href={`/classes/${classItem.id}`}
                            className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
                          >
                            Abrir detalhe →
                          </Link>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              {isAdmin ? (
                <>
                  <h2 className="text-lg font-semibold text-slate-900">Nova turma</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Registre uma turma vazia agora e associe professores e alunos depois.
                  </p>

                  <form onSubmit={handleCreateClass} className="mt-6 space-y-4">
                    <label className="block text-sm font-medium text-slate-700">
                      Nome
                      <input
                        type="text"
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        placeholder="Ex: 2º Ano A"
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                      />
                    </label>

                    <label className="block text-sm font-medium text-slate-700">
                      Período letivo
                      <input
                        type="text"
                        value={academicPeriod}
                        onChange={(event) => setAcademicPeriod(event.target.value)}
                        placeholder="Ex: 2026"
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                      />
                    </label>

                    <label className="block text-sm font-medium text-slate-700">
                      Descrição
                      <textarea
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        rows={4}
                        placeholder="Observações da turma"
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                      />
                    </label>

                    <button
                      type="submit"
                      disabled={saving}
                      className="w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
                    >
                      {saving ? 'Criando...' : 'Criar turma'}
                    </button>
                  </form>
                </>
              ) : (
                <>
                  <h2 className="text-lg font-semibold text-slate-900">Acesso de consulta</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    O administrador realiza o cadastro de turmas e vínculos. Aqui você vê apenas as
                    turmas que já foram disponibilizadas para sua conta.
                  </p>
                </>
              )}
            </section>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
