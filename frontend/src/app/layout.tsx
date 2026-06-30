import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ReactQueryProvider } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  weight: ["300", "400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: {
    default: "TravelEngine — Compara vuelos, trenes y alojamientos",
    template: "%s | TravelEngine",
  },
  description:
    "Motor de agregación de viajes en tiempo real. Compara los mejores precios en vuelos, trenes y alojamientos de los principales proveedores.",
  keywords: ["vuelos baratos", "trenes", "hoteles", "comparador de viajes", "ofertas"],
  openGraph: {
    title: "TravelEngine",
    description: "Compara precios de viajes en tiempo real",
    type: "website",
    locale: "es_ES",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={inter.variable}>
      <body className="antialiased bg-neutral-50">
        <ReactQueryProvider>{children}</ReactQueryProvider>
      </body>
    </html>
  );
}
