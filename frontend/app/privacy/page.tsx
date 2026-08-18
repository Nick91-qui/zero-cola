'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  getMyPrivacyRequest,
  getPrivacyPolicy,
  requestAnonymization,
  type PrivacyPolicy,
  type PrivacyRequest,
} from '@/lib/privacy';

export default function PrivacyPage() {
  const [policy, setPolicy] = useState<PrivacyPolicy | null>(null);
  const [privacyRequest, setPrivacyRequest] = useState<PrivacyRequest | null>(null);
  const [requestLoading, setRequestLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [policyData, requestData] = await Promise.all([
          getPrivacyPolicy(),
          getMyPrivacyRequest().catch(() => null),
        ]);
        if (active) {
          setPolicy(policyData);
          setPrivacyRequest(requestData);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Falha ao carregar a política');
      } finally {
        if (active) setRequestLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <Link href="/dashboard" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Voltar ao painel
        </Link>
        <p className="mt-4 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Privacidade e LGPD
        </p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          {policy?.title || 'Política de Privacidade'}
        </h1>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      {message && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          {message}
        </div>
      )}

      <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          {!policy ? (
            <p className="text-sm text-slate-500">Carregando política...</p>
          ) : (
            <div className="space-y-6 text-sm text-slate-700">
              <p>{policy.summary}</p>
              <div>
                <h2 className="font-semibold text-slate-900">Eventos monitorados</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {policy.monitoring_events.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h2 className="font-semibold text-slate-900">Categorias de dados</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {policy.data_categories.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <p className="text-xs text-slate-500">
                Versão {policy.version} · atualizada em {new Date(policy.updated_at).toLocaleString('pt-BR')}
              </p>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Solicitação de conta</h2>
          <p className="mt-1 text-sm text-slate-600">
            Se quiser excluir sua conta, envie uma solicitação. O administrador decidirá se aprova
            a anonimização dos seus dados.
          </p>

          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            A exclusão não acontece automaticamente. O pedido entra em análise administrativa.
          </div>

          <div className="mt-4 space-y-3">
            <button
              type="button"
              onClick={async () => {
                setRequesting(true);
                setError(null);
                setMessage(null);
                try {
                  const result = await requestAnonymization();
                  setPrivacyRequest(result);
                  setMessage('Solicitação enviada para o administrador.');
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Falha ao solicitar exclusão');
                } finally {
                  setRequesting(false);
                }
              }}
              disabled={requesting || requestLoading || privacyRequest?.status === 'pending'}
              className="w-full rounded-md border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:bg-slate-100 disabled:text-slate-400"
            >
              {privacyRequest?.status === 'pending'
                ? 'Solicitação já enviada'
                : requesting
                  ? 'Enviando...'
                  : 'Solicitar exclusão da conta'}
            </button>

            {requestLoading ? (
              <p className="text-sm text-slate-500">Carregando solicitação...</p>
            ) : privacyRequest ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">
                  Status: {privacyRequest.status}
                </p>
                <p className="mt-1">Tipo: {privacyRequest.request_type}</p>
                <p className="mt-1">
                  Enviado em {new Date(privacyRequest.created_at).toLocaleString('pt-BR')}
                </p>
                {privacyRequest.reviewed_at ? (
                  <p className="mt-1">
                    Analisado em {new Date(privacyRequest.reviewed_at).toLocaleString('pt-BR')}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Nenhuma solicitação registrada.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
