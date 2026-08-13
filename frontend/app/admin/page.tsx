'use client';

import Link from 'next/link';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';

export default function AdminHomePage() {
  const { user, logout } = useAuth();

  return (
    <ProtectedRoute requiredRoles={['admin']}>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-lg font-bold text-slate-900">
                COLA-ZERO
              </Link>
              <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                Área admin
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
          <h1 className="text-3xl font-bold text-slate-900">Administração</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Escolha a área que deseja administrar. Usuários e turmas ficam em caminhos explícitos,
            e o detalhe da turma mostra o vínculo professor &gt; turma &gt; aluno.
          </p>

          <div className="mt-8 grid gap-6 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Usuários</h2>
              <p className="mt-2 text-sm text-slate-600">
                Crie contas, inative usuários e exclua/anonimize cadastros.
              </p>
              <Link
                href="/admin/users"
                className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600"
              >
                Abrir usuários
              </Link>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Turmas</h2>
              <p className="mt-2 text-sm text-slate-600">
                Crie turmas, vincule professores e abra o detalhe para ver alunos.
              </p>
              <Link
                href="/classes"
                className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
              >
                Abrir turmas
              </Link>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Auditoria</h2>
              <p className="mt-2 text-sm text-slate-600">
                Consulte logs administrativos e eventos de segurança.
              </p>
              <Link
                href="/admin/audit"
                className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-slate-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-600"
              >
                Abrir auditoria
              </Link>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
