import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title:
    "CustomsGuard | Autonomous Trade Compliance & Tariff Discrepancy Engine",
  description:
    "Air-gapped Indonesian customs tariff RAG across 5,612 HS-6 subheadings, Lartas permit verification, and CMA CGM Indonesia progressive demurrage modeling.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#ffffff] text-[#111111] selection:bg-[#111111] selection:text-white">
        {children}
      </body>
    </html>
  );
}
