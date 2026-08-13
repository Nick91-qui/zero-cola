'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  downloadTemplatePdf,
  downloadTemplatePreview,
  getTemplate,
  OMRTemplate,
  uploadScan,
  uploadScanBatch,
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
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchResult, setBatchResult] = useState<{
    source_filename: string;
    total_pages: number;
    scans: { id: string; student_code: string | null; status: string }[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [batchBusy, setBatchBusy] = useState(false);

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
        throw new Error('Informe um código de aluno com 5 dígitos');
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

  const handleUploadBatch = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!batchFile) {
      setError('Selecione um arquivo PDF ou imagem para processamento em lote');
      return;
    }
    setBatchBusy(true);
    try {
      const result = await uploadScanBatch(templateId, batchFile);
      setBatchResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha no upload em lote');
    } finally {
      setBatchBusy(false);
    }
  };

  return (
    <div className="space-y-8">
      <Link href="/omr" className="text-sm font-medium text-emerald-700 hover:underline">
        ← Voltar para Gabaritos
      </Link>

      {!template ? (
        <p className="text-sm text-slate-500">{error || 'Carregando gabarito...'}</p>
      ) : (
        <>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">
                {template.title || `Gabarito OMR ${template.layout_version}`}
              </h1>
              <p className="mt-1 text-sm text-slate-600">
                {template.total_questions} questões · Layout: {template.layout_version}
              </p>
            </div>
            {template.exam_id && (
              <Link
                href={`/exams/${template.exam_id}`}
                className="inline-flex items-center gap-1.5 rounded-md bg-emerald-100 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-200"
              >
                Ver Avaliação & Relatórios →
              </Link>
            )}
          </div>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-base font-semibold text-slate-900">1. Gerar folha de resposta</h2>
                <p className="mt-1 text-xs text-slate-500">
                  Gere o PDF pronto para impressão com QR code e código do aluno.
                </p>
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Código do Aluno (5 dígitos)
                  <input
                    value={studentCode}
                    onChange={(e) => setStudentCode(e.target.value)}
                    maxLength={5}
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none"
                    placeholder="10234"
                  />
                </label>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleDownloadPdf}
                    className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-600 disabled:bg-emerald-400"
                  >
                    Baixar PDF da Folha
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleDownloadPreview}
                    className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
                  >
                    Baixar Preview PNG
                  </button>
                </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-base font-semibold text-slate-900">2. Enviar imagem e corrigir (OMR)</h2>
                <p className="mt-1 text-xs text-slate-500">
                  Faça o upload do cartão-resposta (JPG ou PNG) preenchido pelo aluno.
                </p>
                <form onSubmit={handleUpload} className="mt-4 space-y-4">
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                  />
                  <button
                    type="submit"
                    disabled={busy || !file}
                    className="rounded-md bg-slate-900 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-slate-800 disabled:bg-slate-400"
                  >
                    {busy ? 'Processando imagem...' : 'Enviar e Corrigir'}
                  </button>
                </form>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-base font-semibold text-slate-900">
                  3. Processar lote PDF multipágina
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Envie um PDF com uma página por aluno ou uma imagem única para gerar um scan por página.
                </p>
                <form onSubmit={handleUploadBatch} className="mt-4 space-y-4">
                  <label className="block text-sm font-medium text-slate-700">
                    Arquivo PDF ou imagem
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                      onChange={(e) => setBatchFile(e.target.files?.[0] || null)}
                      className="mt-1.5 block w-full text-sm text-slate-600 file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={batchBusy || !batchFile}
                    className="rounded-md border border-emerald-700 bg-emerald-50 px-5 py-2.5 text-sm font-medium text-emerald-800 shadow-sm hover:bg-emerald-100 disabled:bg-slate-100 disabled:text-slate-400"
                  >
                    {batchBusy ? 'Processando lote...' : 'Enviar PDF / Lote'}
                  </button>
                </form>

                {batchResult && (
                  <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
                    <p className="font-semibold">
                      {batchResult.total_pages} página(s) processada(s) em {batchResult.source_filename}
                    </p>
                    <ul className="mt-2 space-y-1 text-xs">
                      {batchResult.scans.map((scan, index) => (
                        <li key={scan.id}>
                          Página {index + 1}: {scan.student_code || 'sem código'} · {scan.status}{' '}
                          <Link href={`/omr/scans/${scan.id}`} className="font-semibold underline">
                            abrir scan
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
          </section>
        </>
      )}
    </div>
  );
}
