'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'

const links = [
  { label: 'Funkce', href: '#funkce' },
  { label: 'Nástroje', href: '#nastroje' },
  { label: 'Jak to funguje', href: '#jak-to-funguje' },
  { label: 'Dokumentace', href: 'https://docs-sovadina.vercel.app' },
]

export function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 z-50 w-full border-b border-white/[0.06] bg-[#030303]/80 backdrop-blur-xl"
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="/" className="text-lg font-bold text-white">
          <span className="text-blue-400">Czech</span>Med
          <span className="text-blue-400">MCP</span>
        </a>

        <div className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-white/50 transition hover:text-white"
            >
              {l.label}
            </a>
          ))}
          <a
            href="https://github.com/petrsovadina/biomcp"
            target="_blank"
            rel="noopener"
            className="rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/20"
          >
            GitHub
          </a>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="text-white/60 md:hidden"
          aria-label="Menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {open ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {open && (
        <div className="border-t border-white/[0.06] px-6 py-4 md:hidden">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block py-2 text-sm text-white/50 transition hover:text-white"
            >
              {l.label}
            </a>
          ))}
        </div>
      )}
    </motion.nav>
  )
}
