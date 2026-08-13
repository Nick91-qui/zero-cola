'use client';

import Link from 'next/link';
import { useAuth } from '@/app/hooks/useAuth';

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Painel de Controle</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-slate-700 mt-4">
          <div className="bg-slate-50 p-3.5 rounded-md border border-slate-200">
            <span className="block text-xs font-semibold text-slate-500 uppercase">Usuário</span>
            <span className="font-semibold text-slate-900">{user?.email}</span>
          </div>
          <div className="bg-slate-50 p-3.5 rounded-md border border-slate-200">
            <span className="block text-xs font-semibold text-slate-500 uppercase">Função</span>
            <span className="font-semibold text-slate-900 capitalize">{user?.role}</span>
          </div>
          {user?.student_code && (
            <div className="bg-slate-50 p-3.5 rounded-md border border-slate-200">
              <span className="block text-xs font-semibold text-slate-500 uppercase">Matrícula (5 dígitos)</span>
              <span className="font-semibold text-slate-900">{user.student_code}</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900">Privacidade</h3>
          <p className="mt-2 text-sm text-slate-600">
            Consulte a política pública, exporte seus dados e acompanhe consentimentos.
          </p>
          <Link
            href="/privacy"
            className="mt-4 inline-flex w-full items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Abrir privacidade
          </Link>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900">Consentimentos</h3>
          <p className="mt-2 text-sm text-slate-600">
            Gerencie o consentimento de monitoramento antes das provas online.
          </p>
          <Link
            href="/consents"
            className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600"
          >
            Ver consentimentos
          </Link>
        </div>

        {user?.role === 'admin' && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900">Administração</h3>
            <p className="mt-2 text-sm text-slate-600">
              Acesse usuários, turmas e auditoria em um ponto único.
            </p>
            <Link
              href="/admin"
              className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600"
            >
              Abrir administração
            </Link>
          </div>
        )}

        {user?.role === 'admin' && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900">Auditoria</h3>
            <p className="mt-2 text-sm text-slate-600">
              Acompanhe eventos sensíveis, logs administrativos e sinais de segurança.
            </p>
            <Link
              href="/admin/audit"
              className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
            >
              Abrir auditoria
            </Link>
          </div>
        )}
      </div>

      {user?.role === 'student' && (
        <div className="grid grid-cols-1 gap-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-slate-900">Provas Online</h3>
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                Tentativas Sequenciais
              </span>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              Inicie uma avaliação online usando o código do exame, responda uma questão por vez e acompanhe seu resultado final ao submeter a prova.
            </p>
            <Link
              href="/attempts/start"
              className="inline-flex items-center justify-center w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600 transition"
            >
              Iniciar Prova Online →
            </Link>
          </div>
        </div>
      )}

      {(user?.role === 'teacher' || user?.role === 'admin') && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-slate-900">Turmas</h3>
              <span className="bg-sky-100 text-sky-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                Matrículas e vínculos
              </span>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              Organize turmas, acompanhe vínculos de professores e estudantes e abra o detalhe para ver o histórico da composição da classe.
            </p>
            <Link
              href="/classes"
              className="inline-flex items-center justify-center w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 transition"
            >
              Abrir Turmas →
            </Link>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-slate-900">Gabaritos OMR</h3>
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                Correção de Cartões
              </span>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              Crie gabaritos com título amigável, gere folhas PDF para impressão e realize a correção automatizada por foto ou scanner.
            </p>
            <Link
              href="/omr"
              className="inline-flex items-center justify-center w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600 transition"
            >
              Abrir Módulo OMR →
            </Link>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-slate-900">Avaliações & Relatórios</h3>
              <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                Análise Pedagógica
              </span>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              Acompanhe médias por turma, estatísticas por questão (% acertos), vinculação com matriz de habilidades BNCC e baixe relatórios PDF / Excel.
            </p>
            <div className="grid gap-3">
              <Link
                href="/exams/new"
                className="inline-flex items-center justify-center w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-600 transition"
              >
                Criar Prova Online →
              </Link>
              <Link
                href="/exams"
                className="inline-flex items-center justify-center w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 transition"
              >
                Gerenciar Avaliações & Exportar →
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
