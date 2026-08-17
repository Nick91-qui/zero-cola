'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { listQuestions } from '@/lib/questions';
import type { Question } from '@/lib/exams';

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [search, setSearch] = useState('');
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const questionData = await listQuestions({
        q: search.trim() || undefined,
        skill_id: selectedSkillId || undefined,
        include_inactive: includeInactive,
        limit: 100,
      });
      setQuestions(questionData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar questões');
    } finally {
      setLoading(false);
    }
  }, [includeInactive, search, selectedSkillId]);

  useEffect(() => {
    void loadQuestions();
  }, [loadQuestions]);

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Banco de questões
            </p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Ver questões</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Esta tela existe apenas para consulta do acervo. Para criar conteúdo, use as rotas
              separadas de habilidade e questão.
            </p>
          </div>

          <div className="grid gap-2 sm:grid-cols-3">
            <Link
              href="/questions/skills/new"
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-400 hover:bg-emerald-50"
            >
              Criar habilidades
            </Link>
            <Link
              href="/questions/new"
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-400 hover:bg-emerald-50"
            >
              Criar questões
            </Link>
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
            1. Consulta
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Use filtros para localizar questões existentes.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            2. Criação
          </p>
          <p className="mt-2 text-sm text-slate-600">
            A criação acontece nas telas específicas de habilidade e questão.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            3. Prova
          </p>
          <p className="mt-2 text-sm text-slate-600">
            O caminho para montar avaliação fica em `/exams/new`.
          </p>
        </div>
      </section>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Questões cadastradas</h2>
            <p className="mt-1 text-sm text-slate-600">
              {loading ? 'Carregando questões...' : `${questions.length} questão(ões) encontradas`}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <label className="block text-sm font-medium text-slate-700">
              Buscar por texto
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Enunciado, disciplina, habilidade, tag"
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Habilidade
              <input
                type="text"
                value={selectedSkillId}
                onChange={(event) => setSelectedSkillId(event.target.value)}
                placeholder="ID da habilidade"
                className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
              />
            </label>
            <label className="flex items-center gap-2 rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(event) => setIncludeInactive(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
              Incluir inativas
            </label>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {loading ? (
            <p className="py-12 text-center text-sm text-slate-500">Carregando questões...</p>
          ) : questions.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
              Nenhuma questão encontrada.
            </div>
          ) : (
            questions.map((question) => (
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
                    <Link
                      href={`/questions/${question.id}`}
                      className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      Editar / Versionar
                    </Link>
                  </div>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
