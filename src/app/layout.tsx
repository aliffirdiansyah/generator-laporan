import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Laporan Bulanan",
  description: "Buat PDF surat lamaran dan laporan kegiatan",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
