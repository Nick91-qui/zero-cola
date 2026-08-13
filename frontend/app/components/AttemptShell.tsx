'use client';

import Link from 'next/link';
import { ReactNode } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';

export interface AttemptShellProps {
  children: ReactNode;
}

export function AttemptShell({ children }: AttemptShellProps) {
  const { user, logout } = useAuth();

  return (
    <ProtectedRoute requiredRole="student">
      <div className="min-h-screen bg-slate-100 text-slate-900">
        <header className="border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 lg:px-6">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-lg font-bold tracking-tight text-slate-900">
                COLA-ZERO
              </Link>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                Área do aluno
              </span>
            </div>

            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span className="max-w-[220px] truncate">{user?.email}</span>
              <button
                type="button"
                onClick={logout}
                className="rounded-full border border-slate-300 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-700"
              >
                Sair
              </button>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-6 lg:px-6">{children}</main>
      </div>
    </ProtectedRoute>
  );
}
