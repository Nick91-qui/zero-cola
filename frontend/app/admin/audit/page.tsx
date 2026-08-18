'use client';

import { FormEvent, useEffect, useState } from 'react';
import { listAuditLogs, listSecurityEvents, type AuditLog, type SecurityEvent } from '@/lib/audit';
import { listAdminConsents, type Consent } from '@/lib/consents';

function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

function shortId(value: string | null | undefined) {
  if (!value) return 'sem id';
  return value.length > 10 ? `${value.slice(0, 8)}…` : value;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [consents, setConsents] = useState<Consent[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [attemptId, setAttemptId] = useState('');
  const [logEventType, setLogEventType] = useState('');
  const [logResourceType, setLogResourceType] = useState('');
  const [consentType, setConsentType] = useState('');
  const [consentGranted, setConsentGranted] = useState<'all' | 'granted' | 'revoked'>('all');
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [loadingConsents, setLoadingConsents] = useState(true);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eventsError, setEventsError] = useState<string | null>(null);

  const loadLogs = async (filters?: {
    eventType?: string;
    resourceType?: string;
  }) => {
    setLoadingLogs(true);
    setError(null);
    try {
      const data = await listAuditLogs({
        limit: 50,
        event_type: filters?.eventType?.trim() || undefined,
        resource_type: filters?.resourceType?.trim() || undefined,
      });
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar auditoria');
    } finally {
      setLoadingLogs(false);
    }
  };

  const loadConsents = async (filters?: { consentType?: string; granted?: boolean }) => {
    setLoadingConsents(true);
    setError(null);
    try {
      const data = await listAdminConsents({
        limit: 50,
        consent_type: filters?.consentType?.trim() || undefined,
        granted: filters?.granted,
      });
      setConsents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar consentimentos');
    } finally {
      setLoadingConsents(false);
    }
  };

  const loadEvents = async (attemptValue: string) => {
    const normalizedAttemptId = attemptValue.trim();
    if (!normalizedAttemptId) return;
    setEventsLoading(true);
    setEventsError(null);
    try {
      const data = await listSecurityEvents(normalizedAttemptId);
      setEvents(data);
      setAttemptId(normalizedAttemptId);
    } catch (err) {
      setEventsError(err instanceof Error ? err.message : 'Falha ao carregar eventos');
    } finally {
      setEventsLoading(false);
    }
  };

  useEffect(() => {
    void loadLogs();
    void loadConsents();
  }, []);

  const handleLogFilterSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await loadLogs({
      eventType: logEventType,
      resourceType: logResourceType,
    });
  };

  const handleConsentFilterSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await loadConsents({
      consentType,
      granted:
        consentGranted === 'all' ? undefined : consentGranted === 'granted',
    });
  };

  const handleSecuritySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await loadEvents(attemptId);
  };

  const recentLogs = logs.slice(0, 10);
  const activeConsents = consents.filter((consent) => consent.granted).length;
  const revokedConsents = consents.filter((consent) => !consent.granted).length;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Governança
        </p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Auditoria e consentimentos</h1>
        <p className="mt-2 max-w-4xl text-sm text-slate-600">
          Consulte a trilha de auditoria, revise consentimentos registrados e abra eventos de
          segurança de uma tentativa específica. Os blocos abaixo foram organizados para reduzir a
          caça ao dado correto.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-600">Logs carregados</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">
            {loadingLogs ? '...' : logs.length}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-600">Consentimentos ativos</p>
          <p className="mt-2 text-3xl font-bold text-emerald-700">
            {loadingConsents ? '...' : activeConsents}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-600">Consentimentos revogados</p>
          <p className="mt-2 text-3xl font-bold text-amber-700">
            {loadingConsents ? '...' : revokedConsents}
          </p>
        </article>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.95fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Trilha de auditoria</h2>
              <p className="mt-1 text-sm text-slate-600">
                Eventos administrativos mais recentes do sistema.
              </p>
            </div>

            <form onSubmit={handleLogFilterSubmit} className="grid gap-3 sm:grid-cols-3">
              <input
                value={logEventType}
                onChange={(event) => setLogEventType(event.target.value)}
                placeholder="Filtrar por evento"
                className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
              <input
                value={logResourceType}
                onChange={(event) => setLogResourceType(event.target.value)}
                placeholder="Filtrar por recurso"
                className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                type="submit"
                disabled={loadingLogs}
                className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
              >
                {loadingLogs ? 'Carregando...' : 'Aplicar'}
              </button>
            </form>
          </div>

          {loadingLogs ? (
            <p className="py-12 text-center text-sm text-slate-500">Carregando logs...</p>
          ) : recentLogs.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
              Nenhum log encontrado para os filtros atuais.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {recentLogs.map((log) => (
                <article key={log.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-1">
                      <h3 className="font-semibold text-slate-900">{log.event_type}</h3>
                      <p className="text-sm text-slate-600">
                        {log.resource_type || 'sem recurso'} · {shortId(log.resource_id)}
                      </p>
                      {log.user_id && (
                        <p className="text-xs text-slate-500">Usuário {shortId(log.user_id)}</p>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                        {formatDate(log.created_at)}
                      </span>
                      {log.resource_type === 'attempt' && log.resource_id ? (
                        <button
                          type="button"
                          onClick={() => void loadEvents(log.resource_id ?? '')}
                          className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 hover:bg-emerald-100"
                        >
                          Ver eventos da tentativa
                        </button>
                      ) : null}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Consentimentos</h2>
              <p className="mt-1 text-sm text-slate-600">
                Visualização administrativa de consentimentos registrados e revogados.
              </p>
            </div>

            <form onSubmit={handleConsentFilterSubmit} className="grid gap-3 sm:grid-cols-3">
              <input
                value={consentType}
                onChange={(event) => setConsentType(event.target.value)}
                placeholder="Tipo de consentimento"
                className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
              <select
                value={consentGranted}
                onChange={(event) =>
                  setConsentGranted(event.target.value as 'all' | 'granted' | 'revoked')
                }
                className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="all">Todos</option>
                <option value="granted">Ativos</option>
                <option value="revoked">Revogados</option>
              </select>
              <button
                type="submit"
                disabled={loadingConsents}
                className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
              >
                {loadingConsents ? 'Carregando...' : 'Aplicar'}
              </button>
            </form>
          </div>

          {loadingConsents ? (
            <p className="py-12 text-center text-sm text-slate-500">Carregando consentimentos...</p>
          ) : consents.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
              Nenhum consentimento encontrado para os filtros atuais.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {consents.map((consent) => (
                <article
                  key={consent.id}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-1">
                      <h3 className="font-semibold text-slate-900">{consent.consent_type}</h3>
                      <p className="text-sm text-slate-600">{consent.purpose}</p>
                      <p className="text-xs text-slate-500">
                        Usuário {shortId(consent.user_id)} · {shortId(consent.policy_version)}
                      </p>
                    </div>
                    <div className="flex flex-col items-start gap-2">
                      <span
                        className={[
                          'rounded-full px-3 py-1 text-xs font-semibold',
                          consent.granted
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800',
                        ].join(' ')}
                      >
                        {consent.granted ? 'Ativo' : 'Revogado'}
                      </span>
                      <span className="text-xs text-slate-500">
                        Atualizado em {formatDate(consent.updated_at)}
                      </span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Eventos de segurança por tentativa</h2>
            <p className="mt-1 text-sm text-slate-600">
              Use o `attempt_id` de uma tentativa ou clique em uma entrada da trilha de auditoria
              para abrir os eventos associados.
            </p>
          </div>
        </div>

        <form onSubmit={handleSecuritySubmit} className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            value={attemptId}
            onChange={(event) => setAttemptId(event.target.value)}
            placeholder="Cole o attempt_id"
            className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={eventsLoading}
            className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
          >
            {eventsLoading ? 'Carregando...' : 'Buscar eventos'}
          </button>
        </form>

        {eventsError && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {eventsError}
          </div>
        )}

        {events.length > 0 ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {events.map((event) => (
              <article key={event.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <h3 className="font-semibold text-slate-900">{event.event_type}</h3>
                <p className="mt-1 text-xs text-slate-500">{formatDate(event.created_at)}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
            Nenhum evento carregado ainda.
          </p>
        )}
      </section>
    </div>
  );
}
