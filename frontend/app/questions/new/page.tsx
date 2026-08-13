'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { listSkills, type SkillSummary } from '@/lib/skills';
import { createQuestion } from '@/lib/questions';

const OPTION_KEYS = ['A', 'B', 'C', 'D', 'E'] as const;

function createEmptyOptions() {
  return {
    A: '',
    B: '',
    C: '',
    D: '',
    E: '',
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

export default function NewQuestionPage() {
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [saving, setSaving] = useState(false);
  const [statement, setStatement] = useState('');
  const [subject, setSubject] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [tags, setTags] = useState('');
  const [correctAnswer, setCorrectAnswer] = useState('A');
  const [options, setOptions] = useState<Record<string, string>>(createEmptyOptions());
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const data = await listSkills();
        if (active) {
          setSkills(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar habilidades');
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const trimmedStatement = statement.trim();
    if (!trimmedStatement) {
      setError('Informe o enunciado da questão.');
      return;
    }

    const normalizedOptions = normalizeOptions(options);
    if (!normalizedOptions || Object.keys(normalizedOptions).length < 2) {
      setError('Informe ao menos duas alternativas.');
      return;
    }

    if (!normalizedOptions[correctAnswer]) {
      setError('Selecione uma alternativa correta válida.');
      return;
    }

    setSaving(true);
    try {
      await createQuestion({
        statement: trimmedStatement,
        type: 'multiple_choice',
        options: normalizedOptions,
        correct_answer: correctAnswer,
        subject: subject.trim() || null,
        difficulty: difficulty.trim() || null,
        tags:
          tags
            .split(',')
            .map((tag) => tag.trim())
            .filter(Boolean) || null,
        skill_ids: selectedSkillIds.length > 0 ? selectedSkillIds : undefined,
      });
      setStatement('');
      setSubject('');
      setDifficulty('');
      setTags('');
      setCorrectAnswer('A');
      setOptions(createEmptyOptions());
      setSelectedSkillIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar questão');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Criar questões
            </p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Nova questão</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Esta tela faz apenas o cadastro de questão. Depois da criação, volte ao banco ou siga
              para a montagem da prova.
            </p>
          </div>

          <Link
            href="/questions"
            className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-400 hover:bg-emerald-50"
          >
            Voltar ao banco
          </Link>
        </div>
      </section>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Dados da questão</h2>
          <p className="mt-1 text-sm text-slate-600">
            Informe o conteúdo principal e as alternativas.
          </p>

          <label className="mt-5 block text-sm font-medium text-slate-700">
            Enunciado
            <textarea
              value={statement}
              onChange={(event) => setStatement(event.target.value)}
              rows={4}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="Digite o enunciado da questão."
            />
          </label>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              Matéria
              <input
                type="text"
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                placeholder="Ex: Matemática"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Dificuldade
              <input
                type="text"
                value={difficulty}
                onChange={(event) => setDifficulty(event.target.value)}
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                placeholder="Ex: easy"
              />
            </label>
          </div>

          <label className="mt-4 block text-sm font-medium text-slate-700">
            Tags
            <input
              type="text"
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="Ex: frações, adição"
            />
          </label>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Alternativas e gabarito</h2>
              <p className="mt-1 text-sm text-slate-600">
                Cadastre as alternativas e marque a correta.
              </p>
            </div>
            <label className="block text-sm font-medium text-slate-700">
              Gabarito correto
              <select
                value={correctAnswer}
                onChange={(event) => setCorrectAnswer(event.target.value)}
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              >
                {OPTION_KEYS.map((optionKey) => (
                  <option key={optionKey} value={optionKey}>
                    {optionKey}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
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
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  placeholder={`Texto da alternativa ${optionKey}`}
                />
              </label>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Habilidades vinculadas</h2>
              <p className="mt-1 text-sm text-slate-600">
                Marque as habilidades que essa questão cobre.
              </p>
            </div>
            <span className="text-sm text-slate-500">{skills.length} habilidade(s)</span>
          </div>

          {skills.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
              Nenhuma habilidade cadastrada ainda. Crie uma habilidade antes de vincular.
            </p>
          ) : (
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
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
          )}
        </section>

        <button
          type="submit"
          disabled={saving}
          className="w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
        >
          {saving ? 'Salvando...' : 'Criar questão'}
        </button>
      </form>
    </div>
  );
}
