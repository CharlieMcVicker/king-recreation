import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { LayoutDashboard, Search, GitCompare, Menu, BookA } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "King Match Explorer",
  description: "Linguistic analysis of King's classes",
};

import MobileNav from "@/components/MobileNav";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 dark:bg-zinc-950`}>
        <div className="flex min-h-screen">
          {/* Sidebar (Desktop) */}
          <aside className="w-64 border-r border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hidden md:flex flex-col fixed inset-y-0">
            <div className="p-6 border-b border-gray-200 dark:border-zinc-800">
              <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">Match Explorer</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Linguistic Analysis Tool</p>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              <Link href="/" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors">
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link href="/explorer" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors">
                <Search className="w-4 h-4" />
                Class Explorer
              </Link>
              <Link href="/compare" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors">
                <GitCompare className="w-4 h-4" />
                Comparison Tool
              </Link>
              <Link href="/search" className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors">
                <BookA className="w-4 h-4" />
                Dictionary Search
              </Link>
            </nav>
            <div className="p-4 border-t border-gray-200 dark:border-zinc-800">
              <div className="flex items-center gap-3 px-3 py-2 text-xs font-medium text-gray-500 dark:text-zinc-500">
                v1.0.0-beta
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 flex flex-col min-w-0 md:pl-64">
            {/* Header for mobile */}
            <MobileNav />
            
            <div className="flex-1 p-6 overflow-auto">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
