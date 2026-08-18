'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ConfirmDialog } from '@/app/components/ConfirmDialog';
import { deleteTemplate, listTemplates, OMRTemplate } from '@/lib/omr';

export default function OmrHomePage() {
  const [templates, setTemplates] = useState<OMRTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [deletingTemplate, setDeletingTemplate] = useState<OMRTemplate | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await listTemplates();
      setTemplates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar gabaritos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleDeleteConfirm = async () => {
    if (!deletingTemplate) return;
    setIsDeleting(true);
    try {
      await deleteTemplate(deletingTemplate.id);
      setTemplates((prev) => prev.filter((t) => t.id !== deletingTemplate.id));
      setDeletingTemplate(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao excluir gabarito');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Gabaritos OMR</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Crie avaliações com folha de respostas, baixe PDF e processe cartões-resposta.
          </p>
        </div>
        <Link
          href="/omr/new"
          className="inline-flex items-center justify-center rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-600"
        >
          + Novo Gabarito
        </Link>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <p className="text-sm text-slate-500">Carregando gabaritos...</p>
        </div>
      ) : templates.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center">
          <h3 className="text-lg font-medium text-slate-900">Nenhum gabarito cadastrado</h3>
          <p className="mt-1 text-sm text-slate-500">Crie seu primeiro gabarito para gerar folhas de resposta.</p>
          <Link
            href="/omr/new"
            className="mt-4 inline-flex items-center rounded-md bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
          >
            Criar Gabarito
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-600 sm:flex-row sm:items-center"
            >
              <div className="space-y-1">
                <h2 className="text-lg font-semibold text-slate-900">
                  {template.title || `Gabarito ${template.layout_version}`}
                </h2>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
                    {template.layout_version}
                  </span>
                  <span>{template.total_questions} questões</span>
                  <span>Criado em {new Date(template.created_at).toLocaleDateString('pt-BR')}</span>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2 sm:mt-0">
                <Link
                  href={`/omr/${template.id}`}
                  className="rounded-md border border-emerald-700 px-3.5 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-50"
                >
                  Abrir Gabarito →
                </Link>
                <button
                  type="button"
                  onClick={() => setDeletingTemplate(template)}
                  className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 hover:border-red-200"
                >
                  Excluir
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={deletingTemplate !== null}
        title="Excluir gabarito?"
        message={
          deletingTemplate
            ? `Você está prestes a excluir o gabarito ${deletingTemplate.title || deletingTemplate.layout_version}.`
            : 'Você está prestes a excluir o gabarito selecionado.'
        }
        warning="As notas, provas e imagens de cartões já corrigidos referentes a este gabarito não serão apagadas do histórico dos alunos."
        confirmLabel={isDeleting ? 'Excluindo...' : 'Confirmar exclusão'}
        busy={isDeleting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeletingTemplate(null)}
      />
    </div>
  );
}
