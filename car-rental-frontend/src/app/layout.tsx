import type { Metadata } from 'next';
//import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

//const _geist = Geist({ subsets: ['latin'] });
//const _geistMono = Geist_Mono({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'DriveEase - Car Rental System',
  description: 'Modern car rental management system for seamless booking experiences',
  icons: {
    icon: [{ url: '/favicon.ico', sizes: 'any' }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
