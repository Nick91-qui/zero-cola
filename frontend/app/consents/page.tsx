'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';
import { useAuth } from '@/app/hooks/useAuth';
import { listMyConsents, upsertMonitoringConsent, type Consent } from '@/lib/consents';
import { exportMyData, requestAnonymization } from '@/lib/privacy';

export default function ConsentsPage() {
  const { user, logout } = useAuth();
  const [consents, setConsents] = useState<Consent[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const data = await listMyConsents();
      setConsents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar consentimentos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleMonitoringConsent = async () => {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await upsertMonitoringConsent({
        granted: true,
        purpose: 'online_exam_monitoring',
        details: { source: 'frontend', context: 'consents-page' },
      });
      setMessage('Consentimento de monitoramento registrado.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao registrar consentimento');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const result = await exportMyData();
      setMessage(`Exportação carregada com ${Object.keys(result.data).length} bloco(s) de dados.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao exportar dados');
    } finally {
      setSaving(false);
    }
  };

  const handleAnonymize = async () => {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const result = await requestAnonymization();
      setMessage(`Pedido concluído para o usuário ${result.user_id}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao solicitar anonimização');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-50">
        <nav className="border-b border-slate-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" className="text-lg font-bold text-slate-900">
                COLA-ZERO
              </Link>
              <span className="rounded bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-800">
                LGPD
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

        <main className="mx-auto max-w-5xl px-4 py-10">
          <h1 className="text-3xl font-bold text-slate-900">Consentimentos e dados</h1>
          <p className="mt-2 text-sm text-slate-600">
            Controle o consentimento de monitoramento, exporte seus dados e acompanhe o histórico.
          </p>

          {error && (
            <div className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}
          {message && (
            <div className="mt-6 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
              {message}
            </div>
          )}

          <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Ações rápidas</h2>
              <div className="mt-4 space-y-3">
                <button
                  type="button"
                  onClick={handleMonitoringConsent}
                  disabled={saving}
                  className="w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
                >
                  Registrar consentimento de monitoramento
                </button>
                <button
                  type="button"
                  onClick={handleExport}
                  disabled={saving}
                  className="w-full rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:bg-slate-100"
                >
                  Exportar meus dados
                </button>
                <button
                  type="button"
                  onClick={handleAnonymize}
                  disabled={saving}
                  className="w-full rounded-md border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:bg-slate-100"
                >
                  Solicitar anonimização
                </button>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-slate-900">Meus consentimentos</h2>
                <span className="text-xs text-slate-500">
                  {loading ? 'Carregando...' : `${consents.length} registro(s)`}
                </span>
              </div>

              {loading ? (
                <p className="py-12 text-center text-sm text-slate-500">Carregando consentimentos...</p>
              ) : consents.length === 0 ? (
                <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                  Nenhum consentimento registrado.
                </p>
              ) : (
                <div className="mt-4 space-y-3">
                  {consents.map((consent) => (
                    <article key={consent.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-slate-900">{consent.consent_type}</h3>
                          <p className="text-sm text-slate-600">{consent.purpose}</p>
                        </div>
                        <span
                          className={[
                            'rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-[0.15em]',
                            consent.granted ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700',
                          ].join(' ')}
                        >
                          {consent.granted ? 'Concedido' : 'Revogado'}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">
                        Atualizado em {new Date(consent.updated_at).toLocaleString('pt-BR')}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
