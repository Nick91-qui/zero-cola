'use client';

import { FormEvent, useEffect, useState } from 'react';
import { listAuditLogs, listSecurityEvents, type AuditLog, type SecurityEvent } from '@/lib/audit';

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [attemptId, setAttemptId] = useState('');
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eventsError, setEventsError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await listAuditLogs({ limit: 50 });
        if (active) setLogs(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Falha ao carregar auditoria');
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  const handleLoadEvents = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!attemptId.trim()) return;
    setEventsLoading(true);
    setEventsError(null);
    try {
      const data = await listSecurityEvents(attemptId.trim());
      setEvents(data);
    } catch (err) {
      setEventsError(err instanceof Error ? err.message : 'Falha ao carregar eventos');
    } finally {
      setEventsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Auditoria</h1>
        <p className="mt-2 max-w-4xl text-sm text-slate-600">
          Consulte eventos sensíveis da aplicação e rastreie sinais de segurança por tentativa
          online.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Logs administrativos</h2>
              <p className="mt-1 text-sm text-slate-600">
                Eventos sensíveis capturados pela trilha de auditoria.
              </p>
            </div>
            <span className="text-xs text-slate-500">
              {loading ? 'Carregando...' : `${logs.length} registro(s)`}
            </span>
          </div>

          {loading ? (
            <p className="py-12 text-center text-sm text-slate-500">Carregando logs...</p>
          ) : logs.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
              Nenhum log encontrado.
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {logs.map((log) => (
                <article key={log.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-900">{log.event_type}</h3>
                      <p className="text-sm text-slate-600">
                        {log.resource_type || 'sem recurso'} {log.resource_id || ''}
                      </p>
                    </div>
                    <p className="text-xs text-slate-500">
                      {new Date(log.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Eventos de segurança por tentativa</h2>
            <p className="mt-1 text-sm text-slate-600">
              Digite um `attempt_id` para carregar os eventos observados durante a prova.
            </p>
          </div>

          <form onSubmit={handleLoadEvents} className="mt-4 space-y-3">
            <input
              value={attemptId}
              onChange={(event) => setAttemptId(event.target.value)}
              placeholder="Cole o attempt_id"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900"
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

          {events.length > 0 && (
            <div className="mt-4 space-y-3">
              {events.map((event) => (
                <article key={event.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="font-semibold text-slate-900">{event.event_type}</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    {new Date(event.created_at).toLocaleString('pt-BR')}
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
