'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { Exam, exportExamPdf, exportExamXlsx, listExams, publishExam } from '@/lib/exams';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function ExamsListPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [exams, setExams] = useState<Exam[]>([]);
  const [classFilter, setClassFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [publishingId, setPublishingId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setError(null);
        setLoading(true);
        const data = await listExams(classFilter);
        if (active) {
          setExams(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar avaliações');
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
  }, [classFilter]);

  const handleExportPdf = async (examId: string, title: string) => {
    setDownloadingId(examId);
    try {
      const blob = await exportExamPdf(examId);
      downloadBlob(blob, `relatorio_${title.replace(/\s+/g, '_')}.pdf`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Falha ao exportar PDF');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleExportXlsx = async (examId: string, title: string) => {
    setDownloadingId(examId);
    try {
      const blob = await exportExamXlsx(examId);
      downloadBlob(blob, `relatorio_${title.replace(/\s+/g, '_')}.xlsx`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Falha ao exportar XLSX');
    } finally {
      setDownloadingId(null);
    }
  };

  const handlePublish = async (examId: string) => {
    setPublishingId(examId);
    try {
      await publishExam(examId);
      const data = await listExams(classFilter);
      setExams(data);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Falha ao publicar avaliação');
    } finally {
      setPublishingId(null);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-lg font-bold text-slate-900">
                COLA-ZERO
              </Link>
              <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                Avaliações & Relatórios
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span>{user?.email}</span>
              <button
                type="button"
                onClick={async () => {
                  await logout();
                  router.push('/auth/login');
                }}
                className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
              >
                Sair
              </button>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-5xl px-4 py-10">
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Gerenciamento de Avaliações</h1>
              <p className="mt-1 text-sm text-slate-600">
                Acompanhe o desempenho por prova, análise por questão e exporte relatórios consolidados em PDF e XLSX.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href="/exams/new"
                className="inline-flex items-center justify-center rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-600"
              >
                + Criar Prova Online
              </Link>
              <Link
                href="/questions"
                className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
              >
                Banco de Questões
              </Link>
              <Link
                href="/omr/new"
                className="inline-flex items-center justify-center rounded-md border border-emerald-700 bg-white px-4 py-2.5 text-sm font-medium text-emerald-700 shadow-sm hover:bg-emerald-50"
              >
                + Criar Gabarito OMR
              </Link>
            </div>
          </div>

          <div className="mb-6 flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <label className="text-sm font-medium text-slate-700">Filtrar por Turma:</label>
            <input
              type="text"
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              placeholder="Ex: 301, 2ª Série A"
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
            />
            {classFilter && (
              <button
                type="button"
                onClick={() => setClassFilter('')}
                className="text-xs text-slate-500 hover:text-slate-700 underline"
              >
                Limpar filtro
              </button>
            )}
          </div>

          {error && (
            <div className="mb-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {loading ? (
            <p className="py-12 text-center text-sm text-slate-500">Carregando avaliações...</p>
          ) : exams.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center">
              <h3 className="text-lg font-medium text-slate-900">Nenhuma avaliação encontrada</h3>
              <p className="mt-1 text-sm text-slate-500">
                As avaliações são criadas automaticamente ao cadastrar um novo gabarito OMR.
              </p>
              <Link
                href="/omr/new"
                className="mt-4 inline-flex items-center rounded-md bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
              >
                Criar Gabarito
              </Link>
            </div>
          ) : (
            <div className="grid gap-4">
              {exams.map((exam) => (
                <div
                  key={exam.id}
                  className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-600 sm:flex-row sm:items-center"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold text-slate-900">{exam.title}</h2>
                      {exam.class_id && (
                        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                          Turma {exam.class_id}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">
                      {exam.total_questions} questões · Nota Máxima: {exam.max_score} · Criado em{' '}
                      {new Date(exam.created_at).toLocaleDateString('pt-BR')}
                    </p>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center gap-2 sm:mt-0">
                    <Link
                      href={`/exams/${exam.id}`}
                      className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
                    >
                      Estatísticas por Questão →
                    </Link>
                    {exam.status === 'draft' && (
                      <button
                        type="button"
                        disabled={publishingId === exam.id}
                        onClick={() => void handlePublish(exam.id)}
                        className="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-600 disabled:bg-slate-300"
                      >
                        {publishingId === exam.id ? 'Publicando...' : 'Publicar'}
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={downloadingId === exam.id}
                      onClick={() => handleExportPdf(exam.id, exam.title)}
                      className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                    >
                      Relatório PDF
                    </button>
                    <button
                      type="button"
                      disabled={downloadingId === exam.id}
                      onClick={() => handleExportXlsx(exam.id, exam.title)}
                      className="rounded-md border border-emerald-700 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800 hover:bg-emerald-100"
                    >
                      Planilha XLSX
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
