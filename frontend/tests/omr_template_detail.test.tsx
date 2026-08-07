import type { ReactNode } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import OmrTemplateDetailPage from '../app/omr/[templateId]/page';
import * as omrLib from '@/lib/omr';

const routerPush = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
  useParams: () => ({ templateId: 'tmpl-1' }),
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

describe('OMR template detail page', () => {
  beforeEach(() => {
    routerPush.mockReset();
    vi.restoreAllMocks();
  });

  it('uploads a batch and shows the generated scans summary', async () => {
    const now = new Date().toISOString();
    const batchSpy = vi.spyOn(omrLib, 'uploadScanBatch').mockResolvedValue({
      omr_template_id: 'tmpl-1',
      source_filename: 'lote.pdf',
      total_pages: 2,
      scans: [
        {
          id: 'scan-1',
          omr_template_id: 'tmpl-1',
          student_code: '12345',
          student_id: 'student-1',
          status: 'success',
          image_url: '/tmp/scan-1.png',
          detected_answers: { '1': 'A' },
          raw_confidence: null,
          score: '10.00',
          error_message: null,
          processed_at: now,
          created_at: now,
          updated_at: now,
        },
        {
          id: 'scan-2',
          omr_template_id: 'tmpl-1',
          student_code: '23456',
          student_id: 'student-2',
          status: 'success',
          image_url: '/tmp/scan-2.png',
          detected_answers: { '1': 'B' },
          raw_confidence: null,
          score: '9.00',
          error_message: null,
          processed_at: now,
          created_at: now,
          updated_at: now,
        },
      ],
    });

    vi.spyOn(omrLib, 'getTemplate').mockResolvedValue({
      id: 'tmpl-1',
      title: 'Prova OMR em lote',
      exam_id: 'exam-1',
      layout_version: 'v1_std_20q',
      total_questions: 20,
      options_per_question: 5,
      correct_answers: { '1': 'A' },
      is_active: true,
      created_at: now,
      updated_at: now,
    });

    render(<OmrTemplateDetailPage />);

    await screen.findByText('Prova OMR em lote');

    const file = new File(['pdf-bytes'], 'lote.pdf', { type: 'application/pdf' });
    fireEvent.change(screen.getByLabelText(/arquivo pdf ou imagem/i), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar PDF / Lote' }));

    await waitFor(() => {
      expect(batchSpy).toHaveBeenCalledWith('tmpl-1', file);
      expect(screen.getByText(/2 página\(s\) processada\(s\) em lote\.pdf/)).toBeInTheDocument();
      expect(screen.getByText(/Página 1: 12345/)).toBeInTheDocument();
      expect(screen.getByText(/Página 2: 23456/)).toBeInTheDocument();
    });
  });
});
