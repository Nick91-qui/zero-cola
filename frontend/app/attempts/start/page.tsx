'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { listAvailableExams, startOnlineAttempt, type AvailableExam } from '@/lib/attempts';
import { listMyConsents, type Consent } from '@/lib/consents';

function StartAttemptContent() {
  const router = useRouter();
  const [availableExams, setAvailableExams] = useState<AvailableExam[]>([]);
  const [consents, setConsents] = useState<Consent[]>([]);
  const [loadingExams, setLoadingExams] = useState(true);
  const [loadingConsents, setLoadingConsents] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const monitoringConsent = consents.find((consent) => consent.consent_type === 'monitoring');
  const monitoringConsentGranted = Boolean(monitoringConsent?.granted);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoadingExams(true);
        setLoadingConsents(true);
        const [exams, consentData] = await Promise.all([listAvailableExams(), listMyConsents()]);
        if (active) {
          setAvailableExams(exams);
          setConsents(consentData);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar provas disponíveis');
        }
      } finally {
        if (active) {
          setLoadingExams(false);
          setLoadingConsents(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const handleStart = async (targetExamId: string) => {
    if (!monitoringConsentGranted) {
      setError('É necessário registrar o consentimento de monitoramento antes de iniciar a prova.');
      return;
    }

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
        <h1 className="mt-3 text-3xl font-bold text-slate-900">Iniciar tentativa online</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Antes de começar, confirme o consentimento de monitoramento. Depois disso, escolha uma
          prova publicada da sua turma para iniciar a tentativa com salvamento automático.
        </p>

        <div className="mt-8 space-y-6">
          <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="space-y-2">
                <h2 className="text-base font-semibold text-emerald-950">
                  Consentimento de monitoramento
                </h2>
                <p className="text-sm text-emerald-900">
                  O sistema só permite iniciar uma prova online após registrar o consentimento de
                  monitoramento.
                </p>
                <p className="text-xs text-emerald-800">
                  {loadingConsents
                    ? 'Carregando consentimento...'
                    : monitoringConsentGranted
                      ? 'Consentimento ativo para provas online.'
                      : 'Consentimento ausente ou revogado. Registre novamente antes de iniciar.'}
                </p>
              </div>
              <Link
                href="/consents"
                className="inline-flex items-center justify-center rounded-lg border border-emerald-700 px-4 py-2 text-xs font-semibold text-emerald-800 transition hover:bg-emerald-100"
              >
                Abrir consentimentos
              </Link>
            </div>
          </section>

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
                        disabled={loading || !monitoringConsentGranted}
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
            {!monitoringConsentGranted && (
              <Link
                href="/consents"
                className="rounded-lg bg-emerald-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
              >
                Registrar consentimento
              </Link>
            )}
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
