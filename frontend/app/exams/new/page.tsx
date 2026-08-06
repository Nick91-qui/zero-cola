'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { listClasses, type ClassSummary } from '@/lib/classes';
import { createExam, type ExamCreatePayload, type Question } from '@/lib/exams';
import { listQuestions } from '@/lib/questions';
import { QuestionBankSelector, type SelectedQuestionDraft } from './question-bank-selector';

export default function NewExamPage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [totalTimeSeconds, setTotalTimeSeconds] = useState('');
  const [maxAttempts, setMaxAttempts] = useState('1');
  const [randomizationEnabled, setRandomizationEnabled] = useState(false);
  const [maxScore, setMaxScore] = useState('10.00');
  const [selectedClassIds, setSelectedClassIds] = useState<string[]>([]);
  const [selectedQuestions, setSelectedQuestions] = useState<SelectedQuestionDraft[]>([]);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadingReferences, setLoadingReferences] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setError(null);
        setLoadingReferences(true);
        const [classData, questionData] = await Promise.all([listClasses(), listQuestions()]);
        if (!active) return;
        setClasses(classData);
        setQuestions(questionData);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar referências');
        }
      } finally {
        if (active) {
          setLoadingReferences(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const questionCount = useMemo(() => selectedQuestions.length, [selectedQuestions.length]);

  const handleToggleClass = (classId: string) => {
    setSelectedClassIds((current) =>
      current.includes(classId) ? current.filter((id) => id !== classId) : [...current, classId],
    );
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Informe o título da avaliação.');
      return;
    }

    if (selectedQuestions.length === 0) {
      setError('Selecione ao menos uma questão do banco.');
      return;
    }

    const payloadQuestions: ExamCreatePayload['questions'] = selectedQuestions.map((item, index) => ({
      display_order: index + 1,
      weight: item.weight,
      question_id: item.question.id,
    }));

    setSaving(true);
    try {
      const exam = await createExam({
        title: title.trim(),
        description: description.trim() || undefined,
        class_ids: selectedClassIds,
        total_questions: payloadQuestions.length,
        total_time_seconds: totalTimeSeconds ? Number(totalTimeSeconds) : null,
        max_attempts: Number(maxAttempts) || 1,
        randomization_enabled: randomizationEnabled,
        max_score: maxScore,
        questions: payloadQuestions,
      });
      router.push(`/exams/${exam.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar avaliação');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <div>
              <Link href="/dashboard" className="text-lg font-bold text-slate-900">
                COLA-ZERO
              </Link>
              <span className="ml-3 rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                Nova avaliação
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span>{user?.email}</span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
              >
                Sair
              </button>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-6xl px-4 py-10">
          <Link href="/exams" className="text-sm font-medium text-emerald-700 hover:underline">
            ← Voltar para Avaliações
          </Link>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Criar avaliação online</h1>
              <p className="mt-1 text-sm text-slate-600">
                Selecione questões do banco, escolha turmas e publique quando estiver pronta.
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
              <span className="font-semibold text-slate-900">{questionCount}</span> questão(ões)
            </div>
          </div>

          {error && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Dados da avaliação</h2>
              <p className="mt-1 text-sm text-slate-600">
                Configure metadados, tempo limite e comportamento da tentativa online.
              </p>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Título
                  <input
                    type="text"
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Ex: Prova integradora"
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  />
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Duração total em segundos
                  <input
                    type="number"
                    min="0"
                    value={totalTimeSeconds}
                    onChange={(event) => setTotalTimeSeconds(event.target.value)}
                    placeholder="Opcional"
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  />
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Máximo de tentativas
                  <input
                    type="number"
                    min="1"
                    value={maxAttempts}
                    onChange={(event) => setMaxAttempts(event.target.value)}
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  />
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Nota máxima
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={maxScore}
                    onChange={(event) => setMaxScore(event.target.value)}
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  />
                </label>
              </div>

              <label className="mt-4 block text-sm font-medium text-slate-700">
                Descrição
                <textarea
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={3}
                  className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  placeholder="Objetivos, conteúdo e orientações."
                />
              </label>

              <label className="mt-4 flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={randomizationEnabled}
                  onChange={(event) => setRandomizationEnabled(event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                Randomizar ordem das questões por tentativa online
              </label>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">Turmas</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Vincule a avaliação às turmas que poderão acessar a prova.
                  </p>
                </div>
                {loadingReferences && <span className="text-sm text-slate-500">Carregando referências...</span>}
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {classes.length === 0 ? (
                  <p className="text-sm text-slate-500">Nenhuma turma encontrada.</p>
                ) : (
                  classes.map((classItem) => {
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
                        <div>
                          <div className="font-semibold text-slate-900">{classItem.name}</div>
                          <div className="text-xs text-slate-500">
                            {classItem.academic_period || 'Sem período informado'} · {classItem.student_count} estudante(s)
                          </div>
                        </div>
                      </label>
                    );
                  })
                )}
              </div>
            </section>

            <QuestionBankSelector
              questions={questions}
              selectedQuestions={selectedQuestions}
              onChange={setSelectedQuestions}
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <Link
                href="/questions"
                className="rounded-md border border-emerald-700 bg-white px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-50"
              >
                Abrir banco de questões
              </Link>
              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href="/exams"
                  className="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                >
                  Cancelar
                </Link>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-md bg-emerald-700 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-600 disabled:bg-emerald-400"
                >
                  {saving ? 'Salvando...' : 'Criar avaliação'}
                </button>
              </div>
            </div>
          </form>
        </main>
      </div>
    </ProtectedRoute>
  );
}
