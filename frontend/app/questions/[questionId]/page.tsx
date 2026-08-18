'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ConfirmDialog } from '@/app/components/ConfirmDialog';
import { listSkills, type SkillSummary } from '@/lib/skills';
import { deactivateQuestion, getQuestion, updateQuestion, type QuestionUpdatePayload } from '@/lib/questions';
import type { Question } from '@/lib/exams';

const OPTION_KEYS = ['A', 'B', 'C', 'D', 'E'] as const;

function emptyOptions() {
  return { A: '', B: '', C: '', D: '', E: '' };
}

export default function QuestionDetailPage() {
  const params = useParams<{ questionId: string }>();
  const questionId = params.questionId;
  const router = useRouter();

  const [question, setQuestion] = useState<Question | null>(null);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [deactivateConfirmationOpen, setDeactivateConfirmationOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statement, setStatement] = useState('');
  const [subject, setSubject] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [tags, setTags] = useState('');
  const [correctAnswer, setCorrectAnswer] = useState('A');
  const [options, setOptions] = useState<Record<string, string>>(emptyOptions());
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        const [questionData, skillData] = await Promise.all([getQuestion(questionId), listSkills()]);
        if (!active) return;
        setQuestion(questionData);
        setSkills(skillData);
        setStatement(questionData.statement);
        setSubject(questionData.subject || '');
        setDifficulty(questionData.difficulty || '');
        setTags(questionData.tags?.join(', ') || '');
        const currentOptions = questionData.options || {};
        setOptions({
          A: currentOptions.A || '',
          B: currentOptions.B || '',
          C: currentOptions.C || '',
          D: currentOptions.D || '',
          E: currentOptions.E || '',
        });
        setCorrectAnswer(typeof questionData.correct_answer === 'string' ? questionData.correct_answer : 'A');
        setSelectedSkillIds(questionData.skills.map((skill) => skill.id));
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Falha ao carregar questão');
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [questionId]);

  const selectedSkillCount = useMemo(() => selectedSkillIds.length, [selectedSkillIds.length]);

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const cleanedOptions = Object.fromEntries(
      Object.entries(options)
        .map(([key, value]) => [key, value.trim()])
        .filter(([, value]) => value.length > 0),
    );

    if (!statement.trim()) {
      setError('Informe o enunciado da questão.');
      return;
    }

    if (Object.keys(cleanedOptions).length < 2) {
      setError('Informe ao menos duas alternativas.');
      return;
    }

    if (!cleanedOptions[correctAnswer]) {
      setError('Selecione uma alternativa correta válida.');
      return;
    }

    setSaving(true);
    try {
      const payload: QuestionUpdatePayload = {
        statement: statement.trim(),
        subject: subject.trim() || null,
        difficulty: difficulty.trim() || null,
        tags: tags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
        correct_answer: correctAnswer,
        options: cleanedOptions,
        skill_ids: selectedSkillIds,
      };
      const updated = await updateQuestion(questionId, payload);
      router.replace(`/questions/${updated.id}`);
      setQuestion(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar questão');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async () => {
    setDeactivating(true);
    setError(null);
    try {
      const updated = await deactivateQuestion(questionId);
      setQuestion(updated);
      setDeactivateConfirmationOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao inativar questão');
    } finally {
      setDeactivating(false);
    }
  };

  return (
    <div className="space-y-8">
          <Link href="/questions" className="text-sm font-medium text-emerald-700 hover:underline">
            ← Voltar para questões
          </Link>

          {loading ? (
            <p className="mt-8 text-sm text-slate-500">Carregando questão...</p>
          ) : error && !question ? (
            <div className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          ) : question ? (
            <>
              <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h1 className="text-3xl font-bold text-slate-900">
                      {question.statement}
                    </h1>
                    <p className="mt-2 text-sm text-slate-600">
                      {question.subject || 'Sem disciplina'} · {question.difficulty || 'Sem dificuldade'}
                    </p>
                    <p className="mt-2 text-sm text-slate-500">
                      Versão {question.version ?? 1} · {question.is_active ? 'Ativa' : 'Inativa'}
                    </p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                      {selectedSkillCount} habilidade(s)
                    </span>
                    <button
                      type="button"
                      onClick={() => setDeactivateConfirmationOpen(true)}
                      disabled={deactivating || !question.is_active}
                      className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-50"
                    >
                      Inativar
                    </button>
                  </div>
                </div>
              </div>

              {error && (
                <div className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>
              )}

              <ConfirmDialog
                open={deactivateConfirmationOpen}
                title="Inativar questão?"
                message="A questão deixa de aparecer como ativa no banco, mas a versão atual e o histórico permanecem disponíveis."
                warning="Essa ação preserva o histórico pedagógico e não apaga as tentativas já registradas."
                confirmLabel={deactivating ? 'Inativando...' : 'Confirmar inativação'}
                busy={deactivating}
                onConfirm={handleDeactivate}
                onCancel={() => setDeactivateConfirmationOpen(false)}
              />

              <form onSubmit={handleSave} className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-slate-900">Editar e versionar</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    A edição cria uma nova versão e preserva o histórico da anterior.
                  </p>

                  <label className="mt-5 block text-sm font-medium text-slate-700">
                    Enunciado
                    <textarea
                      value={statement}
                      onChange={(event) => setStatement(event.target.value)}
                      rows={4}
                      className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                    />
                  </label>

                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Matéria
                      <input
                        type="text"
                        value={subject}
                        onChange={(event) => setSubject(event.target.value)}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                      />
                    </label>
                    <label className="block text-sm font-medium text-slate-700">
                      Dificuldade
                      <input
                        type="text"
                        value={difficulty}
                        onChange={(event) => setDifficulty(event.target.value)}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                      />
                    </label>
                  </div>

                  <label className="mt-4 block text-sm font-medium text-slate-700">
                    Tags
                    <input
                      type="text"
                      value={tags}
                      onChange={(event) => setTags(event.target.value)}
                      className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                      placeholder="Separadas por vírgula"
                    />
                  </label>

                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Gabarito correto
                      <select
                        value={correctAnswer}
                        onChange={(event) => setCorrectAnswer(event.target.value)}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                      >
                        {OPTION_KEYS.map((optionKey) => (
                          <option key={optionKey} value={optionKey}>
                            {optionKey}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      A nova versão será criada com `parent_id` apontando para esta questão.
                    </div>
                  </div>

                  <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-sm font-medium text-slate-700">Alternativas</div>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      {OPTION_KEYS.map((optionKey) => (
                        <label key={optionKey} className="block text-xs font-medium text-slate-600">
                          {optionKey}
                          <input
                            type="text"
                            value={options[optionKey]}
                            onChange={(event) =>
                              setOptions((current) => ({
                                ...current,
                                [optionKey]: event.target.value,
                              }))
                            }
                            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                          />
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 flex flex-wrap gap-3">
                    <button
                      type="submit"
                      disabled={saving}
                      className="rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
                    >
                      {saving ? 'Salvando...' : 'Salvar nova versão'}
                    </button>
                    <Link
                      href="/questions"
                      className="rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      Voltar
                    </Link>
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-slate-900">Habilidades vinculadas</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    A nova versão pode manter ou trocar as habilidades associadas.
                  </p>

                  <div className="mt-4 grid gap-2">
                    {skills.map((skill) => {
                      const checked = selectedSkillIds.includes(skill.id);
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
                            onChange={() =>
                              setSelectedSkillIds((current) =>
                                current.includes(skill.id)
                                  ? current.filter((id) => id !== skill.id)
                                  : [...current, skill.id],
                              )
                            }
                            className="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-600"
                          />
                          <span>
                            <span className="block font-semibold text-slate-900">{skill.code}</span>
                            <span className="block text-xs text-slate-500">{skill.description}</span>
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </section>
              </form>
            </>
          ) : null}
    </div>
  );
}
