'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/hooks/useAuth';
import { ProtectedRoute } from '@/app/components/ProtectedRoute';

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push('/auth/login');
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-50">
        <nav className="bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <h1 className="text-xl font-bold text-slate-900">COLA-ZERO</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-600">
                {user?.email} ({user?.role})
              </span>
              <button
                onClick={handleLogout}
                disabled={isLoading}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-400 text-xs text-white font-medium rounded-md transition"
              >
                Sair
              </button>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 mb-8">
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

          {user?.role === 'student' && (
            <div className="grid grid-cols-1 gap-6">
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
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
              {/* Card OMR */}
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
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

              {/* Card Avaliações & Relatórios */}
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
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
        </main>
      </div>
    </ProtectedRoute>
  );
}
