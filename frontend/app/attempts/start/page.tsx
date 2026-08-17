'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { listAvailableExams, startOnlineAttempt, type AvailableExam } from '@/lib/attempts';

function StartAttemptContent() {
  const router = useRouter();
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

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Prova online
            </p>
            <h1 className="mt-3 text-3xl font-bold text-slate-900">
              Iniciar tentativa online
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Escolha uma prova publicada da sua turma para iniciar a tentativa e continuar a prova
              com salvamento automático.
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

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href="/dashboard"
                  className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Voltar ao painel
                </Link>
              </div>
            </div>
      </div>
    </div>
  );
}

export default function StartAttemptPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">
          Carregando tentativa...
        </div>
      }
    >
      <StartAttemptContent />
    </Suspense>
  );
}
