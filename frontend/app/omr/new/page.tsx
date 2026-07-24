'use client';

import { FormEvent, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { createTemplate } from '@/lib/omr';

const OPTIONS = ['A', 'B', 'C', 'D', 'E'] as const;

export default function NewOmrTemplatePage() {
  const router = useRouter();
  const [layoutVersion, setLayoutVersion] = useState('v1_std_20q');
  const [totalQuestions, setTotalQuestions] = useState(20);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const questionNumbers = useMemo(
    () => Array.from({ length: totalQuestions }, (_, i) => i + 1),
    [totalQuestions],
  );

  const handleLayoutChange = (value: string) => {
    setLayoutVersion(value);
    const nextTotal = value === 'v1_std_50q' ? 50 : 20;
    setTotalQuestions(nextTotal);
    setAnswers({});
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const missing = questionNumbers.filter((n) => !answers[String(n)]);
    if (missing.length > 0) {
      setError(`Defina a resposta correta das questões: ${missing.slice(0, 8).join(', ')}${missing.length > 8 ? '...' : ''}`);
      return;
    }

    setSaving(true);
    try {
      const template = await createTemplate({
        layout_version: layoutVersion,
        total_questions: totalQuestions,
        options_per_question: 5,
        correct_answers: answers,
      });
      router.push(`/omr/${template.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar gabarito');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <main className="mx-auto max-w-4xl px-4 py-10">
          <Link href="/omr" className="text-sm text-emerald-700 hover:underline">
            ← Voltar
          </Link>
          <h1 className="mt-4 text-3xl font-semibold text-slate-900">Novo gabarito OMR</h1>
          <p className="mt-2 text-slate-600">
            Modo avulso: informe o layout e a chave de respostas.
          </p>

          {error && (
            <div className="mt-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-8">
            <section className="rounded border border-slate-200 bg-white p-5">
              <label className="block text-sm font-medium text-slate-700">Layout</label>
              <select
                value={layoutVersion}
                onChange={(e) => handleLayoutChange(e.target.value)}
                className="mt-2 w-full rounded border border-slate-300 px-3 py-2"
              >
                <option value="v1_std_20q">v1_std_20q (20 questões)</option>
                <option value="v1_std_50q">v1_std_50q (50 questões)</option>
              </select>
            </section>

            <section className="rounded border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-medium text-slate-900">Chave de respostas</h2>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-5">
                {questionNumbers.map((num) => (
                  <label key={num} className="text-sm text-slate-700">
                    Q{num}
                    <select
                      value={answers[String(num)] || ''}
                      onChange={(e) =>
                        setAnswers((prev) => ({ ...prev, [String(num)]: e.target.value }))
                      }
                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                      required
                    >
                      <option value="">—</option>
                      {OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
            </section>

            <button
              type="submit"
              disabled={saving}
              className="rounded bg-emerald-700 px-5 py-2.5 font-medium text-white hover:bg-emerald-600 disabled:bg-emerald-400"
            >
              {saving ? 'Salvando...' : 'Criar gabarito'}
            </button>
          </form>
        </main>
      </div>
    </ProtectedRoute>
  );
}
