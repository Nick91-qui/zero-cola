'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { startOnlineAttempt } from '@/lib/attempts';

export default function StartAttemptPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const [examId, setExamId] = useState(() => searchParams.get('examId') ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const session = await startOnlineAttempt(examId.trim());
      router.push(`/attempts/${session.attempt.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao iniciar a tentativa');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute requiredRole="student">
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
            <Link href="/dashboard" className="text-lg font-bold text-slate-900">
              COLA-ZERO
            </Link>
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

        <main className="mx-auto max-w-4xl px-4 py-10">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Prova online
            </p>
            <h1 className="mt-3 text-3xl font-bold text-slate-900">
              Iniciar tentativa online
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Informe o identificador da avaliação para carregar o exame, iniciar a tentativa e continuar a prova com salvamento automático.
            </p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">
                  ID da avaliação
                </span>
                <input
                  value={examId}
                  onChange={(event) => setExamId(event.target.value)}
                  placeholder="Cole aqui o exam_id"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-600"
                />
              </label>

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="submit"
                  disabled={loading || !examId.trim()}
                  className="rounded-lg bg-emerald-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {loading ? 'Iniciando...' : 'Iniciar tentativa'}
                </button>
                <Link
                  href="/dashboard"
                  className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Voltar ao painel
                </Link>
              </div>
            </form>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
