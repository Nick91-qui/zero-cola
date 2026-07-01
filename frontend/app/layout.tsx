import type { Metadata } from 'next';
import { AuthProvider } from '@/app/context/AuthContext';
import './globals.css';

export const metadata: Metadata = {
  title: 'COLA-ZERO',
  description: 'Secure Online Assessment Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
