import { ReactNode } from 'react';
import { AcademicShell } from '@/app/components/AcademicShell';

export default function ClassesLayout({ children }: { children: ReactNode }) {
  return <AcademicShell>{children}</AcademicShell>;
}
