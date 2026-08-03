import type { ReactNode } from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import DashboardPage from '../app/dashboard/page';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

vi.mock('@/app/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock('@/app/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { email: 'teacher@cola-zero.edu', role: 'teacher' },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

describe('Dashboard navigation', () => {
  it('exposes the classes entry point for teachers', () => {
    render(<DashboardPage />);

    expect(screen.getByText('Turmas')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Abrir Turmas/i })).toHaveAttribute('href', '/classes');
  });
});
