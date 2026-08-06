'use client';

import { useMemo, useState } from 'react';
import type { Question } from '@/lib/exams';

export interface SelectedQuestionDraft {
  question: Question;
  weight: string;
}

interface QuestionBankSelectorProps {
  questions: Question[];
  selectedQuestions: SelectedQuestionDraft[];
  onChange: (selectedQuestions: SelectedQuestionDraft[]) => void;
}

function matchesQuery(question: Question, query: string) {
  if (!query.trim()) return true;
  const normalized = query.trim().toLowerCase();
  const text = [
    question.statement,
    question.subject ?? '',
    question.difficulty ?? '',
    question.tags?.join(' ') ?? '',
    question.skills.map((skill) => `${skill.code} ${skill.description}`).join(' '),
  ]
    .join(' ')
    .toLowerCase();
  return text.includes(normalized);
}

export function QuestionBankSelector({
  questions,
  selectedQuestions,
  onChange,
}: QuestionBankSelectorProps) {
  const [query, setQuery] = useState('');

  const selectedIds = useMemo(
    () => new Set(selectedQuestions.map((item) => item.question.id)),
    [selectedQuestions],
  );

  const availableQuestions = useMemo(
    () =>
      questions.filter(
        (question) => !selectedIds.has(question.id) && matchesQuery(question, query),
      ),
    [questions, query, selectedIds],
  );

  const addQuestion = (question: Question) => {
    onChange([...selectedQuestions, { question, weight: '1.00' }]);
  };

  const removeQuestion = (questionId: string) => {
    onChange(selectedQuestions.filter((item) => item.question.id !== questionId));
  };

  const moveQuestion = (questionId: string, direction: -1 | 1) => {
    const currentIndex = selectedQuestions.findIndex((item) => item.question.id === questionId);
    if (currentIndex < 0) return;
    const nextIndex = currentIndex + direction;
    if (nextIndex < 0 || nextIndex >= selectedQuestions.length) return;
    const nextSelected = [...selectedQuestions];
    const [item] = nextSelected.splice(currentIndex, 1);
    nextSelected.splice(nextIndex, 0, item);
    onChange(nextSelected);
  };

  const updateWeight = (questionId: string, weight: string) => {
    onChange(
      selectedQuestions.map((item) =>
        item.question.id === questionId
          ? {
              ...item,
              weight,
            }
          : item,
      ),
    );
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Banco de Questões</h2>
          <p className="mt-1 text-sm text-slate-600">
            Selecione questões já cadastradas para compor a avaliação.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {selectedQuestions.length} selecionada(s)
        </span>
      </div>

      <label className="mt-4 block text-sm font-medium text-slate-700">
        Buscar questão
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar por enunciado, habilidade ou tema"
          className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
        />
      </label>

      <div className="mt-4 grid gap-6 xl:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-900">Questões disponíveis</h3>
            <span className="text-xs text-slate-500">{availableQuestions.length} encontrada(s)</span>
          </div>

          {availableQuestions.length === 0 ? (
            <p className="mt-4 rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
              Nenhuma questão encontrada com os filtros atuais.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {availableQuestions.map((question) => (
                <article key={question.id} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-900">{question.statement}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {question.subject || 'Sem disciplina'} · {question.difficulty || 'Sem dificuldade'}
                      </p>
                      <p className="mt-2 text-xs text-slate-500">
                        Habilidades:{' '}
                        {question.skills.length > 0
                          ? question.skills.map((skill) => skill.code).join(', ')
                          : 'Nenhuma'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => addQuestion(question)}
                      className="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-600"
                    >
                      Adicionar
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-900">Seleção da prova</h3>
            <span className="text-xs text-slate-500">Ordem editável</span>
          </div>

          {selectedQuestions.length === 0 ? (
            <p className="mt-4 rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
              Adicione questões do banco para montar a prova.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {selectedQuestions.map((item, index) => (
                <article key={item.question.id} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                        Ordem {index + 1}
                      </p>
                      <p className="mt-1 text-sm font-semibold text-slate-900">{item.question.statement}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.question.skills.length > 0
                          ? item.question.skills.map((skill) => skill.code).join(', ')
                          : 'Nenhuma habilidade vinculada'}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => moveQuestion(item.question.id, -1)}
                        disabled={index === 0}
                        className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 disabled:opacity-40"
                      >
                        ↑
                      </button>
                      <button
                        type="button"
                        onClick={() => moveQuestion(item.question.id, 1)}
                        disabled={index === selectedQuestions.length - 1}
                        className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 disabled:opacity-40"
                      >
                        ↓
                      </button>
                      <button
                        type="button"
                        onClick={() => removeQuestion(item.question.id)}
                        className="rounded-md border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs font-semibold text-red-700"
                      >
                        Remover
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Peso
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={item.weight}
                        onChange={(event) => updateWeight(item.question.id, event.target.value)}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                      />
                    </label>
                    <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
                      Resposta correta:{' '}
                      <span className="font-semibold text-emerald-700">
                        {String(item.question.correct_answer)}
                      </span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
