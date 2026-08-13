'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { confirmScan, getScan, OMRScan, updateScan } from '@/lib/omr';

const OPTIONS = ['A', 'B', 'C', 'D', 'E', ''] as const;

export default function OmrScanReviewPage() {
  const params = useParams<{ scanId: string }>();
  const scanId = params.scanId;

  const [scan, setScan] = useState<OMRScan | null>(null);
  const [studentCode, setStudentCode] = useState('');
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await getScan(scanId);
        if (!active) return;
        setScan(data);
        setStudentCode(data.student_code || '');
        setAnswers(data.detected_answers || {});
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Scan não encontrado');
      }
    })();
    return () => {
      active = false;
    };
  }, [scanId]);

  const questionKeys = useMemo(() => {
    const keys = Object.keys(answers);
    if (keys.length === 0) return Array.from({ length: 20 }, (_, i) => String(i + 1));
    return keys.sort((a, b) => Number(a) - Number(b));
  }, [answers]);

  const handleSave = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateScan(scanId, {
        student_code: studentCode || undefined,
        detected_answers: answers,
      });
      setScan(updated);
      setAnswers(updated.detected_answers || {});
      setStudentCode(updated.student_code || '');
      setMessage('Correção atualizada.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar');
    } finally {
      setBusy(false);
    }
  };

  const handleConfirm = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const grade = await confirmScan(scanId);
      setMessage(`Nota confirmada: ${grade.score} (grade ${grade.id})`);
      const refreshed = await getScan(scanId);
      setScan(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao confirmar');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-8">
      <Link href="/omr" className="text-sm font-medium text-emerald-700 hover:underline">
        ← Gabaritos
      </Link>

      {!scan ? (
        <p className="text-slate-500">{error || 'Carregando scan...'}</p>
      ) : (
        <>
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Revisão OMR</h1>
            <p className="mt-2 text-slate-600">
              Status: <strong>{scan.status}</strong>
              {scan.score != null ? ` · Score: ${scan.score}` : ''}
            </p>
            {scan.error_message && <p className="mt-2 text-sm text-amber-700">{scan.error_message}</p>}
          </div>

          {error && (
            <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-red-700">{error}</div>
          )}
          {message && (
            <div className="rounded border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800">
              {message}
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-6">
            <section className="rounded border border-slate-200 bg-white p-5">
                  <label className="block text-sm font-medium text-slate-700">
                    Código do aluno
                    <input
                      value={studentCode}
                      onChange={(e) => setStudentCode(e.target.value)}
                      maxLength={5}
                      className="mt-1 w-full max-w-xs rounded border border-slate-300 px-3 py-2"
                    />
                  </label>
                  <p className="mt-2 text-xs text-slate-500">
                    Student ID resolvido: {scan.student_id || 'não associado'}
                  </p>
            </section>

            <section className="rounded border border-slate-200 bg-white p-5">
                  <h2 className="text-lg font-medium text-slate-900">Respostas detectadas</h2>
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-5">
                    {questionKeys.map((key) => (
                      <label key={key} className="text-sm text-slate-700">
                        Q{key}
                        <select
                          value={answers[key] ?? ''}
                          onChange={(e) =>
                            setAnswers((prev) => ({
                              ...prev,
                              [key]: e.target.value || null,
                            }))
                          }
                          className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                        >
                          {OPTIONS.map((opt) => (
                            <option key={opt || 'empty'} value={opt}>
                              {opt || '—'}
                            </option>
                          ))}
                        </select>
                      </label>
                    ))}
                  </div>
            </section>

            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={busy}
                className="rounded border border-slate-300 bg-white px-4 py-2 text-slate-800 hover:bg-slate-100 disabled:opacity-50"
              >
                Salvar ajustes
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={handleConfirm}
                className="rounded bg-emerald-700 px-4 py-2 text-white hover:bg-emerald-600 disabled:bg-emerald-400"
              >
                Confirmar nota
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  );
}
