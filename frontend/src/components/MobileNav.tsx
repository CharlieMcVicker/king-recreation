"use client";

import { useState } from "react";
import Link from "next/link";
import {
  LayoutDashboard,
  Search,
  GitCompare,
  Menu,
  X,
  BookA,
  RefreshCw,
  BarChart3,
} from "lucide-react";

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);

  const toggle = () => setIsOpen(!isOpen);

  return (
    <>
      <header className="md:hidden flex items-center justify-between p-4 border-b border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <h1 className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
          Match Explorer
        </h1>
        <button
          onClick={toggle}
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <Menu className="w-6 h-6" />
        </button>
      </header>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={toggle}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`fixed top-0 left-0 bottom-0 w-64 bg-white dark:bg-zinc-900 z-50 transform transition-transform duration-300 ease-in-out border-r border-gray-200 dark:border-zinc-800 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-6 border-b border-gray-200 dark:border-zinc-800 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
              Match Explorer
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Linguistic Analysis Tool
            </p>
          </div>
          <button
            onClick={toggle}
            className="p-2 -mr-2 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="p-4 space-y-1">
          <Link
            href="/"
            onClick={toggle}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </Link>
          <Link
            href="/explorer"
            onClick={toggle}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <Search className="w-4 h-4" />
            Class Explorer
          </Link>
          <Link
            href="/compare"
            onClick={toggle}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <GitCompare className="w-4 h-4" />
            Comparison Tool
          </Link>
          <Link
            href="/reconstruction"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-emerald-600 dark:text-emerald-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Reconstruction
          </Link>
          <Link
            href="/failures"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <div className="w-4 h-4 flex items-center justify-center">
              <span className="text-xs font-bold text-red-500">!</span>
            </div>
            Derivation Failures
          </Link>
          <Link
            href="/analysis"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <div className="w-4 h-4 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-indigo-500" />
            </div>
            Reconstruction Analysis
          </Link>
          <Link
            href="/search"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-gray-600 dark:text-zinc-400 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <BookA className="w-4 h-4" />
            Dictionary Search
          </Link>
        </nav>
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-zinc-800">
          <div className="flex items-center gap-3 px-3 py-2 text-xs font-medium text-gray-500 dark:text-zinc-500">
            v1.0.0-beta
          </div>
        </div>
      </aside>
    </>
  );
}
