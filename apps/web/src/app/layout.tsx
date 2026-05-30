import "./globals.css";

import type { ReactNode } from "react";
import { Inter, JetBrains_Mono, Plus_Jakarta_Sans } from "next/font/google";

import { ToastContainer } from "@/components/ui/Toast";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata = {
  title: "Diagnóstico Inteligente — Asistente POC",
  description: "Asistente conversacional para diagnóstico técnico de motocicletas. Ingresa el bastidor y recibe diagnóstico guiado.",
  manifest: "/manifest.json",
  icons: {
    icon: "/design/logoApp.png",
  },
};

export const viewport = {
  themeColor: "#3B82F6",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html
      lang="es"
      className={`${inter.variable} ${jakarta.variable} ${jetbrains.variable}`}
    >
      <body className="bg-surface-primary font-body text-text-primary antialiased">
        {children}
        <ToastContainer />
      </body>
    </html>
  );
}
