'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { listTemplates, OMRTemplate } from '@/lib/omr';

export default function OmrHomePage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [templates, setTemplates] = useState<OMRTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await listTemplates();
        if (active) setTemplates(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Failed to load templates');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <ProtectedRoute requiredRoles={['teacher', 'admin']}>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-lg font-semibold text-slate-900">
                COLA-ZERO
              </Link>
              <span className="text-sm text-slate-500">OMR</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span>{user?.email}</span>
              <button
                type="button"
                onClick={async () => {
                  await logout();
                  router.push('/auth/login');
                }}
                className="rounded bg-slate-800 px-3 py-1.5 text-white hover:bg-slate-700"
              >
                Sair
              </button>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-5xl px-4 py-10">
          <div className="mb-8 flex items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl font-semibold text-slate-900">Gabaritos OMR</h1>
              <p className="mt-2 text-slate-600">
                Crie folhas de resposta, baixe o PDF e corrija por imagem.
              </p>
            </div>
            <Link
              href="/omr/new"
              className="rounded bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
            >
              Novo gabarito
            </Link>
          </div>

          {error && (
            <div className="mb-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-red-700">
              {error}
            </div>
          )}

          {loading ? (
            <p className="text-slate-500">Carregando templates...</p>
          ) : templates.length === 0 ? (
            <div className="rounded border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
              <p className="text-slate-600">Nenhum gabarito ainda.</p>
              <Link href="/omr/new" className="mt-4 inline-block text-emerald-700 hover:underline">
                Criar o primeiro
              </Link>
            </div>
          ) : (
            <ul className="space-y-3">
              {templates.map((template) => (
                <li key={template.id}>
                  <Link
                    href={`/omr/${template.id}`}
                    className="block rounded border border-slate-200 bg-white px-4 py-4 hover:border-emerald-600"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-medium text-slate-900">{template.layout_version}</p>
                        <p className="text-sm text-slate-500">
                          {template.total_questions} questões · criado em{' '}
                          {new Date(template.created_at).toLocaleString()}
                        </p>
                      </div>
                      <span className="text-sm text-emerald-700">Abrir →</span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
