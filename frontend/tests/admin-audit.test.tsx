import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import AuditPage from '../app/admin/audit/page';
import * as auditLib from '@/lib/audit';
import * as consentsLib from '@/lib/consents';

describe('Admin audit page', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.spyOn(auditLib, 'listAuditLogs').mockResolvedValue([
      {
        id: 'log-1',
        user_id: 'user-1',
        event_type: 'consent.updated',
        resource_type: 'consent',
        resource_id: 'consent-1',
        details: null,
        ip_address: null,
        user_agent: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 'log-2',
        user_id: 'user-2',
        event_type: 'security_event.recorded',
        resource_type: 'attempt',
        resource_id: 'attempt-1',
        details: null,
        ip_address: null,
        user_agent: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    vi.spyOn(consentsLib, 'listAdminConsents').mockResolvedValue([
      {
        id: 'consent-1',
        user_id: 'student-1',
        consent_type: 'monitoring',
        purpose: 'online_exam_monitoring',
        granted: true,
        granted_at: new Date().toISOString(),
        revoked_at: null,
        policy_version: 'step9-v1',
        details: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    vi.spyOn(auditLib, 'listSecurityEvents').mockResolvedValue([
      {
        id: 'security-1',
        attempt_id: 'attempt-1',
        event_type: 'blur',
        details: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
  });

  it('renders logs, consents and attempt security events', async () => {
    render(<AuditPage />);

    expect(await screen.findByText('consent.updated')).toBeInTheDocument();
    expect(screen.getByText('monitoring')).toBeInTheDocument();
    expect(screen.getByText('Consentimentos ativos')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Ver eventos da tentativa' }));

    await waitFor(() => {
      expect(auditLib.listSecurityEvents).toHaveBeenCalledWith('attempt-1');
      expect(screen.getByText('blur')).toBeInTheDocument();
    });
  });
});
