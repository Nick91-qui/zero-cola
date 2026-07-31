'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { createExam, type ExamCreatePayload } from '@/lib/exams';
import { listClasses, type ClassSummary } from '@/lib/classes';
import { listSkills, type SkillSummary } from '@/lib/skills';

const OPTION_KEYS = ['A', 'B', 'C', 'D', 'E'] as const;

type QuestionDraft = {
  id: string;
  statement: string;
  correct_answer: string;
  options: Record<string, string>;
  skill_ids: string[];
};

function createQuestionDraft(): QuestionDraft {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    statement: '',
    correct_answer: 'A',
    options: {
      A: '',
      B: '',
      C: '',
      D: '',
      E: '',
    },
    skill_ids: [],
  };
}

function normalizeOptions(options: Record<string, string>) {
  const cleaned = Object.fromEntries(
    Object.entries(options)
      .map(([key, value]) => [key, value.trim()])
      .filter(([, value]) => value.length > 0),
  );
  return Object.keys(cleaned).length > 0 ? cleaned : null;
}

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
  const [questions, setQuestions] = useState<QuestionDraft[]>([createQuestionDraft()]);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [loadingReferences, setLoadingReferences] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setError(null);
        setLoadingReferences(true);
        const [classData, skillData] = await Promise.all([listClasses(), listSkills()]);
        if (!active) return;
        setClasses(classData);
        setSkills(skillData);
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

    load();
    return () => {
      active = false;
    };
  }, []);

  const questionCount = useMemo(() => questions.length, [questions.length]);

  const updateQuestion = (index: number, updater: (question: QuestionDraft) => QuestionDraft) => {
    setQuestions((current) => current.map((question, currentIndex) => {
      if (currentIndex !== index) return question;
      return updater(question);
    }));
  };

  const handleToggleClass = (classId: string) => {
    setSelectedClassIds((current) =>
      current.includes(classId)
        ? current.filter((id) => id !== classId)
        : [...current, classId],
    );
  };

  const handleToggleSkill = (questionIndex: number, skillId: string) => {
    updateQuestion(questionIndex, (question) => ({
      ...question,
      skill_ids: question.skill_ids.includes(skillId)
        ? question.skill_ids.filter((id) => id !== skillId)
        : [...question.skill_ids, skillId],
    }));
  };

  const handleAddQuestion = () => {
    setQuestions((current) => [...current, createQuestionDraft()]);
  };

  const handleRemoveQuestion = (index: number) => {
    setQuestions((current) => (current.length <= 1 ? current : current.filter((_, i) => i !== index)));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Informe o título da avaliação.');
      return;
    }

    const payloadQuestions: ExamCreatePayload['questions'] = [];

    for (const [index, question] of questions.entries()) {
      const statement = question.statement.trim();
      if (!statement) {
        setError(`A questão ${index + 1} precisa de enunciado.`);
        return;
      }

      const options = normalizeOptions(question.options);
      if (!options || Object.keys(options).length < 2) {
        setError(`A questão ${index + 1} precisa de pelo menos duas alternativas.`);
        return;
      }

      if (!options[question.correct_answer]) {
        setError(`A questão ${index + 1} precisa marcar uma alternativa correta válida.`);
        return;
      }

      payloadQuestions.push({
        display_order: index + 1,
        weight: '1.00',
        question: {
          statement,
          type: 'multiple_choice',
          options,
          correct_answer: question.correct_answer,
          skill_ids: question.skill_ids.length > 0 ? question.skill_ids : undefined,
        },
      });
    }

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
                Monte a prova, escolha turmas e publique quando estiver pronta.
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
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Título
                  <input
                    type="text"
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                    placeholder="Ex: Prova de Matemática - 2ª Série A"
                  />
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Duração total em segundos
                  <input
                    type="number"
                    min="0"
                    value={totalTimeSeconds}
                    onChange={(event) => setTotalTimeSeconds(event.target.value)}
                    className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                    placeholder="Opcional"
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

            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">Questões</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Cada questão será materializada como parte do banco reutilizável e projetada para o gabarito do exame.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleAddQuestion}
                  className="rounded-md border border-emerald-700 px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-50"
                >
                  + Adicionar questão
                </button>
              </div>

              {questions.map((question, index) => (
                <article key={question.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-base font-semibold text-slate-900">Questão {index + 1}</h3>
                      <p className="text-sm text-slate-500">Ordem de exibição {index + 1}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveQuestion(index)}
                      disabled={questions.length <= 1}
                      className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:text-slate-400"
                    >
                      Remover
                    </button>
                  </div>

                  <div className="mt-5 grid gap-4">
                    <label className="block text-sm font-medium text-slate-700">
                      Enunciado
                      <textarea
                        value={question.statement}
                        onChange={(event) =>
                          updateQuestion(index, (current) => ({
                            ...current,
                            statement: event.target.value,
                          }))
                        }
                        rows={4}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                        placeholder="Digite o enunciado da questão."
                      />
                    </label>

                    <div className="grid gap-4 md:grid-cols-2">
                      <label className="block text-sm font-medium text-slate-700">
                        Gabarito correto
                        <select
                          value={question.correct_answer}
                          onChange={(event) =>
                            updateQuestion(index, (current) => ({
                              ...current,
                              correct_answer: event.target.value,
                            }))
                          }
                          className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                        >
                          {OPTION_KEYS.map((optionKey) => (
                            <option key={optionKey} value={optionKey}>
                              {optionKey}
                            </option>
                          ))}
                        </select>
                      </label>

                      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                        <div className="text-sm font-medium text-slate-700">Alternativas</div>
                        <div className="mt-3 grid gap-3 sm:grid-cols-2">
                          {OPTION_KEYS.map((optionKey) => (
                            <label key={optionKey} className="block text-xs font-medium text-slate-600">
                              {optionKey}
                              <input
                                type="text"
                                value={question.options[optionKey]}
                                onChange={(event) =>
                                  updateQuestion(index, (current) => ({
                                    ...current,
                                    options: {
                                      ...current.options,
                                      [optionKey]: event.target.value,
                                    },
                                  }))
                                }
                                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                                placeholder={`Texto da alternativa ${optionKey}`}
                              />
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>

                    {skills.length > 0 && (
                      <div className="rounded-xl border border-slate-200 p-4">
                        <div className="text-sm font-medium text-slate-700">Habilidades vinculadas</div>
                        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                          {skills.map((skill) => {
                            const checked = question.skill_ids.includes(skill.id);
                            return (
                              <label
                                key={skill.id}
                                className={[
                                  'flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 text-sm transition',
                                  checked
                                    ? 'border-emerald-500 bg-emerald-50'
                                    : 'border-slate-200 bg-white hover:border-emerald-300',
                                ].join(' ')}
                              >
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  onChange={() => handleToggleSkill(index, skill.id)}
                                  className="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                                />
                                <span>
                                  <span className="block font-semibold text-slate-900">{skill.code}</span>
                                  <span className="block text-xs text-slate-500">{skill.description}</span>
                                </span>
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </section>

            <div className="flex flex-wrap items-center justify-end gap-3">
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
          </form>
        </main>
      </div>
    </ProtectedRoute>
  );
}
