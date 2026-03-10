'use client'

import { motion } from 'framer-motion'

const fadeUp = {
  hidden: { opacity: 0, y: 30, filter: 'blur(10px)' },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.8, delay: 0.2 + i * 0.15, ease: [0.25, 0.4, 0.25, 1] as const },
  }),
}

export function Hero() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-[#030303] flex items-center justify-center">
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          animate={{ y: [0, 15, 0] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute left-[-10%] top-[20%] h-[140px] w-[600px] rotate-12 rounded-full bg-gradient-to-r from-blue-500/[0.15] to-transparent border-2 border-white/[0.1] backdrop-blur-sm"
        />
        <motion.div
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          className="absolute right-[-5%] top-[70%] h-[120px] w-[500px] -rotate-[15deg] rounded-full bg-gradient-to-r from-emerald-500/[0.12] to-transparent border-2 border-white/[0.08] backdrop-blur-sm"
        />
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
          className="absolute right-[20%] top-[10%] h-[60px] w-[200px] rotate-[20deg] rounded-full bg-gradient-to-r from-amber-500/[0.1] to-transparent border-2 border-white/[0.06]"
        />
      </div>

      <div className="absolute inset-0 bg-gradient-to-t from-[#030303] via-transparent to-[#030303]/80" />

      <div className="relative z-10 mx-auto max-w-4xl px-6 text-center">
        <motion.div
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-1.5"
        >
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-sm tracking-wide text-white/60">
            Open source &middot; MIT licence &middot; 60 AI nástrojů
          </span>
        </motion.div>

        <motion.h1
          custom={1}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="text-5xl font-bold tracking-tight sm:text-6xl md:text-7xl lg:text-8xl"
        >
          <span className="bg-gradient-to-b from-white to-white/80 bg-clip-text text-transparent">
            AI napojení na
          </span>
          <br />
          <span className="bg-gradient-to-r from-blue-300 via-white/90 to-emerald-300 bg-clip-text text-transparent">
            české zdravotnictví
          </span>
        </motion.h1>

        <motion.p
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mx-auto mt-8 max-w-xl text-lg leading-relaxed font-light tracking-wide text-white/40 md:text-xl"
        >
          CzechMedMCP propojuje Claude, Cursor a další AI asistenty s SUKL,
          MKN-10, PubMed a dalšími zdroji. Jeden server, jeden protokol.
        </motion.p>

        <motion.div
          custom={3}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <a
            href="#zacit"
            className="w-full rounded-xl bg-white px-8 py-4 text-center font-semibold text-[#030303] shadow-lg shadow-white/10 transition hover:bg-white/90 sm:w-auto"
          >
            Začít za 2 minuty
          </a>
          <a
            href="https://github.com/petrsovadina/biomcp"
            target="_blank"
            rel="noopener"
            className="w-full rounded-xl border border-white/10 px-8 py-4 text-center font-semibold text-white/70 transition hover:border-white/20 hover:text-white sm:w-auto"
          >
            GitHub
          </a>
        </motion.div>

        <motion.div
          custom={4}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mx-auto mt-20 max-w-2xl"
        >
          <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.03] shadow-2xl backdrop-blur-sm">
            <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
              <div className="h-3 w-3 rounded-full bg-red-500/80" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <div className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs text-white/30">terminal</span>
            </div>
            <div className="p-6 text-left font-mono text-sm leading-relaxed">
              <p className="text-white/30"># Instalace za 10 sekund</p>
              <p className="text-emerald-400">$ pip install czechmedmcp</p>
              <p className="mt-4 text-white/30"># Spuštění MCP serveru</p>
              <p className="text-emerald-400">$ czechmedmcp run</p>
              <p className="mt-2 text-white/50">
                CzechMedMCP v0.7.3 — 60 nástrojů připraveno
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
