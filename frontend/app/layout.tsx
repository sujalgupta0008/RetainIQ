import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider, ThemeScript } from "@/lib/theme";
import AppShell from "@/components/AppShell";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const jbmono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jbmono", display: "swap" });

export const metadata: Metadata = {
  title: "RetainIQ — Retention ROI Intelligence",
  description: "AI-powered retention & ROI intelligence for financial institutions.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="light" suppressHydrationWarning>
      <body className={`${jakarta.variable} ${inter.variable} ${jbmono.variable} font-sans antialiased`}>
        <ThemeScript />
        <div className="canvas-bg" aria-hidden />
        <div className="canvas-grid" aria-hidden />
        <ThemeProvider>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
