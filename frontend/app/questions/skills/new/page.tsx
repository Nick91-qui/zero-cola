'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { createSkill } from '@/lib/skills';

export default function NewSkillPage() {
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [gradeLevel, setGradeLevel] = useState('');
  const [curriculum, setCurriculum] = useState('BNCC');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setCreated(false);

    const trimmedCode = code.trim();
    const trimmedDescription = description.trim();
    if (!trimmedCode || !trimmedDescription) {
      setError('Informe o código e a descrição da habilidade.');
      return;
    }

    setSaving(true);
    try {
      await createSkill({
        code: trimmedCode,
        description: trimmedDescription,
        subject: subject.trim() || null,
        grade_level: gradeLevel.trim() || null,
        curriculum: curriculum.trim() || 'BNCC',
      });
      setCreated(true);
      setCode('');
      setDescription('');
      setSubject('');
      setGradeLevel('');
      setCurriculum('BNCC');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar habilidade');
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
              Criar habilidades
            </p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Nova habilidade</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Esta tela faz apenas o cadastro de habilidades. Depois disso, volte para criar a
              questão e vinculá-la ao conteúdo correto.
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

      {created ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          Habilidade criada com sucesso.
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Dados da habilidade</h2>
        <p className="mt-1 text-sm text-slate-600">
          Preencha apenas o necessário para registrar a habilidade no banco.
        </p>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Código
            <input
              type="text"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="Ex: EF05MA01"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Descrição
            <input
              type="text"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="Resolver adições simples"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Área da habilidade
            <input
              type="text"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="Ex: Matemática"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Etapa/ano
            <input
              type="text"
              value={gradeLevel}
              onChange={(event) => setGradeLevel(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="Ex: 5º ano"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700 md:col-span-2">
            Currículo
            <input
              type="text"
              value={curriculum}
              onChange={(event) => setCurriculum(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              placeholder="BNCC"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="mt-6 w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
        >
          {saving ? 'Salvando...' : 'Criar habilidade'}
        </button>
      </form>
    </div>
  );
}
