'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { listClasses, type ClassSummary } from '@/lib/classes';
import {
  archiveExam,
  exportExamOmrPackage,
  exportExamPreviewPdf,
  getExam,
  getExamStatistics,
  publishExam,
  updateExam,
  returnExamToDraft,
  type ExamDetail,
  type ExamStatistics,
} from '@/lib/exams';

function formatClassNames(classIds: string[] | undefined, classes: ClassSummary[]) {
  if (!classIds || classIds.length === 0) return 'Geral';

  const classNameById = new Map(classes.map((classItem) => [classItem.id, classItem.name]));
  const labels = classIds.map((classId) => classNameById.get(classId) ?? classId);

  if (labels.length <= 3) {
    return labels.join(', ');
  }

  return `${labels.slice(0, 3).join(', ')} + ${labels.length - 3}`;
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
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [selectedClassIds, setSelectedClassIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [savingClasses, setSavingClasses] = useState(false);
  const [downloadingOmr, setDownloadingOmr] = useState(false);
  const [downloadingPreview, setDownloadingPreview] = useState(false);

  const loadExam = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [examData, classData] = await Promise.all([
        getExam(examId),
        listClasses().catch(() => []),
      ]);
      setExam(examData);
      setClasses(classData);
      setSelectedClassIds(examData.class_ids ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar avaliação');
    } finally {
      setLoading(false);
    }
  }, [examId]);

  const loadStatistics = useCallback(async () => {
    setLoadingStats(true);
    setStatsError(null);

    try {
      const statsData = await getExamStatistics(examId);
      setStats(statsData);
    } catch (err) {
      setStats(null);
      setStatsError(err instanceof Error ? err.message : 'Falha ao carregar estatísticas');
    } finally {
      setLoadingStats(false);
    }
  }, [examId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- data fetch hydrates local exam state on mount
    void loadExam();
    void loadStatistics();
  }, [loadExam, loadStatistics]);

  const handleAction = async (action: 'publish' | 'draft' | 'archive') => {
    setBusyAction(action);
    setError(null);
    try {
      await (
        action === 'publish'
          ? publishExam(examId)
          : action === 'draft'
            ? returnExamToDraft(examId)
            : archiveExam(examId)
      );
      await loadExam();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar status da avaliação');
    } finally {
      setBusyAction(null);
    }
  };

  const handleToggleClass = (classId: string) => {
    setSelectedClassIds((current) =>
      current.includes(classId) ? current.filter((id) => id !== classId) : [...current, classId],
    );
  };

  const handleSaveClasses = async () => {
    setSavingClasses(true);
    setError(null);

    try {
      await updateExam(examId, { class_ids: selectedClassIds });
      await loadExam();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar turmas da avaliação');
    } finally {
      setSavingClasses(false);
    }
  };

  const handleDownloadOmrPackage = async () => {
    setDownloadingOmr(true);
    setError(null);

    try {
      const blob = await exportExamOmrPackage(examId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `folhas_omr_${examId}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao gerar folhas OMR');
    } finally {
      setDownloadingOmr(false);
    }
  };

  const handleDownloadPreview = async () => {
    setDownloadingPreview(true);
    setError(null);

    try {
      const blob = await exportExamPreviewPdf(examId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `previsualizacao_${examId}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao gerar pré-visualização');
    } finally {
      setDownloadingPreview(false);
    }
  };

  const classCountLabel = selectedClassIds.length === 1 ? '1 turma' : `${selectedClassIds.length} turmas`;

  return (
    <div className="space-y-8">
      <Link href="/exams" className="text-sm font-medium text-emerald-700 hover:underline">
        ← Voltar para Avaliações
      </Link>

      {loading ? (
        <p className="py-12 text-center text-sm text-slate-500">Carregando avaliação...</p>
      ) : error || !exam ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error || 'Avaliação não encontrada.'}
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:flex-row lg:items-start lg:justify-between">
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
                        {classCountLabel}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {formatClassNames(exam.class_ids, classes)}
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
                  <button
                    type="button"
                    onClick={handleDownloadPreview}
                    disabled={downloadingPreview}
                    className="rounded-md border border-sky-200 bg-sky-50 px-4 py-2 text-sm font-semibold text-sky-800 shadow-sm hover:bg-sky-100 disabled:text-slate-400"
                  >
                    {downloadingPreview ? 'Gerando preview...' : 'Pré-visualizar prova'}
                  </button>
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
                  <button
                    type="button"
                    onClick={handleDownloadOmrPackage}
                    disabled={downloadingOmr}
                    className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800 shadow-sm hover:bg-emerald-100 disabled:text-slate-400"
                  >
                    {downloadingOmr ? 'Gerando OMR...' : 'Baixar folhas OMR'}
                  </button>
                </div>
              </div>

          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Turmas vinculadas</h2>
                    <p className="text-sm text-slate-600">
                      Ajuste as turmas que podem acessar esta avaliação. A publicação continua separada da atribuição.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void handleSaveClasses()}
                    disabled={savingClasses}
                    className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-600 disabled:bg-slate-300"
                  >
                    {savingClasses ? 'Salvando...' : 'Salvar turmas'}
                  </button>
                </div>

                {classes.length === 0 ? (
                  <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
                    Nenhuma turma disponível para associação.
                  </p>
                ) : (
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    {classes.map((classItem) => {
                      const checked = selectedClassIds.includes(classItem.id);
                      return (
                        <label
                          key={classItem.id}
                          className={[
                            'flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition',
                            checked
                              ? 'border-emerald-500 bg-emerald-50'
                              : 'border-slate-200 bg-white hover:border-emerald-300',
                          ].join(' ')}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => handleToggleClass(classItem.id)}
                            className="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                          />
                          <span>
                            <span className="block font-semibold text-slate-900">{classItem.name}</span>
                            <span className="block text-xs text-slate-500">
                              {classItem.academic_period || 'Sem período'} · {classItem.student_count} aluno(s)
                            </span>
                          </span>
                        </label>
                      );
                    })}
                  </div>
                )}
              </section>

          <section
            className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            data-testid="exam-preview-section"
          >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Pré-visualização da prova</h2>
                    <p className="text-sm text-slate-600">
                      Exibição da composição sem gabarito para revisão antes da publicação.
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    {exam.exam_questions.length} questão(ões)
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

                          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-2">
                            <div className="rounded-lg bg-white p-3 text-sm text-slate-700 shadow-sm">
                              <span className="block text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                                Alternativas
                              </span>
                              <div className="mt-2 space-y-2">
                                {item.question.options &&
                                Object.keys(item.question.options).length > 0 ? (
                                  Object.entries(item.question.options)
                                    .sort(([left], [right]) => left.localeCompare(right))
                                    .map(([label, value]) => (
                                      <div
                                        key={label}
                                        className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
                                      >
                                        <span className="font-semibold text-slate-900">{label}.</span>{' '}
                                        {value}
                                      </div>
                                    ))
                                ) : (
                                  <div className="rounded-md border border-dashed border-slate-300 bg-white px-3 py-2 text-sm text-slate-500">
                                    Sem alternativas cadastradas.
                                  </div>
                                )}
                              </div>
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

                {loadingStats ? (
                  <p className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                    Carregando estatísticas por questão...
                  </p>
                ) : statsError ? (
                  <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                    <p>Não foi possível carregar as estatísticas por questão agora.</p>
                    <button
                      type="button"
                      onClick={() => void loadStatistics()}
                      className="mt-3 rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 shadow-sm hover:bg-amber-100"
                    >
                      Tentar novamente
                    </button>
                  </div>
                ) : stats ? (
                  <>
                    <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
                        <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                          Média da Turma
                        </span>
                        <p className="mt-2 text-3xl font-extrabold text-slate-900">
                          {stats.average_score.toFixed(2)}{' '}
                          <span className="text-sm font-normal text-slate-500">
                            / {stats.max_score.toFixed(2)}
                          </span>
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
                              <td className="px-4 py-3 font-medium text-slate-900">
                                Q{question.question_number}
                              </td>
                              <td className="px-4 py-3 text-emerald-700">{question.correct_option || '-'}</td>
                              <td className="px-4 py-3 text-slate-700">{question.correct_count}</td>
                              <td className="px-4 py-3 text-slate-700">{question.incorrect_count}</td>
                              <td className="px-4 py-3 text-slate-700">
                                {question.accuracy_percentage.toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : null}
              </section>
        </>
      )}
    </div>
  );
}
