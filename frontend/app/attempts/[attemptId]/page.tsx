'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { ApiError } from '@/lib/api';
import { getExamSummary, type ExamSummary } from '@/lib/exams';
import {
  getAttemptResult,
  getAttemptSession,
  nextAttemptQuestion,
  previousAttemptQuestion,
  saveAttemptAnswer,
  submitAttempt,
  type AttemptResult,
  type AttemptSession,
} from '@/lib/attempts';

function normalizeError(error: unknown) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return 'Falha inesperada ao carregar a tentativa';
}

function formatDuration(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function stringifyOption(value: unknown) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (value && typeof value === 'object') return JSON.stringify(value);
  return '';
}

export default function AttemptPage() {
  const params = useParams<{ attemptId: string }>();
  const attemptId = params.attemptId;
  const { user, logout } = useAuth();

  const [session, setSession] = useState<AttemptSession | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [exam, setExam] = useState<ExamSummary | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentQuestion = session?.current_question ?? null;

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const attemptSession = await getAttemptSession(attemptId);
        if (!active) return;

        setSession(attemptSession);
        setResult(null);
        setSelectedOption(attemptSession.current_question?.selected_option ?? null);
        try {
          const examSummary = await getExamSummary(attemptSession.attempt.exam_id);
          if (active) {
            setExam(examSummary);
          }
        } catch {
          if (active) {
            setExam(null);
          }
        }
      } catch (sessionError) {
        try {
          const attemptResult = await getAttemptResult(attemptId);
          if (!active) return;

          setResult(attemptResult);
          setSession(null);
          setSelectedOption(null);
          try {
            const examSummary = await getExamSummary(attemptResult.attempt.exam_id);
            if (active) {
              setExam(examSummary);
            }
          } catch {
            if (active) {
              setExam(null);
            }
          }
        } catch (resultError) {
          if (active) {
            setError(normalizeError(resultError ?? sessionError));
          }
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    load();
    return () => {
      active = false;
    };
  }, [attemptId]);

  useEffect(() => {
    setSelectedOption(currentQuestion?.selected_option ?? null);
  }, [currentQuestion?.question_number, currentQuestion?.selected_option]);

  const questionOptions = currentQuestion?.options
    ? Object.entries(currentQuestion.options).sort(([a], [b]) => a.localeCompare(b))
    : [];

  const handleSelect = async (option: string) => {
    if (!currentQuestion) return;
    const previousSelection = selectedOption;
    setSelectedOption(option);
    setSaving(true);
    setError(null);

    try {
      const updated = await saveAttemptAnswer(attemptId, currentQuestion.question_number, option);
      setSession(updated);
      setSelectedOption(updated.current_question?.selected_option ?? null);
    } catch (selectError) {
      setSelectedOption(previousSelection);
      setError(normalizeError(selectError));
    } finally {
      setSaving(false);
    }
  };

  const handleNavigate = async (direction: 'previous' | 'next') => {
    if (!currentQuestion) return;

    setSaving(true);
    setError(null);

    try {
      const updated =
        direction === 'next'
          ? await nextAttemptQuestion(attemptId, currentQuestion.question_number)
          : await previousAttemptQuestion(attemptId, currentQuestion.question_number);
      setSession(updated);
      setSelectedOption(updated.current_question?.selected_option ?? null);
    } catch (navigateError) {
      setError(normalizeError(navigateError));
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const attemptResult = await submitAttempt(attemptId);
      setResult(attemptResult);
      setSession(null);
      setSelectedOption(null);
    } catch (submitError) {
      setError(normalizeError(submitError));
    } finally {
      setSubmitting(false);
    }
  };

  const answeredCount = session?.attempt.answers.filter((answer) => answer.selected_option).length ?? 0;

  return (
    <ProtectedRoute requiredRole="student">
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
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

        <main className="mx-auto max-w-6xl px-4 py-10">
          {loading ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
              Carregando sua tentativa...
            </div>
          ) : error && !session && !result ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm">
              {error}
            </div>
          ) : result ? (
            <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                Tentativa concluída
              </p>
              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                {exam?.title || 'Resultado da tentativa'}
              </h1>
              <p className="mt-2 text-sm text-slate-600">
                {result.attempt.total_questions} questões · resposta final consolidada e gravada.
              </p>

              <div className="mt-8 grid gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Acertos
                  </span>
                  <p className="mt-2 text-3xl font-bold text-slate-900">
                    {result.attempt.correct_answers}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Erros
                  </span>
                  <p className="mt-2 text-3xl font-bold text-slate-900">
                    {result.attempt.incorrect_answers}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Nota
                  </span>
                  <p className="mt-2 text-3xl font-bold text-slate-900">
                    {result.attempt.final_score}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Grade
                  </span>
                  <p className="mt-2 text-3xl font-bold text-slate-900">
                    {result.grade?.score ?? result.attempt.final_score}
                  </p>
                </div>
              </div>

              <div className="mt-8 overflow-hidden rounded-xl border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-slate-700">Questão</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-700">Resposta marcada</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-700">Correta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {result.attempt.answers.map((answer) => (
                      <tr key={answer.id}>
                        <td className="px-4 py-3 font-medium text-slate-900">Q{answer.question_number}</td>
                        <td className="px-4 py-3 text-slate-700">
                          {answer.selected_option ?? 'Sem resposta'}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={
                              answer.is_correct
                                ? 'rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800'
                                : 'rounded-full bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-800'
                            }
                          >
                            {answer.is_correct ? 'Sim' : 'Não'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : session && currentQuestion ? (
            <section className="grid gap-6 lg:grid-cols-[1fr_320px]">
              <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                      Prova online
                    </p>
                    <h1 className="mt-2 text-3xl font-bold text-slate-900">
                      {exam?.title || 'Avaliação em andamento'}
                    </h1>
                    <p className="mt-1 text-sm text-slate-600">
                      Questão {currentQuestion.question_number} de {session.total_questions}
                    </p>
                  </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-right">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                      Tempo limite
                  </p>
                  <p className="mt-1 text-2xl font-bold text-slate-900">
                      {exam?.total_time_seconds ? formatDuration(exam.total_time_seconds) : '—'}
                  </p>
                </div>
              </div>

                {error && (
                  <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-6">
                  <p className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
                    Enunciado
                  </p>
                  <div className="mt-3 whitespace-pre-line text-base leading-7 text-slate-900">
                    {currentQuestion.statement || 'Questão sem enunciado textual.'}
                  </div>
                </div>

                <div className="mt-6 grid gap-3">
                  {questionOptions.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">
                      Esta questão não possui alternativas estruturadas.
                    </div>
                  ) : (
                    questionOptions.map(([key, value]) => {
                      const isSelected = selectedOption === key;
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => handleSelect(key)}
                          disabled={saving}
                          className={[
                            'flex items-start gap-4 rounded-xl border px-4 py-4 text-left transition',
                            isSelected
                              ? 'border-emerald-600 bg-emerald-50 shadow-sm'
                              : 'border-slate-200 bg-white hover:border-emerald-300 hover:bg-emerald-50/40',
                          ].join(' ')}
                        >
                          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white">
                            {key}
                          </span>
                          <span className="text-sm leading-6 text-slate-800">
                            {stringifyOption(value) || 'Alternativa sem descrição'}
                          </span>
                        </button>
                      );
                    })
                  )}
                </div>

                <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => handleNavigate('previous')}
                      disabled={saving || currentQuestion.question_number <= 1}
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                    >
                      ← Anterior
                    </button>
                    <button
                      type="button"
                      onClick={() => handleNavigate('next')}
                      disabled={saving || currentQuestion.question_number >= session.total_questions}
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                    >
                      Próxima →
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="rounded-lg bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {submitting ? 'Submetendo...' : 'Submeter prova'}
                  </button>
                </div>
              </div>

              <aside className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Resumo
                  </p>
                  <dl className="mt-4 space-y-3 text-sm text-slate-700">
                    <div className="flex items-center justify-between">
                      <dt>Respondidas</dt>
                      <dd className="font-semibold text-slate-900">{answeredCount}</dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt>Total</dt>
                      <dd className="font-semibold text-slate-900">{session.total_questions}</dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt>Status</dt>
                      <dd className="font-semibold text-slate-900">{session.attempt.status}</dd>
                    </div>
                    <div className="flex items-center justify-between">
                      <dt>Sequência</dt>
                      <dd className="font-semibold text-slate-900">
                        {session.attempt.attempt_number}
                      </dd>
                    </div>
                  </dl>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Navegação
                  </p>
                  <ol className="mt-4 space-y-2 text-sm text-slate-700">
                    {session.attempt.answers.map((answer) => (
                      <li
                        key={answer.question_number}
                        className={[
                          'flex items-center justify-between rounded-lg px-3 py-2',
                          answer.question_number === currentQuestion.question_number
                            ? 'bg-emerald-50 text-emerald-800'
                            : 'bg-slate-50',
                        ].join(' ')}
                      >
                        <span>Questão {answer.question_number}</span>
                        <span className="text-xs font-medium">
                          {answer.selected_option ?? 'Pendente'}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              </aside>
            </section>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
              Não foi possível carregar a tentativa.
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
