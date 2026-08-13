'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, Suspense, useEffect, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { listAvailableExams, startOnlineAttempt, type AvailableExam } from '@/lib/attempts';

function StartAttemptContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const [examId, setExamId] = useState(() => searchParams.get('examId') ?? '');
  const [availableExams, setAvailableExams] = useState<AvailableExam[]>([]);
  const [loadingExams, setLoadingExams] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoadingExams(true);
        const exams = await listAvailableExams();
        if (active) {
          setAvailableExams(exams);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar provas disponíveis');
        }
      } finally {
        if (active) {
          setLoadingExams(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const handleStart = async (targetExamId: string) => {
    setLoading(true);
    setError(null);

    try {
      const session = await startOnlineAttempt(targetExamId);
      router.push(`/attempts/${session.attempt.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao iniciar a tentativa');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await handleStart(examId.trim());
  };

  return (
    <ProtectedRoute requiredRole="student">
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
            <Link href="/dashboard" className="text-lg font-bold text-slate-900">
              COLA-ZERO
            </Link>
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

        <main className="mx-auto max-w-4xl px-4 py-10">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Prova online
            </p>
            <h1 className="mt-3 text-3xl font-bold text-slate-900">
              Iniciar tentativa online
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Escolha uma prova publicada da sua turma ou informe o identificador da avaliação para iniciar a tentativa e continuar a prova com salvamento automático.
            </p>

            <div className="mt-8 space-y-6">
              <section className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-slate-900">Provas disponíveis</h2>
                    <p className="text-xs text-slate-500">
                      Apenas provas publicadas e liberadas para suas turmas aparecem aqui.
                    </p>
                  </div>
                  {loadingExams && <span className="text-xs text-slate-500">Carregando...</span>}
                </div>

                {availableExams.length === 0 && !loadingExams ? (
                  <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
                    Nenhuma prova disponível no momento.
                  </div>
                ) : (
                  <div className="mt-4 grid gap-3">
                    {availableExams.map((exam) => (
                      <article
                        key={exam.id}
                        className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                      >
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                          <div className="space-y-1">
                            <h3 className="text-sm font-semibold text-slate-900">{exam.title}</h3>
                            <p className="text-xs text-slate-600">
                              {exam.description || 'Sem descrição.'}
                            </p>
                            <p className="text-xs text-slate-500">
                              {exam.total_questions} questão(ões)
                              {exam.total_time_seconds ? ` · ${exam.total_time_seconds}s` : ''}
                              {exam.randomization_enabled ? ' · ordem randomizada' : ''}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => void handleStart(exam.id)}
                            disabled={loading}
                            className="rounded-lg bg-emerald-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                          >
                            {loading ? 'Iniciando...' : 'Iniciar prova'}
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <form onSubmit={handleSubmit} className="space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-700">
                    ID da avaliação manual
                  </span>
                  <input
                    value={examId}
                    onChange={(event) => setExamId(event.target.value)}
                    placeholder="Cole aqui o exam_id"
                    className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-600"
                  />
                </label>

                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={loading || !examId.trim()}
                    className="rounded-lg bg-emerald-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {loading ? 'Iniciando...' : 'Iniciar por ID'}
                  </button>
                  <Link
                    href="/dashboard"
                    className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    Voltar ao painel
                  </Link>
                </div>
              </form>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}

export default function StartAttemptPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50">
          <main className="mx-auto max-w-4xl px-4 py-10">
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">
              Carregando tentativa...
            </div>
          </main>
        </div>
      }
    >
      <StartAttemptContent />
    </Suspense>
  );
}
