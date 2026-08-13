'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { listAuditLogs, type AuditLog } from '@/lib/audit';
import { listClasses, type ClassSummary } from '@/lib/classes';
import { listExams, type Exam } from '@/lib/exams';
import { listUsers, type UserSearchResult } from '@/lib/users';

type DashboardData = {
  users: UserSearchResult[];
  classes: ClassSummary[];
  exams: Exam[];
  auditLogs: AuditLog[];
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

function safeLabel(value: string | null | undefined, fallback: string) {
  return value?.trim() ? value : fallback;
}

export default function AdminHomePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setError(null);

      const [usersResult, classesResult, examsResult, auditLogsResult] = await Promise.allSettled([
        listUsers({ include_inactive: true, limit: 1000 }),
        listClasses(true),
        listExams(),
        listAuditLogs({ limit: 8 }),
      ]);

      if (!active) return;

      const nextData: DashboardData = {
        users: usersResult.status === 'fulfilled' ? usersResult.value : [],
        classes: classesResult.status === 'fulfilled' ? classesResult.value : [],
        exams: examsResult.status === 'fulfilled' ? examsResult.value : [],
        auditLogs: auditLogsResult.status === 'fulfilled' ? auditLogsResult.value : [],
      };

      setData(nextData);

      const failures = [usersResult, classesResult, examsResult, auditLogsResult]
        .filter((result) => result.status === 'rejected')
        .map((result) => {
          const reason = result.status === 'rejected' ? result.reason : null;
          return reason instanceof Error ? reason.message : 'Falha ao carregar parte do painel.';
        });

      if (failures.length > 0) {
        setError(failures.join(' | '));
      }
    }

    loadDashboard();

    return () => {
      active = false;
    };
  }, []);

  const metrics = useMemo(() => {
    const users = data?.users ?? [];
    const classes = data?.classes ?? [];
    const exams = data?.exams ?? [];

    const activeUsers = users.filter((user) => user.is_active).length;
    const activeClasses = classes.filter((item) => item.is_active).length;
    const activeExams = exams.filter((exam) => exam.is_active).length;

    return [
      { label: 'Usuários ativos', value: activeUsers.toString(), tone: 'text-emerald-700' },
      { label: 'Turmas ativas', value: activeClasses.toString(), tone: 'text-sky-700' },
      { label: 'Avaliações ativas', value: activeExams.toString(), tone: 'text-indigo-700' },
      { label: 'Eventos recentes', value: (data?.auditLogs.length ?? 0).toString(), tone: 'text-amber-700' },
    ] as const;
  }, [data]);

  const alerts = useMemo(() => {
    const classes = data?.classes ?? [];
    const users = data?.users ?? [];

    return [
      {
        label: 'Turmas sem professor',
        count: classes.filter((item) => !item.teacher_id).length,
        tone: 'text-amber-700',
      },
      {
        label: 'Turmas arquivadas',
        count: classes.filter((item) => item.archived_at).length,
        tone: 'text-slate-700',
      },
      {
        label: 'Professores inativos',
        count: users.filter((user) => user.role === 'teacher' && !user.is_active).length,
        tone: 'text-red-700',
      },
    ];
  }, [data]);

  const roleBreakdown = useMemo(() => {
    const users = data?.users ?? [];

    return {
      total: users.length,
      teachers: users.filter((user) => user.role === 'teacher').length,
      students: users.filter((user) => user.role === 'student').length,
      admins: users.filter((user) => user.role === 'admin').length,
    };
  }, [data]);

  const recentActions = data?.auditLogs ?? [];

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Visão geral
        </p>
        <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Dashboard admin</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Acompanhe usuários, turmas, avaliações e trilha de auditoria a partir de dados vivos
              do sistema. Os atalhos abaixo levam direto às rotinas operacionais.
            </p>
          </div>

          <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
            Acesso restrito a administradores
          </div>
        </div>
      </section>

      {error ? (
        <section className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
          Falha ao carregar o painel: {error}
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <article
            key={metric.label}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <p className="text-sm font-medium text-slate-600">{metric.label}</p>
            <p className={`mt-3 text-4xl font-bold ${metric.tone}`}>{metric.value}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Alertas prioritários</h2>
              <p className="mt-1 text-sm text-slate-600">
                Situações de governança que pedem ação antes da rotina seguir.
              </p>
            </div>
            <Link href="/classes" className="text-sm font-medium text-emerald-700 hover:underline">
              Abrir turmas
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.label}
                className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-sm font-semibold ${alert.tone}`}>●</span>
                  <span className="text-sm font-medium text-slate-800">{alert.label}</span>
                </div>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                  {alert.count}
                </span>
              </div>
            ))}
          </div>

        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Ações recentes</h2>
              <p className="mt-1 text-sm text-slate-600">
                Eventos de auditoria e alterações mais recentes do ambiente.
              </p>
            </div>
            <Link href="/admin/audit" className="text-sm font-medium text-emerald-700 hover:underline">
              Ver auditoria
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {recentActions.length > 0 ? (
              recentActions.map((action) => (
                <div
                  key={action.id}
                  className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm"
                >
                  <span className="truncate font-medium text-slate-800">
                    {safeLabel(action.event_type, 'Evento')}
                    {action.resource_type ? ` • ${action.resource_type}` : ''}
                  </span>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                    {safeLabel(action.resource_id?.slice(0, 8), 'sem id')}
                  </span>
                  <span className="text-xs text-slate-500">{formatDate(action.created_at)}</span>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500">
                Nenhum evento recente encontrado.
              </div>
            )}
          </div>

          {data ? (
            <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">Resumo da base</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-4">
                <div className="rounded-xl bg-white px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Total</p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">{roleBreakdown.total}</p>
                </div>
                <div className="rounded-xl bg-white px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Professores</p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    {roleBreakdown.teachers}
                  </p>
                </div>
                <div className="rounded-xl bg-white px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Alunos</p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">{roleBreakdown.students}</p>
                </div>
                <div className="rounded-xl bg-white px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Admins</p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">{roleBreakdown.admins}</p>
                </div>
              </div>
            </div>
          ) : null}
        </article>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Atalhos rápidos</h2>
            <p className="mt-1 text-sm text-slate-600">
              Entradas diretas para as ações mais frequentes do administrador.
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {[
            { label: 'Criar usuário', href: '/admin/users' },
            { label: 'Criar turma', href: '/classes' },
            { label: 'Ver auditoria', href: '/admin/audit' },
            { label: 'Gerenciar consentimentos', href: '/consents' },
          ].map((shortcut) => (
            <Link
              key={shortcut.href}
              href={shortcut.href}
              className="flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-400 hover:bg-emerald-50"
            >
              {shortcut.label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
