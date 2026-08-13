'use client';

import Link from 'next/link';
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { createSkill, listSkills, type SkillSummary } from '@/lib/skills';
import { createQuestion, listQuestions } from '@/lib/questions';
import type { Question } from '@/lib/exams';

const OPTION_KEYS = ['A', 'B', 'C', 'D', 'E'] as const;
const QUESTION_PAGE_SIZE = 8;

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

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [statement, setStatement] = useState('');
  const [subject, setSubject] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [tags, setTags] = useState('');
  const [correctAnswer, setCorrectAnswer] = useState('A');
  const [options, setOptions] = useState<Record<string, string>>(createEmptyOptions());
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [newSkillCode, setNewSkillCode] = useState('');
  const [newSkillDescription, setNewSkillDescription] = useState('');
  const [newSkillSubject, setNewSkillSubject] = useState('');
  const [newSkillGradeLevel, setNewSkillGradeLevel] = useState('');
  const [newSkillCurriculum, setNewSkillCurriculum] = useState('BNCC');
  const [creatingSkill, setCreatingSkill] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasNextPage = questions.length === QUESTION_PAGE_SIZE;

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const [questionData, skillData] = await Promise.all([listQuestions(), listSkills()]);
        if (!active) return;
        setQuestions(questionData);
        setSkills(skillData);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar questões');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const loadQuestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const questionData = await listQuestions({
        q: search.trim() || undefined,
        skill_id: selectedSkillId || undefined,
        include_inactive: includeInactive,
        skip: (currentPage - 1) * QUESTION_PAGE_SIZE,
        limit: QUESTION_PAGE_SIZE,
      });
      setQuestions(questionData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar questões');
    } finally {
      setLoading(false);
    }
  }, [currentPage, includeInactive, search, selectedSkillId]);

  useEffect(() => {
    void loadQuestions();
  }, [loadQuestions]);

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
      const created = await createQuestion({
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
      setQuestions((current) => [created, ...current].slice(0, QUESTION_PAGE_SIZE));
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

  const handleCreateSkill = async () => {
    setError(null);

    const code = newSkillCode.trim();
    const description = newSkillDescription.trim();
    if (!code || !description) {
      setError('Informe o código e a descrição da habilidade.');
      return;
    }

    setCreatingSkill(true);
    try {
      const created = await createSkill({
        code,
        description,
        subject: newSkillSubject.trim() || null,
        grade_level: newSkillGradeLevel.trim() || null,
        curriculum: newSkillCurriculum.trim() || 'BNCC',
      });
      setSkills((current) => [...current, created].sort((a, b) => a.code.localeCompare(b.code)));
      setSelectedSkillIds((current) => (current.includes(created.id) ? current : [...current, created.id]));
      setNewSkillCode('');
      setNewSkillDescription('');
      setNewSkillSubject('');
      setNewSkillGradeLevel('');
      setNewSkillCurriculum('BNCC');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar habilidade');
    } finally {
      setCreatingSkill(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Banco de questões
            </p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Fluxo do professor</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Use a ordem sugerida: criar habilidade, criar questão e depois montar a prova.
              Isso reduz o salto entre telas e deixa o caminho mais previsível.
            </p>
          </div>

          <div className="grid gap-2 sm:grid-cols-3">
            <a
              href="#nova-habilidade"
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-400 hover:bg-emerald-50"
            >
              Criar habilidade
            </a>
            <a
              href="#nova-questao"
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-400 hover:bg-emerald-50"
            >
              Criar questão
            </a>
            <Link
              href="/exams/new"
              className="inline-flex items-center justify-center rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600"
            >
              Montar prova
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            1. Habilidade
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Registre a habilidade para manter as questões bem agrupadas.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            2. Questão
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Cadastre o enunciado, alternativas e gabarito nesta mesma tela.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            3. Prova
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Leve o conteúdo pronto para a montagem da avaliação online.
          </p>
        </div>
      </section>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Acervo de questões</h2>
              <p className="mt-1 text-sm text-slate-600">
                {loading ? 'Carregando questões...' : `${questions.length} questão(ões) nesta página`}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <label className="block text-sm font-medium text-slate-700">
                Buscar por texto
                <input
                  type="search"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setCurrentPage(1);
                  }}
                  placeholder="Enunciado, disciplina, habilidade, tag"
                  className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Habilidade
                <select
                  value={selectedSkillId}
                  onChange={(event) => {
                    setSelectedSkillId(event.target.value);
                    setCurrentPage(1);
                  }}
                  className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                >
                  <option value="">Todas</option>
                  {skills.map((skill) => (
                    <option key={skill.id} value={skill.id}>
                      {skill.code}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2 rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={includeInactive}
                  onChange={(event) => {
                    setIncludeInactive(event.target.checked);
                    setCurrentPage(1);
                  }}
                  className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                Incluir inativas
              </label>
            </div>
          </div>

          {loading ? (
            <p className="py-12 text-center text-sm text-slate-500">Carregando questões...</p>
          ) : questions.length === 0 ? (
            <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="text-sm text-slate-500">Nenhuma questão encontrada.</p>
            </div>
          ) : (
            <div className="mt-6 grid gap-4">
              {questions.map((question) => (
                <article key={question.id} className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-semibold text-slate-900">{question.statement}</h3>
                        <span
                          className={[
                            'rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-[0.15em]',
                            question.is_active
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-200 text-slate-700',
                          ].join(' ')}
                        >
                          {question.is_active ? 'Ativa' : 'Inativa'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">
                        {question.subject || 'Sem disciplina'} · {question.difficulty || 'Sem dificuldade'}
                      </p>
                      <p className="mt-2 text-sm text-slate-700">
                        Habilidades:{' '}
                        {question.skills.length > 0
                          ? question.skills.map((skill) => skill.code).join(', ')
                          : 'Nenhuma'}
                      </p>
                      <p className="mt-2 text-sm text-slate-700">
                        Gabarito:{' '}
                        <span className="font-semibold text-emerald-700">
                          {String(question.correct_answer)}
                        </span>
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-2 text-right text-xs text-slate-500">
                      <div>Versão {question.version ?? 1}</div>
                      <div>ID {question.id}</div>
                      <Link
                        href={`/questions/${question.id}`}
                        className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Editar / Versionar
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
            <p className="text-xs text-slate-500">
              Página {currentPage} · {questions.length} registro(s) carregado(s)
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                disabled={currentPage === 1 || loading}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                type="button"
                onClick={() => setCurrentPage((page) => page + 1)}
                disabled={!hasNextPage || loading}
                className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-800 disabled:opacity-50"
              >
                Próxima
              </button>
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <section id="nova-habilidade" className="scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Criar habilidade</h2>
            <p className="mt-1 text-sm text-slate-600">
              Crie a habilidade antes ou durante o cadastro da questão para manter o fluxo curto.
            </p>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <label className="block text-xs font-medium text-slate-600">
                Código
                <input
                  type="text"
                  value={newSkillCode}
                  onChange={(event) => setNewSkillCode(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                  placeholder="Ex: EF05MA01"
                />
              </label>
              <label className="block text-xs font-medium text-slate-600">
                Descrição
                <input
                  type="text"
                  value={newSkillDescription}
                  onChange={(event) => setNewSkillDescription(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                  placeholder="Resolver adições simples"
                />
              </label>
              <label className="block text-xs font-medium text-slate-600">
                Área da habilidade
                <input
                  type="text"
                  value={newSkillSubject}
                  onChange={(event) => setNewSkillSubject(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                  placeholder="Ex: Matemática"
                />
              </label>
              <label className="block text-xs font-medium text-slate-600">
                Etapa/ano
                <input
                  type="text"
                  value={newSkillGradeLevel}
                  onChange={(event) => setNewSkillGradeLevel(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                  placeholder="Ex: 5º ano"
                />
              </label>
              <label className="block text-xs font-medium text-slate-600 md:col-span-2">
                Currículo da habilidade
                <input
                  type="text"
                  value={newSkillCurriculum}
                  onChange={(event) => setNewSkillCurriculum(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
                  placeholder="BNCC"
                />
              </label>
            </div>

            <button
              type="button"
              onClick={() => void handleCreateSkill()}
              disabled={creatingSkill}
              className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-300"
            >
              {creatingSkill ? 'Criando...' : 'Criar habilidade'}
            </button>
          </section>

          <section
            id="nova-questao"
            className="scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h2 className="text-lg font-semibold text-slate-900">Criar questão</h2>
            <p className="mt-1 text-sm text-slate-600">
              Cadastre o enunciado e os dados básicos da questão, depois marque as habilidades.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <label className="block text-sm font-medium text-slate-700">
                Enunciado
                <textarea
                  value={statement}
                  onChange={(event) => setStatement(event.target.value)}
                  rows={4}
                  className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  placeholder="Digite o enunciado da questão."
                />
              </label>

              <div className="grid gap-4 md:grid-cols-2">
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

              <label className="block text-sm font-medium text-slate-700">
                Tags
                <input
                  type="text"
                  value={tags}
                  onChange={(event) => setTags(event.target.value)}
                  className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  placeholder="Ex: frações, adição"
                />
              </label>

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

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
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
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                        placeholder={`Texto da alternativa ${optionKey}`}
                      />
                    </label>
                  ))}
                </div>
              </div>

              {skills.length > 0 && (
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="text-sm font-medium text-slate-700">Habilidades</div>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
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
                </div>
              )}

              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
              >
                {saving ? 'Salvando...' : 'Criar questão'}
              </button>
            </form>
          </section>
        </section>
      </div>
    </div>
  );
}
