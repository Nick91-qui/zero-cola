'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useMemo } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { ShellSearch, type ShellSearchItem } from '@/app/components/ShellSearch';
import { useAuth } from '@/app/hooks/useAuth';

type AdminNavItem = {
  href: string;
  label: string;
  hint: string;
};

const NAV_ITEMS: AdminNavItem[] = [
  { href: '/admin', label: 'Visão geral', hint: 'Resumo operacional' },
  { href: '/admin/users', label: 'Usuários', hint: 'Contas e vínculos' },
  { href: '/classes', label: 'Turmas', hint: 'Matrículas e professores' },
  { href: '/admin/audit', label: 'Auditoria', hint: 'Eventos sensíveis' },
  { href: '/consents', label: 'Consentimentos', hint: 'LGPD e monitoramento' },
  { href: '/privacy', label: 'Privacidade', hint: 'Política pública' },
];

const SEARCH_ITEMS: ShellSearchItem[] = NAV_ITEMS.map((item) => ({
  ...item,
  keywords: [item.label, item.hint, item.href.replace('/', ' ')],
}));

function isActivePath(pathname: string, href: string) {
  if (href === '/admin') {
    return pathname === '/admin';
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export interface AdminShellProps {
  children: ReactNode;
}

export function AdminShell({ children }: AdminShellProps) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <ProtectedRoute requiredRoles={['admin']}>
      <div className="min-h-screen bg-slate-100 text-slate-900">
        <header className="border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur">
          <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-6">
            <div className="flex items-center gap-4">
              <Link href="/admin" className="text-lg font-bold tracking-tight text-slate-900">
                COLA-ZERO
              </Link>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                Administração
              </span>
            </div>

            <div className="flex flex-1 items-center gap-3 lg:max-w-xl">
              <ShellSearch id="admin-search" items={SEARCH_ITEMS} />
            </div>

            <div className="flex items-center justify-between gap-3 text-sm text-slate-600 lg:justify-end">
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

        <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[16rem_minmax(0,1fr)] lg:px-6">
          <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-3 shadow-sm lg:sticky lg:top-6">
            <nav className="space-y-1">
              {NAV_ITEMS.map((item) => {
                const active = isActivePath(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={[
                      'flex items-start justify-between rounded-xl px-3 py-3 transition',
                      active
                        ? 'bg-slate-900 text-white shadow-sm'
                        : 'text-slate-700 hover:bg-slate-100',
                    ].join(' ')}
                  >
                    <span>
                      <span className="block text-sm font-semibold">{item.label}</span>
                      <span
                        className={[
                          'mt-0.5 block text-xs',
                          active ? 'text-slate-300' : 'text-slate-500',
                        ].join(' ')}
                      >
                        {item.hint}
                      </span>
                    </span>
                  </Link>
                );
              })}
            </nav>
          </aside>

          <main className="min-w-0">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
