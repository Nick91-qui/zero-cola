import { ReactNode } from 'react';
import { AcademicShell } from '@/app/components/AcademicShell';

export default function QuestionsLayout({ children }: { children: ReactNode }) {
  return <AcademicShell>{children}</AcademicShell>;
}
