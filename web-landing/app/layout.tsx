import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://cg.rafifmsn.com"),
  title: {
    default:
      "CustomsGuard | Autonomous Trade Compliance & Tariff Discrepancy Engine",
    template: "%s | CustomsGuard",
  },
  description:
    "Air-gapped Indonesian customs tariff RAG across 5,612 HS-6 subheadings, mandatory Lartas permit verification (SDPPI, Kemenkes, BPOM), and progressive CMA CGM Indonesia demurrage modeling.",
  keywords: [
    "Customs compliance Indonesia",
    "Harmonized System tariff audit",
    "Indonesian HS-6 subheadings",
    "Lartas permit verification",
    "SDPPI type approval",
    "BPOM import license",
    "Kemenkes distribution license",
    "CMA CGM demurrage detention calculator",
    "Tanjung Priok customs clearance",
    "Autonomous trade compliance AI",
  ],
  authors: [{ name: "CustomsGuard Engineering" }],
  creator: "CustomsGuard",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
  openGraph: {
    title:
      "CustomsGuard | Autonomous Trade Compliance & Tariff Discrepancy Engine",
    description:
      "Eliminate customs Red-Lane holds before cargo reaches port. Air-gapped Indonesian tariff RAG across 5,612 HS-6 codes and CMA CGM demurrage engine.",
    url: "https://cg.rafifmsn.com",
    siteName: "CustomsGuard",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title:
      "CustomsGuard | Autonomous Trade Compliance & Tariff Discrepancy Engine",
    description:
      "Autonomous Indonesian customs tariff RAG and CMA CGM container demurrage calculation.",
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap"
          rel="stylesheet"
        />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body className="min-h-screen bg-[#121212] font-sans text-[#F8FAFC] selection:bg-[#A78BFA] selection:text-[#0B0B0F] antialiased">
        {children}
      </body>
    </html>
  );
}
