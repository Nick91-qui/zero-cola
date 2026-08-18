'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ConfirmDialog } from '@/app/components/ConfirmDialog';
import { buildArchiveCopy } from '@/app/components/destructiveCopy';
import { useAuth } from '@/app/hooks/useAuth';
import {
  addStudentsToClass,
  addTeachersToClass,
  archiveClass,
  getClass,
  removeStudentFromClass,
  removeTeacherFromClass,
  listClasses,
  transferStudentBetweenClasses,
  type ClassDetail,
  type ClassSummary,
} from '@/lib/classes';
import { MemberSearchField } from './member-search-field';

function formatName(email: string, studentCode: string | null) {
  return studentCode ? `${email} (${studentCode})` : email;
}

export default function ClassDetailPage() {
  const params = useParams<{ classId: string }>();
  const classId = params.classId;
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [classData, setClassData] = useState<ClassDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [removingMembershipId, setRemovingMembershipId] = useState<string | null>(null);
  const [transferringStudentId, setTransferringStudentId] = useState<string>('');
  const [transferTargetClassId, setTransferTargetClassId] = useState<string>('');
  const [transferMessage, setTransferMessage] = useState<string | null>(null);
  const [archiveConfirmationOpen, setArchiveConfirmationOpen] = useState(false);
  const [classOptions, setClassOptions] = useState<ClassSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadClass = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [data, classList] = await Promise.all([
        getClass(classId),
        isAdmin ? listClasses(true).catch(() => []) : Promise.resolve([]),
      ]);
      setClassData(data);
      setClassOptions(classList.filter((item) => item.id !== classId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar turma');
    } finally {
      setLoading(false);
    }
  }, [classId]);

  useEffect(() => {
    void loadClass();
  }, [loadClass]);

  const handleArchive = async () => {
    setSaving(true);
    setError(null);

    try {
      const updated = await archiveClass(classId);
      setClassData((current) =>
        current
          ? {
              ...current,
              ...updated,
            }
          : current,
      );
      await loadClass();
      setArchiveConfirmationOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao arquivar turma');
    } finally {
      setSaving(false);
    }
  };

  const archiveCopy = classData ? buildArchiveCopy('a turma', classData.name) : null;

  const handleAddStudents = useCallback(
    async (studentIds: string[]) => {
      await addStudentsToClass(classId, studentIds);
      await loadClass();
    },
    [classId, loadClass],
  );

  const handleAddTeachers = useCallback(
    async (teacherIds: string[]) => {
      await addTeachersToClass(classId, teacherIds);
      await loadClass();
    },
    [classId, loadClass],
  );

  const activeStudents = useMemo(
    () => classData?.memberships.filter((membership) => membership.is_active) ?? [],
    [classData],
  );

  const availableTransferTargets = useMemo(
    () => classOptions.filter((item) => item.is_active),
    [classOptions],
  );

  const handleTransferStudent = async () => {
    if (!transferringStudentId || !transferTargetClassId) {
      setError('Escolha um estudante e uma turma de destino.');
      return;
    }

    setSaving(true);
    setError(null);
    setTransferMessage(null);

    try {
      await transferStudentBetweenClasses(classId, transferringStudentId, transferTargetClassId);
      setTransferMessage('Aluno transferido com sucesso.');
      setTransferringStudentId('');
      setTransferTargetClassId('');
      await loadClass();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao transferir estudante');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveStudent = async (studentId: string) => {
    setRemovingMembershipId(studentId);
    setError(null);

    try {
      await removeStudentFromClass(classId, studentId);
      await loadClass();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao remover estudante');
    } finally {
      setRemovingMembershipId(null);
    }
  };

  const handleRemoveTeacher = async (teacherId: string) => {
    setRemovingMembershipId(teacherId);
    setError(null);

    try {
      await removeTeacherFromClass(classId, teacherId);
      await loadClass();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao remover professor');
    } finally {
      setRemovingMembershipId(null);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/classes" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Voltar para Turmas
        </Link>
      </div>

      {loading ? (
        <p className="py-12 text-center text-sm text-slate-500">Carregando turma...</p>
      ) : error || !classData ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || 'Turma não encontrada.'}
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-3xl font-bold text-slate-900">{classData.name}</h1>
                <span
                  className={[
                    'rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]',
                    classData.is_active
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-200 text-slate-700',
                  ].join(' ')}
                >
                  {classData.is_active ? 'Ativa' : 'Arquivada'}
                </span>
              </div>
              <p className="max-w-3xl text-sm text-slate-600">
                {classData.description || 'Sem descrição cadastrada.'}
              </p>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Período
                  </span>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    {classData.academic_period || '—'}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Estudantes ativos
                  </span>
                  <p className="mt-2 text-2xl font-bold text-slate-900">{classData.student_count}</p>
                </div>
                {isAdmin ? (
                  <>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Professores vinculados
                      </span>
                      <p className="mt-2 text-2xl font-bold text-slate-900">
                        {classData.teachers.length}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        ID da turma
                      </span>
                      <p className="mt-2 break-all text-sm font-semibold text-slate-900">
                        {classData.id}
                      </p>
                    </div>
                  </>
                ) : null}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {isAdmin && classData.is_active && (
                <button
                  type="button"
                  onClick={() => setArchiveConfirmationOpen(true)}
                  disabled={saving}
                  className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 shadow-sm hover:bg-red-100 disabled:text-slate-400"
                >
                  Arquivar turma
                </button>
              )}
            </div>
          </div>

          <section className="grid gap-6 xl:grid-cols-2">
            {isAdmin ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Professores vinculados</h2>
                    <p className="mt-1 text-sm text-slate-600">Docentes desta turma.</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    {classData.teachers.length} vínculo(s)
                  </span>
                </div>

                <MemberSearchField
                  role="teacher"
                  title="Vincular professor(es)"
                  helperText="Busque docentes por e-mail para compartilhar o acesso à turma."
                  placeholder="Ex: professora@cola-zero.edu"
                  actionLabel="Vincular professores"
                  blockedIds={classData.teachers
                    .filter((membership) => membership.is_active)
                    .map((membership) => membership.teacher_id)}
                  onSubmit={handleAddTeachers}
                />

                {classData.teachers.length === 0 ? (
                  <p className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                    Nenhum professor vinculado.
                  </p>
                ) : (
                  <div className="mt-6 space-y-3">
                    {classData.teachers.map((membership) => (
                      <article
                        key={membership.id}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="font-semibold text-slate-900">
                              {membership.teacher ? membership.teacher.email : membership.teacher_id}
                            </p>
                            <p className="text-sm text-slate-600">
                              {membership.teacher?.role || 'teacher'}
                            </p>
                          </div>
                          <span
                            className={[
                              'rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-[0.15em]',
                              membership.is_active
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-slate-200 text-slate-700',
                            ].join(' ')}
                          >
                            {membership.is_active ? 'Ativo' : 'Arquivado'}
                          </span>
                        </div>
                        {membership.is_active && (
                          <button
                            type="button"
                            onClick={() => handleRemoveTeacher(membership.teacher_id)}
                            disabled={removingMembershipId === membership.teacher_id}
                            className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
                          >
                            {removingMembershipId === membership.teacher_id
                              ? 'Removendo...'
                              : 'Remover vínculo do professor'}
                          </button>
                        )}
                      </article>
                    ))}
                  </div>
                )}
              </div>
            ) : null}

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">Estudantes vinculados</h2>
                  <p className="mt-1 text-sm text-slate-600">Alunos desta turma.</p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  {classData.memberships.length} vínculo(s)
                </span>
              </div>

              {isAdmin ? (
                <div className="mt-5 rounded-xl border border-sky-200 bg-sky-50 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900">Transferir estudante</h3>
                      <p className="mt-1 text-sm text-slate-600">
                        A matrícula atual é inativada e o aluno passa para a turma destino com
                        trilha de auditoria.
                      </p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm">
                      {activeStudents.length} ativo(s)
                    </span>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Estudante
                      <select
                        value={transferringStudentId}
                        onChange={(event) => setTransferringStudentId(event.target.value)}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none"
                      >
                        <option value="">Selecione um estudante</option>
                        {activeStudents.map((membership) => (
                          <option key={membership.id} value={membership.student_id}>
                            {membership.student ? formatName(membership.student.email, membership.student.student_code) : membership.student_id}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="block text-sm font-medium text-slate-700">
                      Turma destino
                      <select
                        value={transferTargetClassId}
                        onChange={(event) => setTransferTargetClassId(event.target.value)}
                        className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none"
                      >
                        <option value="">Selecione a turma</option>
                        {availableTransferTargets.map((targetClass) => (
                          <option key={targetClass.id} value={targetClass.id}>
                            {targetClass.name}
                            {targetClass.academic_period ? ` · ${targetClass.academic_period}` : ''}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={handleTransferStudent}
                      disabled={
                        saving ||
                        activeStudents.length === 0 ||
                        availableTransferTargets.length === 0 ||
                        !transferringStudentId ||
                        !transferTargetClassId
                      }
                      className="rounded-md bg-sky-700 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-600 disabled:bg-slate-300"
                    >
                      {saving ? 'Transferindo...' : 'Transferir aluno'}
                    </button>
                    <p className="text-xs text-slate-500">
                      Use esse fluxo para promoção anual ou troca de turma sem perder histórico.
                    </p>
                  </div>
                </div>
              ) : null}

              {transferMessage ? (
                <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  {transferMessage}
                </div>
              ) : null}

              {isAdmin ? (
                <MemberSearchField
                  role="student"
                  title="Vincular estudante(s)"
                  helperText="Busque estudantes por e-mail ou código para adicionar à turma."
                  placeholder="Ex: aluno@cola-zero.edu ou 12345"
                  actionLabel="Vincular estudantes"
                  blockedIds={classData.memberships
                    .filter((membership) => membership.is_active)
                    .map((membership) => membership.student_id)}
                  onSubmit={handleAddStudents}
                />
              ) : null}

              {classData.memberships.length === 0 ? (
                <p className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                  Nenhum estudante vinculado.
                </p>
              ) : (
                  <div className="mt-6 space-y-3">
                    {classData.memberships.map((membership) => (
                      <article
                      key={membership.id}
                      className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-900">
                            {membership.student
                              ? formatName(
                                  membership.student.email,
                                  membership.student.student_code,
                                )
                              : membership.student_id}
                          </p>
                          <p className="text-sm text-slate-600">
                            {membership.academic_period || 'Sem período'}
                          </p>
                        </div>
                        <span
                          className={[
                            'rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-[0.15em]',
                            membership.is_active
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-200 text-slate-700',
                          ].join(' ')}
                        >
                          {membership.is_active ? 'Ativo' : 'Arquivado'}
                        </span>
                      </div>
                      {isAdmin && membership.is_active && (
                        <button
                          type="button"
                          onClick={() => handleRemoveStudent(membership.student_id)}
                          disabled={removingMembershipId === membership.student_id}
                          className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
                        >
                          {removingMembershipId === membership.student_id
                            ? 'Removendo...'
                            : 'Remover vínculo do estudante'}
                        </button>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>
          <ConfirmDialog
            open={archiveConfirmationOpen}
            title={archiveCopy?.title ?? 'Arquivar turma?'}
            message={archiveCopy?.message ?? `Arquivar a turma ${classData.name}?`}
            warning={archiveCopy?.warning}
            confirmLabel={saving ? 'Arquivando...' : archiveCopy?.confirmLabel ?? 'Confirmar arquivamento'}
            busy={saving}
            onConfirm={handleArchive}
            onCancel={() => setArchiveConfirmationOpen(false)}
          />
        </>
      )}
    </div>
  );
}
