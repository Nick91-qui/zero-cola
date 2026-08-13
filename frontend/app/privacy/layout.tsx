import { ReactNode } from 'react';
import { PortalShell } from '@/app/components/PortalShell';

export default function PrivacyLayout({ children }: { children: ReactNode }) {
  return <PortalShell>{children}</PortalShell>;
}
