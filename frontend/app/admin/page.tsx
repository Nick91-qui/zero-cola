import Link from 'next/link';

const metrics = [
  { label: 'Usuários ativos', value: '1540', tone: 'text-emerald-700' },
  { label: 'Turmas ativas', value: '62', tone: 'text-sky-700' },
  { label: 'Provas publicadas', value: '28', tone: 'text-indigo-700' },
  { label: 'Eventos de auditoria', value: '312', tone: 'text-amber-700' },
];

const alerts = [
  { label: 'Alunos sem turma', count: 50, tone: 'text-red-700' },
  { label: 'Turmas sem professor', count: 5, tone: 'text-amber-700' },
  { label: 'Alunos sem professor', count: 12, tone: 'text-amber-700' },
];

const recentActions = [
  { label: 'Usuário prof@...', status: 'Criado', when: 'agora' },
  { label: 'Turma 2º Ano A', status: 'Arquivada', when: '5m atrás' },
  { label: 'Turma 2º Ano A', status: 'Arquivada', when: '1h atrás' },
  { label: 'Turma 2º Ano A', status: 'Arquivada', when: '2h atrás' },
];

const shortcuts = [
  { label: 'Criar usuário', href: '/admin/users' },
  { label: 'Criar turma', href: '/classes' },
  { label: 'Ver auditoria', href: '/admin/audit' },
  { label: 'Gerenciar consentimentos', href: '/consents' },
];

export default function AdminHomePage() {
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
              Monitore usuários, turmas, auditoria e governança em um ponto único. A navegação
              lateral leva às áreas operacionais, e esta tela resume o que precisa de atenção.
            </p>
          </div>

          <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
            Acesso restrito a administradores
          </div>
        </div>
      </section>

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
                Situações que pedem ação antes da rotina seguir.
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
                Linha do tempo curta das mudanças administrativas mais importantes.
              </p>
            </div>
            <Link href="/admin/audit" className="text-sm font-medium text-emerald-700 hover:underline">
              Ver auditoria
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {recentActions.map((action) => (
              <div
                key={`${action.label}-${action.when}`}
                className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm"
              >
                <span className="truncate font-medium text-slate-800">{action.label}</span>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                  {action.status}
                </span>
                <span className="text-xs text-slate-500">{action.when}</span>
              </div>
            ))}
          </div>
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
          {shortcuts.map((shortcut) => (
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
