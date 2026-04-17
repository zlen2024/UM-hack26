import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'UM CRM',
  description: 'Simple CRM Application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}