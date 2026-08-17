'use client';

import { FormEvent, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { createTemplate, OMR_LAYOUT_OPTIONS } from '@/lib/omr';

const OPTIONS = ['A', 'B', 'C', 'D', 'E'] as const;

export default function NewOmrTemplatePage() {
  const router = useRouter();
  type LayoutVersion = (typeof OMR_LAYOUT_OPTIONS)[number]['value'];
  const [title, setTitle] = useState('');
  const [layoutVersion, setLayoutVersion] = useState<LayoutVersion>(OMR_LAYOUT_OPTIONS[0].value);
  const [totalQuestions, setTotalQuestions] = useState<number>(OMR_LAYOUT_OPTIONS[0].totalQuestions);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const questionNumbers = useMemo(
    () => Array.from({ length: totalQuestions }, (_, i) => i + 1),
    [totalQuestions],
  );

  const handleLayoutChange = (value: LayoutVersion) => {
    setLayoutVersion(value);
    const nextTotal = OMR_LAYOUT_OPTIONS.find((option) => option.value === value)?.totalQuestions ?? 10;
    setTotalQuestions(nextTotal);
    setAnswers({});
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Por favor, informe o título do gabarito/avaliação.');
      return;
    }

    const missing = questionNumbers.filter((n) => !answers[String(n)]);
    if (missing.length > 0) {
      setError(`Defina a resposta correta das questões: ${missing.slice(0, 8).join(', ')}${missing.length > 8 ? '...' : ''}`);
      return;
    }

    setSaving(true);
    try {
      const template = await createTemplate({
        title: title.trim(),
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
    <div className="space-y-8">
      <div>
        <Link href="/omr" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Voltar para Gabaritos
        </Link>
        <h1 className="mt-4 text-3xl font-bold text-slate-900">Novo Gabarito OMR</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Informe o título da avaliação, selecione a estrutura de questões e defina o gabarito.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-base font-semibold text-slate-900">Informações Principais</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Título / Nome do Gabarito <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ex: Prova de Química – Ligações Químicas – 2ª Série A"
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Modelo de Folha (Layout)</label>
              <select
                value={layoutVersion}
                onChange={(e) => handleLayoutChange(e.target.value as LayoutVersion)}
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                {OMR_LAYOUT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value} ({option.label})
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-slate-500">
                Layouts disponíveis de 10 a 100 questões, em passos de 10.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Chave de Respostas (Gabarito Oficial)</h2>
          <p className="mb-4 text-xs text-slate-500">Selecione a alternativa correta para cada questão.</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-5">
            {questionNumbers.map((num) => (
              <label key={num} className="text-sm font-medium text-slate-700">
                Questão {num}
                <select
                  value={answers[String(num)] || ''}
                  onChange={(e) => setAnswers((prev) => ({ ...prev, [String(num)]: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
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

        <div className="flex justify-end gap-3">
          <Link
            href="/omr"
            className="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-emerald-700 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-600 disabled:bg-emerald-400"
          >
            {saving ? 'Salvando...' : 'Criar e Gerar Gabarito'}
          </button>
        </div>
      </form>
    </div>
  );
}
