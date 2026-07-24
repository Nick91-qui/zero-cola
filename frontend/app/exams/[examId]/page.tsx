'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { ExamStatistics, exportExamPdf, exportExamXlsx, getExamStatistics } from '@/lib/exams';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function ExamDetailStatisticsPage() {
  const params = useParams<{ examId: string }>();
  const examId = params.examId;

  const [stats, setStats] = useState<ExamStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await getExamStatistics(examId);
        if (active) setStats(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Falha ao carregar estatísticas');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [examId]);

  const handleExportPdf = async () => {
    if (!stats) return;
    setBusy(true);
    try {
      const blob = await exportExamPdf(examId);
      downloadBlob(blob, `relatorio_${stats.exam_title.replace(/\s+/g, '_')}.pdf`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao baixar PDF');
    } finally {
      setBusy(false);
    }
  };

  const handleExportXlsx = async () => {
    if (!stats) return;
    setBusy(true);
    try {
      const blob = await exportExamXlsx(examId);
      downloadBlob(blob, `relatorio_${stats.exam_title.replace(/\s+/g, '_')}.xlsx`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao baixar XLSX');
    } finally {
      setBusy(false);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <main className="mx-auto max-w-5xl px-4 py-10">
          <Link href="/exams" className="text-sm font-medium text-emerald-700 hover:underline">
            ← Voltar para Avaliações
          </Link>

          {loading ? (
            <p className="mt-8 text-center text-sm text-slate-500">Carregando estatísticas da avaliação...</p>
          ) : error || !stats ? (
            <div className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error || 'Estatísticas não encontradas.'}
            </div>
          ) : (
            <>
              <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-slate-900">{stats.exam_title}</h1>
                  <p className="mt-1 text-sm text-slate-600">
                    Turma: <span className="font-semibold text-slate-900">{stats.class_id || 'Geral'}</span> · Total de Alunos Avaliados:{' '}
                    <span className="font-semibold text-slate-900">{stats.total_attempts}</span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleExportPdf}
                    className="rounded-md border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
                  >
                    Baixar PDF
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleExportXlsx}
                    className="rounded-md bg-emerald-700 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-600"
                  >
                    Exportar Planilha Excel
                  </button>
                </div>
              </div>

              {/* Cards Resumo */}
              <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Média da Turma</span>
                  <p className="mt-2 text-3xl font-extrabold text-slate-900">
                    {stats.average_score.toFixed(2)}{' '}
                    <span className="text-sm font-normal text-slate-500">/ {stats.max_score.toFixed(2)}</span>
                  </p>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Alunos Avaliados</span>
                  <p className="mt-2 text-3xl font-extrabold text-slate-900">{stats.total_attempts}</p>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total de Questões</span>
                  <p className="mt-2 text-3xl font-extrabold text-slate-900">{stats.question_statistics.length}</p>
                </div>
              </div>

              {/* Tabela de Análise por Questão */}
              <section className="mt-8 rounded-lg border border-slate-200 bg-white shadow-sm overflow-hidden">
                <div className="border-b border-slate-200 px-6 py-4">
                  <h2 className="text-lg font-bold text-slate-900">Análise Pedagógica de Desempenho por Questão</h2>
                  <p className="text-xs text-slate-500">Percentual de acertos, erros e mapeamento de habilidades curriculares.</p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-700">
                    <thead className="bg-slate-100 text-xs font-semibold text-slate-700 uppercase tracking-wider">
                      <tr>
                        <th className="px-6 py-3">Questão</th>
                        <th className="px-4 py-3 text-center">Gabarito</th>
                        <th className="px-4 py-3 text-center">Respostas</th>
                        <th className="px-4 py-3 text-center">Acertos</th>
                        <th className="px-4 py-3 text-center">Erros</th>
                        <th className="px-6 py-3 text-center">% Acerto</th>
                        <th className="px-6 py-3">Habilidades BNCC</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {stats.question_statistics.map((q) => (
                        <tr key={q.question_number} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-semibold text-slate-900">Q{q.question_number}</td>
                          <td className="px-4 py-4 text-center font-bold text-emerald-800 bg-emerald-50 rounded">
                            {q.correct_option || '-'}
                          </td>
                          <td className="px-4 py-4 text-center text-slate-600">{q.total_responses}</td>
                          <td className="px-4 py-4 text-center font-medium text-emerald-700">{q.correct_count}</td>
                          <td className="px-4 py-4 text-center font-medium text-red-600">{q.incorrect_count}</td>
                          <td className="px-6 py-4 text-center">
                            <div className="flex items-center justify-center gap-2">
                              <div className="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                                <div
                                  className="bg-emerald-600 h-2 rounded-full"
                                  style={{ width: `${q.accuracy_percentage}%` }}
                                />
                              </div>
                              <span className="font-semibold text-slate-900">{q.accuracy_percentage.toFixed(1)}%</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-600">
                            {q.skills.length === 0 ? (
                              <span className="text-slate-400 italic">Nenhuma vinculada</span>
                            ) : (
                              <div className="flex flex-wrap gap-1">
                                {q.skills.map((s) => (
                                  <span key={s.id} className="rounded bg-blue-100 px-2 py-0.5 font-medium text-blue-800" title={s.description}>
                                    {s.code}
                                  </span>
                                ))}
                              </div>
                            )}
                          </td>
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
