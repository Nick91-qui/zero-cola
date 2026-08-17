'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import { useAuth } from '@/app/hooks/useAuth';

export default function DashboardPage() {
  const { user } = useAuth();

  const primaryActions = useMemo(() => {
    const common = [
      {
        href: '/privacy',
        label: 'Privacidade',
        description: 'Política pública, exportação e dados pessoais.',
        tone: 'from-slate-900 to-slate-700',
      },
      {
        href: '/consents',
        label: 'Consentimentos',
        description: 'Gerencie o monitoramento e o histórico LGPD.',
        tone: 'from-emerald-700 to-emerald-500',
      },
    ];

    if (user?.role === 'student') {
      return [
        ...common,
        {
          href: '/attempts/start',
          label: 'Iniciar prova',
          description: 'Abra uma tentativa online disponível para sua turma.',
          tone: 'from-sky-700 to-sky-500',
        },
      ];
    }

    if (user?.role === 'teacher') {
      return [
        ...common,
        {
          href: '/classes',
          label: 'Turmas',
          description: 'Consulte vínculos, estudantes e professores.',
          tone: 'from-sky-700 to-sky-500',
        },
        {
          href: '/exams',
          label: 'Avaliações',
          description: 'Gerencie provas, relatórios e exportações.',
          tone: 'from-indigo-700 to-indigo-500',
        },
      ];
    }

    return [
      ...common,
      {
        href: '/admin',
        label: 'Administração',
        description: 'Usuários, auditoria, turmas e governança.',
        tone: 'from-amber-700 to-amber-500',
      },
      {
        href: '/classes',
        label: 'Turmas',
        description: 'Cadastre, arquive e organize vínculos.',
        tone: 'from-sky-700 to-sky-500',
      },
      {
        href: '/exams',
        label: 'Avaliações',
        description: 'Acompanhe provas, gabaritos e relatórios.',
        tone: 'from-indigo-700 to-indigo-500',
      },
    ];
  }, [user?.role]);

  return (
    <div className="space-y-8">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {primaryActions.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-emerald-300"
          >
            <div className={`h-1.5 rounded-full bg-gradient-to-r ${action.tone}`} />
            <h2 className="mt-4 text-lg font-bold text-slate-900">{action.label}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">{action.description}</p>
            <span className="mt-4 inline-flex text-sm font-semibold text-emerald-700 transition group-hover:translate-x-1">
              Abrir →
            </span>
          </Link>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Ações prioritárias</h2>
              <p className="mt-1 text-sm text-slate-600">
                Atalhos para o próximo passo mais comum do seu perfil.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              Fluxo rápido
            </span>
          </div>

          <div className="mt-5 grid gap-3">
            {user?.role === 'student' && (
              <Link
                href="/attempts/start"
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-emerald-300 hover:bg-emerald-50/50"
              >
                <span className="block text-sm font-semibold text-slate-900">Iniciar prova online</span>
                <span className="mt-1 block text-sm text-slate-600">
                  Continue uma avaliação disponível para sua turma.
                </span>
              </Link>
            )}

            {user?.role === 'teacher' && (
              <>
                <Link
                  href="/classes"
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-sky-300 hover:bg-sky-50/50"
                >
                  <span className="block text-sm font-semibold text-slate-900">Gerenciar turmas</span>
                  <span className="mt-1 block text-sm text-slate-600">
                    Ajuste vínculos de professores e estudantes.
                  </span>
                </Link>
                <Link
                  href="/exams"
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-indigo-300 hover:bg-indigo-50/50"
                >
                  <span className="block text-sm font-semibold text-slate-900">Avaliações e relatórios</span>
                  <span className="mt-1 block text-sm text-slate-600">
                    Publique provas, exporte relatórios e acompanhe métricas.
                  </span>
                </Link>
              </>
            )}

            {user?.role === 'admin' && (
              <>
                <Link
                  href="/admin"
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-amber-300 hover:bg-amber-50/50"
                >
                  <span className="block text-sm font-semibold text-slate-900">Administração</span>
                  <span className="mt-1 block text-sm text-slate-600">
                    Usuários, turmas, auditoria e governança.
                  </span>
                </Link>
                <Link
                  href="/admin/audit"
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-slate-300 hover:bg-slate-100"
                >
                  <span className="block text-sm font-semibold text-slate-900">Abrir auditoria</span>
                  <span className="mt-1 block text-sm text-slate-600">
                    Revise eventos sensíveis e trilhas administrativas.
                  </span>
                </Link>
              </>
            )}
          </div>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Mapa do portal</h2>
              <p className="mt-1 text-sm text-slate-600">
                Entradas mais usadas no fluxo diário.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {[
              { label: 'Privacidade', href: '/privacy' },
              { label: 'Consentimentos', href: '/consents' },
              { label: 'Turmas', href: '/classes' },
              { label: 'Avaliações', href: '/exams' },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm font-semibold text-slate-800 transition hover:border-emerald-300 hover:bg-emerald-50/50"
              >
                {item.label}
              </Link>
            ))}
          </div>

        </article>
      </section>
    </div>
  );
}
