import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Providers from "./providers";
import Link from "next/link";
import { Box, Code } from "lucide-react";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Web2API",
  description: "Turn any website into an API",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} font-sans bg-zinc-950 text-zinc-50 min-h-screen antialiased`}>
        <Providers>
          <div className="flex flex-col min-h-screen">
            <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-50">
              <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 font-bold text-xl text-amber-500">
                  <Box className="h-6 w-6" />
                  <span>Web2API</span>
                </Link>
                
                <nav className="flex items-center gap-6 text-sm font-medium">
                  <Link href="/" className="hover:text-amber-500 transition-colors">
                    Dashboard
                  </Link>
                  <Link href="/monitors" className="hover:text-amber-500 transition-colors">
                    Monitors
                  </Link>
                  <Link href="/scrapers/new" className="hover:text-amber-500 transition-colors">
                    New Scraper
                  </Link>
                  <a href="https://www.motia.dev/docs" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-amber-500 transition-colors">
                    <Code className="h-4 w-4" />
                    Docs
                  </a>
                </nav>
              </div>
            </header>
            
            <main className="flex-1 container mx-auto px-4 py-8">
        {children}
            </main>
            
            <footer className="border-t border-zinc-800 py-6 mt-auto">
              <div className="container mx-auto px-4 text-center text-sm text-zinc-500">
                Built with Motia & Next.js
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
