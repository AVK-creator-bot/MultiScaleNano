import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MultiscaleNano — Free Nanotechnology Simulation Platform",
  description:
    "Design lipid nanoparticles and run real OpenMM molecular dynamics in your browser. Free, open source, for nanotechnology and drug delivery research.",
  openGraph: {
    title: "MultiscaleNano",
    description:
      "Free browser-based nanotechnology simulation — OpenMM MD for lipid nanoparticle research.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
