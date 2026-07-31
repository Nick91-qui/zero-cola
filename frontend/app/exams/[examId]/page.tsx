'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import {
  archiveExam,
  getExam,
  getExamStatistics,
  publishExam,
  returnExamToDraft,
  type ExamDetail,
  type ExamStatistics,
} from '@/lib/exams';

function downloadLabelList(values: string[] | undefined) {
  if (!values || values.length === 0) return 'Geral';
  return values.join(', ');
}

function statusBadge(status?: string) {
  switch (status) {
    case 'published':
      return 'bg-emerald-100 text-emerald-800';
    case 'archived':
      return 'bg-slate-200 text-slate-700';
    default:
      return 'bg-amber-100 text-amber-800';
  }
}

export default function ExamDetailStatisticsPage() {
  const params = useParams<{ examId: string }>();
  const examId = params.examId;

  const [exam, setExam] = useState<ExamDetail | null>(null);
  const [stats, setStats] = useState<ExamStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const loadExam = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [examData, statsData] = await Promise.all([
        getExam(examId),
        getExamStatistics(examId),
      ]);
      setExam(examData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar avaliação');
    } finally {
      setLoading(false);
    }
  }, [examId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- data fetch hydrates local exam state on mount
    void loadExam();
  }, [loadExam]);

  const handleAction = async (action: 'publish' | 'draft' | 'archive') => {
    setBusyAction(action);
    setError(null);
    try {
      const updated =
        action === 'publish'
          ? await publishExam(examId)
          : action === 'draft'
            ? await returnExamToDraft(examId)
            : await archiveExam(examId);
      setExam((current) => (current ? { ...current, ...updated } : updated));
      await loadExam();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar status da avaliação');
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <main className="mx-auto max-w-6xl px-4 py-10">
          <Link href="/exams" className="text-sm font-medium text-emerald-700 hover:underline">
            ← Voltar para Avaliações
          </Link>

          {loading ? (
            <p className="mt-8 text-center text-sm text-slate-500">Carregando avaliação...</p>
          ) : error || !stats || !exam ? (
            <div className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error || 'Avaliação não encontrada.'}
            </div>
          ) : (
            <>
              <div className="mt-4 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <h1 className="text-3xl font-bold text-slate-900">{exam.title}</h1>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${statusBadge(exam.status)}`}>
                      {exam.status || 'draft'}
                    </span>
                  </div>
                  <p className="max-w-3xl text-sm text-slate-600">
                    {exam.description || 'Sem descrição cadastrada.'}
                  </p>

                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Turmas
                      </span>
                      <p className="mt-2 text-sm font-semibold text-slate-900">
                        {downloadLabelList(exam.class_ids)}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Questões
                      </span>
                      <p className="mt-2 text-2xl font-bold text-slate-900">{exam.total_questions}</p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Tempo
                      </span>
                      <p className="mt-2 text-2xl font-bold text-slate-900">
                        {exam.total_time_seconds ?? '—'}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Randomização
                      </span>
                      <p className="mt-2 text-sm font-semibold text-slate-900">
                        {exam.randomization_enabled ? 'Ativada' : 'Desativada'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {exam.status === 'draft' && (
                    <button
                      type="button"
                      onClick={() => handleAction('publish')}
                      disabled={busyAction !== null}
                      className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-600 disabled:bg-slate-300"
                    >
                      {busyAction === 'publish' ? 'Publicando...' : 'Publicar'}
                    </button>
                  )}
                  {exam.status === 'published' && (
                    <button
                      type="button"
                      onClick={() => handleAction('draft')}
                      disabled={busyAction !== null}
                      className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 disabled:text-slate-400"
                    >
                      {busyAction === 'draft' ? 'Revertendo...' : 'Voltar para rascunho'}
                    </button>
                  )}
                  {exam.status !== 'archived' && (
                    <button
                      type="button"
                      onClick={() => handleAction('archive')}
                      disabled={busyAction !== null}
                      className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 shadow-sm hover:bg-red-100 disabled:text-slate-400"
                    >
                      {busyAction === 'archive' ? 'Arquivando...' : 'Arquivar'}
                    </button>
                  )}
                </div>
              </div>

              <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Questões da avaliação</h2>
                    <p className="text-sm text-slate-600">
                      Composição que será usada para answer key, tentativa online e análise pedagógica.
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    {exam.exam_questions.length} item(ns)
                  </span>
                </div>

                {exam.exam_questions.length === 0 ? (
                  <p className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                    Esta avaliação ainda não possui questões vinculadas.
                  </p>
                ) : (
                  <div className="mt-6 grid gap-4">
                    {exam.exam_questions
                      .slice()
                      .sort((a, b) => a.display_order - b.display_order)
                      .map((item) => (
                        <article key={item.id} className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                                Ordem {item.display_order}
                              </p>
                              <h3 className="mt-1 text-base font-semibold text-slate-900">
                                {item.question.statement}
                              </h3>
                            </div>
                            <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm">
                              Peso {item.weight}
                            </div>
                          </div>

                          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                            <div className="rounded-lg bg-white p-3 text-sm text-slate-700 shadow-sm">
                              <span className="block text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                                Proveniência
                              </span>
                              <span className="mt-1 block break-all font-medium text-slate-900">
                                {item.question_id}
                              </span>
                            </div>
                            <div className="rounded-lg bg-white p-3 text-sm text-slate-700 shadow-sm">
                              <span className="block text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                                Gabarito
                              </span>
                              <span className="mt-1 block font-bold text-emerald-700">
                                {String(item.question.correct_answer)}
                              </span>
                            </div>
                            <div className="rounded-lg bg-white p-3 text-sm text-slate-700 shadow-sm">
                              <span className="block text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                                Habilidades
                              </span>
                              <span className="mt-1 block font-medium text-slate-900">
                                {item.question.skills.length > 0
                                  ? item.question.skills.map((skill) => skill.code).join(', ')
                                  : 'Nenhuma'}
                              </span>
                            </div>
                          </div>
                        </article>
                      ))}
                  </div>
                )}
              </section>

              <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Estatísticas e exportações</h2>
                    <p className="text-sm text-slate-600">
                      Os resultados consolidados continuam disponíveis no mesmo domínio unificado de avaliação.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      href="/exams"
                      className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
                    >
                      Lista de avaliações
                    </Link>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Média da Turma
                    </span>
                    <p className="mt-2 text-3xl font-extrabold text-slate-900">
                      {stats.average_score.toFixed(2)}{' '}
                      <span className="text-sm font-normal text-slate-500">/ {stats.max_score.toFixed(2)}</span>
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Alunos Avaliados
                    </span>
                    <p className="mt-2 text-3xl font-extrabold text-slate-900">{stats.total_attempts}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Total de Questões
                    </span>
                    <p className="mt-2 text-3xl font-extrabold text-slate-900">
                      {stats.question_statistics.length}
                    </p>
                  </div>
                </div>

                <div className="mt-8 overflow-hidden rounded-xl border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-slate-700">Questão</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-700">Gabarito</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-700">Acertos</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-700">Erros</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-700">% Acerto</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white">
                      {stats.question_statistics.map((question) => (
                        <tr key={question.question_number}>
                          <td className="px-4 py-3 font-medium text-slate-900">Q{question.question_number}</td>
                          <td className="px-4 py-3 text-emerald-700">{question.correct_option || '-'}</td>
                          <td className="px-4 py-3 text-slate-700">{question.correct_count}</td>
                          <td className="px-4 py-3 text-slate-700">{question.incorrect_count}</td>
                          <td className="px-4 py-3 text-slate-700">{question.accuracy_percentage.toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
