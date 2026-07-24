'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import {
  downloadTemplatePdf,
  downloadTemplatePreview,
  getTemplate,
  OMRTemplate,
  uploadScan,
} from '@/lib/omr';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function OmrTemplateDetailPage() {
  const params = useParams<{ templateId: string }>();
  const router = useRouter();
  const templateId = params.templateId;

  const [template, setTemplate] = useState<OMRTemplate | null>(null);
  const [studentCode, setStudentCode] = useState('10234');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await getTemplate(templateId);
        if (active) setTemplate(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Template não encontrado');
      }
    })();
    return () => {
      active = false;
    };
  }, [templateId]);

  const handleDownloadPdf = async () => {
    setError(null);
    setBusy(true);
    try {
      if (!/^\d{5}$/.test(studentCode)) {
        throw new Error('Informe um student_code com 5 dígitos');
      }
      const blob = await downloadTemplatePdf(templateId, studentCode);
      downloadBlob(blob, `gabarito-${studentCode}.pdf`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao baixar PDF');
    } finally {
      setBusy(false);
    }
  };

  const handleDownloadPreview = async () => {
    setError(null);
    setBusy(true);
    try {
      const blob = await downloadTemplatePreview(templateId, studentCode);
      downloadBlob(blob, `preview-${studentCode}.png`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao baixar preview');
    } finally {
      setBusy(false);
    }
  };

  const handleUpload = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError('Selecione uma imagem JPG/PNG');
      return;
    }
    setBusy(true);
    try {
      const scan = await uploadScan(templateId, file);
      router.push(`/omr/scans/${scan.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha no upload');
    } finally {
      setBusy(false);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <main className="mx-auto max-w-3xl px-4 py-10">
          <Link href="/omr" className="text-sm text-emerald-700 hover:underline">
            ← Gabaritos
          </Link>

          {!template ? (
            <p className="mt-6 text-slate-500">{error || 'Carregando...'}</p>
          ) : (
            <>
              <h1 className="mt-4 text-3xl font-semibold text-slate-900">
                {template.layout_version}
              </h1>
              <p className="mt-2 text-slate-600">
                {template.total_questions} questões · ID {template.id}
              </p>

              {error && (
                <div className="mt-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-red-700">
                  {error}
                </div>
              )}

              <section className="mt-8 rounded border border-slate-200 bg-white p-5">
                <h2 className="text-lg font-medium text-slate-900">1. Gerar folha</h2>
                <p className="mt-1 text-sm text-slate-500">
                  PDF para impressão ou PNG de calibração (mesmo espaço do motor OMR).
                </p>
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Código do aluno (5 dígitos)
                  <input
                    value={studentCode}
                    onChange={(e) => setStudentCode(e.target.value)}
                    maxLength={5}
                    className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                    placeholder="10234"
                  />
                </label>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleDownloadPdf}
                    className="rounded bg-emerald-700 px-4 py-2 text-white hover:bg-emerald-600 disabled:bg-emerald-400"
                  >
                    Baixar PDF
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleDownloadPreview}
                    className="rounded border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                  >
                    Baixar preview PNG
                  </button>
                </div>
              </section>

              <section className="mt-6 rounded border border-slate-200 bg-white p-5">
                <h2 className="text-lg font-medium text-slate-900">2. Corrigir por imagem</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Envie JPG/JPEG/PNG de uma folha preenchida (uma imagem por vez).
                </p>
                <form onSubmit={handleUpload} className="mt-4 space-y-4">
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-slate-600"
                  />
                  <button
                    type="submit"
                    disabled={busy || !file}
                    className="rounded bg-slate-900 px-4 py-2 text-white hover:bg-slate-700 disabled:bg-slate-400"
                  >
                    {busy ? 'Processando...' : 'Enviar e corrigir'}
                  </button>
                </form>
              </section>
            </>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
