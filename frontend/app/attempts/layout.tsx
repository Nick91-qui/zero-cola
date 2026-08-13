import { ReactNode } from 'react';
import { AttemptShell } from '@/app/components/AttemptShell';

export default function AttemptsLayout({ children }: { children: ReactNode }) {
  return <AttemptShell>{children}</AttemptShell>;
}
