'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useAuth } from '@/app/hooks/useAuth';
import {
  addStudentsToClass,
  addTeachersToClass,
  listClasses,
  type ClassSummary,
} from '@/lib/classes';
import {
  archiveUser,
  createUser,
  deleteUser,
  listUsers,
  type UserSearchResult,
} from '@/lib/users';
import {
  approvePrivacyRequest,
  listPrivacyRequests,
  rejectPrivacyRequest,
  type PrivacyRequest,
} from '@/lib/privacy';
import { ConfirmDialog } from '@/app/components/ConfirmDialog';

type AdminUserRole = 'student' | 'teacher';
type DirectoryRoleFilter = 'all' | 'student' | 'teacher' | 'admin';

export default function AdminUsersPage() {
  const { user } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [role, setRole] = useState<AdminUserRole>('teacher');
  const [studentCode, setStudentCode] = useState('');
  const [classSearch, setClassSearch] = useState('');
  const [selectedClassIds, setSelectedClassIds] = useState<string[]>([]);
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [loadingClasses, setLoadingClasses] = useState(true);

  const [users, setUsers] = useState<UserSearchResult[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [privacyRequests, setPrivacyRequests] = useState<PrivacyRequest[]>([]);
  const [loadingPrivacyRequests, setLoadingPrivacyRequests] = useState(true);
  const [directorySearch, setDirectorySearch] = useState('');
  const [directoryRoleFilter, setDirectoryRoleFilter] = useState<DirectoryRoleFilter>('all');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isReviewingRequest, setIsReviewingRequest] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<
    | { kind: 'archive'; target: UserSearchResult }
    | { kind: 'delete'; target: UserSearchResult }
    | null
  >(null);
  const [pendingPrivacyAction, setPendingPrivacyAction] = useState<
    | { kind: 'approve'; target: PrivacyRequest }
    | { kind: 'reject'; target: PrivacyRequest }
    | null
  >(null);

  const loadClasses = async () => {
    try {
      setLoadingClasses(true);
      const data = await listClasses(false);
      setClasses(data);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Falha ao carregar turmas');
    } finally {
      setLoadingClasses(false);
    }
  };

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const data = await listUsers({ include_inactive: true, limit: 100 });
      setUsers(data);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Falha ao carregar usuarios');
    } finally {
      setLoadingUsers(false);
    }
  };

  const loadPrivacyRequests = async () => {
    try {
      setLoadingPrivacyRequests(true);
      const data = await listPrivacyRequests();
      setPrivacyRequests(data);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Falha ao carregar solicitações');
    } finally {
      setLoadingPrivacyRequests(false);
    }
  };

  useEffect(() => {
    void loadClasses();
    void loadUsers();
    void loadPrivacyRequests();
  }, []);

  const teacherLookup = useMemo(() => {
    return new Map(users.filter((item) => item.role === 'teacher').map((item) => [item.id, item]));
  }, [users]);

  const filteredUsers = useMemo(() => {
    const search = directorySearch.trim().toLowerCase();
    return users.filter((item) => {
      const matchesRole = directoryRoleFilter === 'all' || item.role === directoryRoleFilter;
      if (!matchesRole) return false;
      if (!search) return true;
      const haystack = [item.email, item.student_code ?? '', item.role].join(' ').toLowerCase();
      return haystack.includes(search);
    });
  }, [directoryRoleFilter, directorySearch, users]);

  const filteredClasses = useMemo(() => {
    const search = classSearch.trim().toLowerCase();
    if (!search) return classes;
    return classes.filter((classItem) => {
      const haystack = [classItem.name, classItem.academic_period ?? '', classItem.description ?? '']
        .join(' ')
        .toLowerCase();
      return haystack.includes(search);
    });
  }, [classSearch, classes]);

  const toggleClass = (classId: string) => {
    setSelectedClassIds((current) =>
      current.includes(classId) ? current.filter((id) => id !== classId) : [...current, classId],
    );
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setPasswordConfirm('');
    setStudentCode('');
    setSelectedClassIds([]);
    setClassSearch('');
  };

  const refreshAll = async () => {
    await Promise.all([loadClasses(), loadUsers(), loadPrivacyRequests()]);
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);

    if (!email || !password || !passwordConfirm) {
      setLocalError('Todos os campos são obrigatórios.');
      return;
    }

    if (password.length < 8) {
      setLocalError('A senha deve ter pelo menos 8 caracteres.');
      return;
    }

    if (password !== passwordConfirm) {
      setLocalError('As senhas não conferem.');
      return;
    }

    if (role === 'student' && !/^\d{5}$/.test(studentCode)) {
      setLocalError('O código do aluno deve ter exatamente 5 dígitos.');
      return;
    }

    setIsSubmitting(true);

    try {
      const created = await createUser({
        email,
        password,
        role,
        student_code: role === 'student' ? studentCode : null,
      });

      if (selectedClassIds.length > 0) {
        const payload = [created.id];
        await Promise.all(
          selectedClassIds.map((classId) =>
            role === 'teacher'
              ? addTeachersToClass(classId, payload)
              : addStudentsToClass(classId, payload),
          ),
        );
      }

      const roleLabel = role === 'student' ? 'Aluno' : 'Professor';
      setSuccessMessage(
        selectedClassIds.length > 0
          ? `${roleLabel} ${created.email} criado e vinculado com sucesso.`
          : `${roleLabel} ${created.email} criado com sucesso.`,
      );
      resetForm();
      await refreshAll();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Falha ao criar usuario');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleArchiveUser = async (target: UserSearchResult) => {
    if (target.id === user?.id) {
      setLocalError('Você não pode inativar sua própria conta. Solicite ao administrador.');
      return;
    }
    setPendingAction({ kind: 'archive', target });
  };

  const handleDeleteUser = async (target: UserSearchResult) => {
    if (target.id === user?.id) {
      setLocalError('Você não pode excluir a própria conta. Solicite ao administrador.');
      return;
    }
    setPendingAction({ kind: 'delete', target });
  };

  const confirmPendingAction = async () => {
    if (!pendingAction) return;

    const { kind, target } = pendingAction;
    setIsConfirming(true);
    setLocalError(null);
    setSuccessMessage(null);

    try {
      if (kind === 'archive') {
        await archiveUser(target.id);
        setSuccessMessage(`Usuário ${target.email} inativado com sucesso.`);
      } else {
        await deleteUser(target.id);
        setSuccessMessage(`Usuário ${target.email} excluído com sucesso.`);
      }
      await loadUsers();
      setPendingAction(null);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Falha ao executar ação');
    } finally {
      setIsConfirming(false);
    }
  };

  const handleApprovePrivacyRequest = (target: PrivacyRequest) => {
    setPendingPrivacyAction({ kind: 'approve', target });
  };

  const handleRejectPrivacyRequest = (target: PrivacyRequest) => {
    setPendingPrivacyAction({ kind: 'reject', target });
  };

  const confirmPendingPrivacyAction = async () => {
    if (!pendingPrivacyAction) return;

    const { kind, target } = pendingPrivacyAction;
    setIsReviewingRequest(true);
    setLocalError(null);
    setSuccessMessage(null);

    try {
      if (kind === 'approve') {
        await approvePrivacyRequest(target.id);
        setSuccessMessage(`Solicitação de ${target.user.email} aprovada e anonimizada.`);
      } else {
        await rejectPrivacyRequest(target.id);
        setSuccessMessage(`Solicitação de ${target.user.email} rejeitada.`);
      }
      await loadPrivacyRequests();
      await loadUsers();
      setPendingPrivacyAction(null);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Falha ao revisar solicitação');
    } finally {
      setIsReviewingRequest(false);
    }
  };

  const assignmentLabel =
    role === 'student'
      ? 'Matricular aluno nas turmas selecionadas'
      : 'Vincular professor às turmas selecionadas';

  const stats = useMemo(() => {
    const activeUsers = users.filter((item) => item.is_active);
    return {
      total: users.length,
      active: activeUsers.length,
      teachers: activeUsers.filter((item) => item.role === 'teacher').length,
      students: activeUsers.filter((item) => item.role === 'student').length,
      admins: activeUsers.filter((item) => item.role === 'admin').length,
    };
  }, [users]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Usuários</h1>
        <p className="mt-2 max-w-4xl text-sm text-slate-600">
          Crie contas de professor ou aluno, vincule turmas e gerencie inativação ou exclusão com
          contexto claro.
        </p>
        <p className="mt-2 max-w-4xl text-xs text-slate-500">
          A própria conta não pode ser excluída ou inativada diretamente por quem está logado.
          Qualquer solicitação desse tipo deve ser avaliada por um administrador.
        </p>
      </div>

      {(localError || successMessage) && (
        <div
          className={[
            'rounded-lg px-4 py-3 text-sm',
            localError
              ? 'border border-red-200 bg-red-50 text-red-700'
              : 'border border-emerald-200 bg-emerald-50 text-emerald-700',
          ].join(' ')}
        >
          {localError || successMessage}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Total</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{stats.total}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Ativos</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{stats.active}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Professores
          </p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{stats.teachers}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Alunos</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{stats.students}</p>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Solicitações de exclusão</h2>
            <p className="mt-1 text-sm text-slate-600">
              Pedidos enviados pelos usuários para análise administrativa.
            </p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
            {loadingPrivacyRequests ? 'Carregando...' : `${privacyRequests.length} pendência(s)`}
          </span>
        </div>

        {loadingPrivacyRequests ? (
          <p className="mt-6 text-sm text-slate-500">Carregando solicitações...</p>
        ) : privacyRequests.length === 0 ? (
          <p className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
            Nenhuma solicitação pendente.
          </p>
        ) : (
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {privacyRequests.map((request) => (
              <article key={request.id} className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900">
                      {request.user.email}
                    </h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {request.user.role}
                      {request.user.student_code ? ` · ${request.user.student_code}` : ''}
                    </p>
                  </div>
                  <span className="rounded-full bg-white px-2.5 py-0.5 text-xs font-semibold uppercase tracking-[0.15em] text-slate-600">
                    {request.status}
                  </span>
                </div>

                <p className="mt-3 text-sm text-slate-700">
                  Solicitado em {new Date(request.created_at).toLocaleString('pt-BR')}
                </p>
                {request.reason ? (
                  <p className="mt-2 text-sm text-slate-700">{request.reason}</p>
                ) : null}

                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => handleApprovePrivacyRequest(request)}
                    className="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-600"
                  >
                    Aprovar
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRejectPrivacyRequest(request)}
                    className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Rejeitar
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1fr_1.05fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">Novo usuário</h2>
            <p className="mt-1 text-sm text-slate-600">
              Crie professor ou aluno e já faça o vínculo com as turmas corretas.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isSubmitting}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                placeholder="user@email.com"
                required
              />
            </div>

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-slate-700">
                Papel
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as AdminUserRole)}
                disabled={isSubmitting}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
              >
                <option value="teacher">Professor</option>
                <option value="student">Aluno</option>
              </select>
            </div>

            {role === 'student' && (
              <div>
                <label htmlFor="studentCode" className="block text-sm font-medium text-slate-700">
                  Código do aluno
                </label>
                <input
                  id="studentCode"
                  type="text"
                  inputMode="numeric"
                  pattern="\d{5}"
                  maxLength={5}
                  value={studentCode}
                  onChange={(e) => setStudentCode(e.target.value.replace(/\D/g, '').slice(0, 5))}
                  disabled={isSubmitting}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                  placeholder="10234"
                  required
                />
                <p className="mt-1 text-xs text-slate-500">
                  Exatamente 5 dígitos, usado na prova OMR.
                </p>
              </div>
            )}

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                Senha
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isSubmitting}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                placeholder="••••••••"
                minLength={8}
                required
              />
            </div>

            <div>
              <label htmlFor="passwordConfirm" className="block text-sm font-medium text-slate-700">
                Confirmar senha
              </label>
              <input
                id="passwordConfirm"
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                disabled={isSubmitting}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
                placeholder="••••••••"
                minLength={8}
                required
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-md bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
            >
              {isSubmitting ? 'Criando...' : 'Criar usuário'}
            </button>
          </form>

          <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Turmas selecionadas</p>
            <p className="mt-1 text-sm text-slate-600">{assignmentLabel}</p>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Turmas para vínculo</h2>
              <p className="mt-1 text-sm text-slate-600">
                Selecione as turmas que serão vinculadas ao usuário criado.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {selectedClassIds.length} selecionada(s)
            </span>
          </div>

          <label className="block text-sm font-medium text-slate-700">
            Buscar turma
            <input
              type="search"
              value={classSearch}
              onChange={(e) => setClassSearch(e.target.value)}
              placeholder="Nome, período ou descrição"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
            />
          </label>

      {loadingClasses ? (
            <p className="mt-6 text-sm text-slate-500">Carregando turmas...</p>
          ) : filteredClasses.length === 0 ? (
            <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="text-sm text-slate-500">
                Nenhuma turma encontrada. Vá em{' '}
                <Link href="/classes" className="font-semibold text-emerald-700 hover:underline">
                  Turmas
                </Link>{' '}
                para criar ou revisar as turmas.
              </p>
            </div>
          ) : (
            <div className="mt-5 grid gap-3">
              {filteredClasses.map((classItem) => {
                const checked = selectedClassIds.includes(classItem.id);
                const teacher = classItem.teacher_id ? teacherLookup.get(classItem.teacher_id) : undefined;
                return (
                  <label
                    key={classItem.id}
                    className={[
                      'flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 transition',
                      checked
                        ? 'border-emerald-300 bg-emerald-50'
                        : 'border-slate-200 bg-slate-50 hover:border-emerald-300',
                    ].join(' ')}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleClass(classItem.id)}
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                    />
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900">{classItem.name}</span>
                        <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                          {classItem.academic_period || 'sem período'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">
                        Professor: {teacher?.email || 'sem professor vinculado'}
                      </p>
                      {classItem.description && (
                        <p className="mt-1 text-sm text-slate-600">{classItem.description}</p>
                      )}
                    </div>
                  </label>
                );
              })}
            </div>
          )}
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Usuários cadastrados</h2>
            <p className="mt-1 text-sm text-slate-600">
              Veja professores, alunos e administradores. Use a busca para localizar contas
              específicas.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {(['all', 'teacher', 'student', 'admin'] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setDirectoryRoleFilter(value)}
                className={[
                  'rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition',
                  directoryRoleFilter === value
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200',
                ].join(' ')}
              >
                {value === 'all' ? 'Todos' : value}
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-[1fr_auto]">
          <input
            type="search"
            value={directorySearch}
            onChange={(e) => setDirectorySearch(e.target.value)}
            placeholder="Buscar por email, matrícula ou papel"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => setDirectorySearch('')}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Limpar
          </button>
        </div>

        {loadingUsers ? (
          <p className="mt-6 text-sm text-slate-500">Carregando usuários...</p>
        ) : filteredUsers.length === 0 ? (
          <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <p className="text-sm text-slate-500">Nenhum usuário encontrado.</p>
          </div>
        ) : (
          <div className="mt-5 overflow-hidden rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-4 py-3">Usuário</th>
                  <th className="px-4 py-3">Papel</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Matrícula</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredUsers.map((item) => {
                  const isSelf = item.id === user?.id;
                  return (
                    <tr key={item.id} className="align-top">
                      <td className="px-4 py-4">
                        <div className="font-medium text-slate-900">{item.email}</div>
                        <div className="mt-1 text-xs text-slate-500">{item.id}</div>
                      </td>
                      <td className="px-4 py-4 capitalize text-slate-700">{item.role}</td>
                      <td className="px-4 py-4">
                        <span
                          className={[
                            'rounded-full px-2.5 py-0.5 text-xs font-semibold',
                            item.is_active
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-200 text-slate-700',
                          ].join(' ')}
                        >
                          {item.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-slate-700">{item.student_code || '—'}</td>
                      <td className="px-4 py-4">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => void handleArchiveUser(item)}
                            disabled={!item.is_active || isSelf}
                            className="rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-800 hover:bg-amber-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
                          >
                            Inativar
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleDeleteUser(item)}
                            disabled={isSelf}
                            className="rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="text-lg font-semibold text-slate-900">Turmas cadastradas</h2>
          <p className="mt-1 text-sm text-slate-600">
            Veja rapidamente quem coordena cada turma e abra o detalhe para conferir o vínculo
            turma &gt; aluno.
          </p>
        </div>

        {loadingClasses ? (
          <p className="text-sm text-slate-500">Carregando turmas...</p>
        ) : classes.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <p className="text-sm text-slate-500">Nenhuma turma cadastrada.</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {classes.map((classItem) => {
              const teacher = classItem.teacher_id ? teacherLookup.get(classItem.teacher_id) : undefined;
              return (
                <article
                  key={classItem.id}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-base font-semibold text-slate-900">{classItem.name}</h3>
                      <p className="mt-1 text-sm text-slate-600">
                        {classItem.academic_period || 'Sem período informado'}
                      </p>
                    </div>
                    <span
                      className={[
                        'rounded-full px-2.5 py-0.5 text-xs font-semibold',
                        classItem.is_active
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-200 text-slate-700',
                      ].join(' ')}
                    >
                      {classItem.is_active ? 'Ativa' : 'Arquivada'}
                    </span>
                  </div>

                  <p className="mt-3 text-sm text-slate-700">
                    Professor: {teacher?.email || 'sem professor vinculado'}
                  </p>
                  <p className="mt-1 text-sm text-slate-700">{classItem.student_count} aluno(s)</p>

                  {classItem.description && (
                    <p className="mt-3 text-sm text-slate-600">{classItem.description}</p>
                  )}

                  <Link
                    href={`/classes/${classItem.id}`}
                    className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800"
                  >
                    Abrir detalhe da turma
                  </Link>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <ConfirmDialog
        open={pendingAction !== null}
        title={
          pendingAction?.kind === 'delete'
            ? 'Excluir usuário?'
            : 'Inativar usuário?'
        }
        message={
          pendingAction?.kind === 'delete'
            ? `Excluir definitivamente ${pendingAction.target.email}?`
            : `Inativar ${pendingAction?.target.email}?`
        }
        warning={
          pendingAction?.kind === 'delete'
            ? 'Essa ação remove o acesso e anonimiza os dados pessoais do usuário. Registros acadêmicos associados podem permanecer para histórico.'
            : 'O usuário perde acesso, mas os dados permanecem.'
        }
        confirmLabel={pendingAction?.kind === 'delete' ? 'Confirmar exclusão' : 'Confirmar inativação'}
        busy={isConfirming}
        onConfirm={confirmPendingAction}
        onCancel={() => setPendingAction(null)}
      />

      <ConfirmDialog
        open={pendingPrivacyAction !== null}
        title={
          pendingPrivacyAction?.kind === 'approve'
            ? 'Aprovar exclusão?'
            : 'Rejeitar exclusão?'
        }
        message={
          pendingPrivacyAction?.kind === 'approve'
            ? `Aprovar a anonimização da conta de ${pendingPrivacyAction.target.user.email}?`
            : `Rejeitar a solicitação de ${pendingPrivacyAction?.target.user.email}?`
        }
        warning={
          pendingPrivacyAction?.kind === 'approve'
            ? 'A conta será anonimizada e o usuário perderá acesso ao sistema.'
            : 'A solicitação será marcada como rejeitada e o usuário continuará com acesso.'
        }
        confirmLabel={
          pendingPrivacyAction?.kind === 'approve'
            ? 'Confirmar aprovação'
            : 'Confirmar rejeição'
        }
        busy={isReviewingRequest}
        onConfirm={confirmPendingPrivacyAction}
        onCancel={() => setPendingPrivacyAction(null)}
      />
    </div>
  );
}
