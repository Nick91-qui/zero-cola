'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getPrivacyPolicy, type PrivacyPolicy } from '@/lib/privacy';

export default function PrivacyPage() {
  const [policy, setPolicy] = useState<PrivacyPolicy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getPrivacyPolicy();
        if (active) setPolicy(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Falha ao carregar a política');
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-4xl">
        <Link href="/dashboard" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Voltar ao painel
        </Link>

        <section className="mt-4 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
            Privacidade e LGPD
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            {policy?.title || 'Política de Privacidade'}
          </h1>
          {error && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}
          {!policy ? (
            <p className="mt-4 text-sm text-slate-500">Carregando política...</p>
          ) : (
            <div className="mt-6 space-y-6 text-sm text-slate-700">
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
        </section>
      </div>
    </main>
  );
}
