'use client';

import { useEffect, useMemo, useState } from 'react';
import { searchUsers, type UserSearchResult } from '@/lib/users';

interface MemberSearchFieldProps {
  role: 'student' | 'teacher';
  title: string;
  helperText: string;
  placeholder: string;
  actionLabel: string;
  blockedIds?: string[];
  onSubmit: (selectedIds: string[]) => Promise<void>;
}

function formatUserLabel(user: UserSearchResult) {
  return user.student_code ? `${user.email} (${user.student_code})` : user.email;
}

export function MemberSearchField({
  role,
  title,
  helperText,
  placeholder,
  actionLabel,
  blockedIds = [],
  onSubmit,
}: MemberSearchFieldProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<UserSearchResult[]>([]);
  const [selected, setSelected] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedIds = useMemo(() => new Set(selected.map((item) => item.id)), [selected]);
  const blockedSet = useMemo(() => new Set(blockedIds), [blockedIds]);

  const handleQueryChange = (value: string) => {
    setQuery(value);
    if (value.trim().length < 2) {
      setResults([]);
    }
  };

  useEffect(() => {
    const trimmed = query.trim();
    let active = true;

    if (trimmed.length < 2) {
      return () => {
        active = false;
      };
    }

    const timeout = window.setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const users = await searchUsers({ q: trimmed, role, limit: 8 });
        if (!active) {
          return;
        }
        setResults(
          users.filter((user) => !blockedSet.has(user.id) && !selectedIds.has(user.id)),
        );
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Falha ao buscar usuários');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [blockedSet, query, role, selectedIds]);

  const addUser = (user: UserSearchResult) => {
    setSelected((current) => (current.some((item) => item.id === user.id) ? current : [...current, user]));
    setQuery('');
    setResults([]);
  };

  const removeUser = (userId: string) => {
    setSelected((current) => current.filter((item) => item.id !== userId));
  };

  const handleSubmit = async () => {
    if (selected.length === 0) {
      setError('Selecione ao menos um usuário.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await onSubmit(selected.map((item) => item.id));
      setSelected([]);
      setQuery('');
      setResults([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao vincular usuários');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="mt-1 text-sm text-slate-600">{helperText}</p>
        </div>
        <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm">
          {selected.length} selecionado(s)
        </span>
      </div>

      <label className="mt-4 block text-sm font-medium text-slate-700">
        Buscar usuário
        <input
          type="search"
          value={query}
          onChange={(event) => handleQueryChange(event.target.value)}
          placeholder={placeholder}
          className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none"
        />
      </label>

      <p className="mt-2 text-xs text-slate-500">Digite ao menos 2 caracteres para pesquisar por email ou código.</p>

      {loading && <p className="mt-3 text-sm text-slate-500">Buscando usuários...</p>}

      {results.length > 0 && (
        <div className="mt-3 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {results.map((user) => (
            <button
              key={user.id}
              type="button"
              aria-label="Adicionar"
              onClick={() => addUser(user)}
              className="flex w-full items-center justify-between gap-4 border-b border-slate-100 px-4 py-3 text-left text-sm text-slate-700 last:border-b-0 hover:bg-emerald-50"
            >
              <span>
                <span className="block font-medium text-slate-900">{formatUserLabel(user)}</span>
                <span className="block text-xs uppercase tracking-[0.18em] text-slate-500">
                  {user.role}
                </span>
              </span>
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                Adicionar
              </span>
            </button>
          ))}
        </div>
      )}

      {selected.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {selected.map((user) => (
            <button
              key={user.id}
              type="button"
              onClick={() => removeUser(user.id)}
              className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-100 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-200"
            >
              {formatUserLabel(user)}
              <span aria-hidden="true">×</span>
            </button>
          ))}
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting || selected.length === 0}
        className="mt-3 rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:bg-slate-300"
      >
        {submitting ? 'Vinculando...' : actionLabel}
      </button>
    </div>
  );
}
