'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

export type ShellSearchItem = {
  href: string;
  label: string;
  hint: string;
  keywords?: string[];
};

export interface ShellSearchProps {
  id: string;
  items: ShellSearchItem[];
  placeholder?: string;
}

function normalizeText(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

export function ShellSearch({ id, items, placeholder = 'Busca global' }: ShellSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const filteredItems = useMemo(() => {
    const normalizedQuery = normalizeText(query);

    if (!normalizedQuery) {
      return items.slice(0, 6);
    }

    return items
      .filter((item) => {
        const searchable = [item.label, item.hint, ...(item.keywords ?? [])]
          .map(normalizeText)
          .join(' ');
        return searchable.includes(normalizedQuery);
      })
      .slice(0, 6);
  }, [items, query]);

  function openFirstMatch() {
    const target = filteredItems[activeIndex] ?? filteredItems[0];
    if (target) {
      router.push(target.href);
      setQuery('');
      setIsOpen(false);
      setActiveIndex(0);
    }
  }

  return (
    <div className="relative w-full">
      <label className="sr-only" htmlFor={id}>
        {placeholder}
      </label>
      <input
        id={id}
        type="search"
        value={query}
        placeholder={placeholder}
        autoComplete="off"
        className="w-full rounded-full border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-500"
        onChange={(event) => {
          setQuery(event.target.value);
          setIsOpen(true);
          setActiveIndex(0);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            openFirstMatch();
          }
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            setIsOpen(true);
            setActiveIndex((current) => Math.min(current + 1, Math.max(filteredItems.length - 1, 0)));
          }
          if (event.key === 'ArrowUp') {
            event.preventDefault();
            setActiveIndex((current) => Math.max(current - 1, 0));
          }
          if (event.key === 'Escape') {
            setIsOpen(false);
          }
        }}
      />

      {isOpen && filteredItems.length > 0 ? (
        <div className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-30 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
          <div className="border-b border-slate-100 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Resultados
          </div>
          <ul className="max-h-80 overflow-auto py-2">
            {filteredItems.map((item, index) => {
              const active = index === activeIndex;
              return (
                <li key={item.href}>
                  <button
                    type="button"
                    className={[
                      'flex w-full items-start justify-between gap-4 px-4 py-3 text-left transition',
                      active ? 'bg-emerald-50' : 'hover:bg-slate-50',
                    ].join(' ')}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => {
                      router.push(item.href);
                      setQuery('');
                      setIsOpen(false);
                      setActiveIndex(0);
                    }}
                  >
                    <span>
                      <span className="block text-sm font-semibold text-slate-900">{item.label}</span>
                      <span className="mt-0.5 block text-xs text-slate-500">{item.hint}</span>
                    </span>
                    <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500">
                      {item.href}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
