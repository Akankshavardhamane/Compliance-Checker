import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Legal Metrology Compliance Checker",
  description: "AI-based compliance analysis for packaged product labels.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen flex flex-col text-gray-900`}>
        <Navigation />
        <main className="flex-grow">
          {children}
        </main>
      </body>
    </html>
  );
}
