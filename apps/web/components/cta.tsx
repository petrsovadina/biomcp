'use client'

import { motion } from 'framer-motion'

export function CTA() {
  return (
    <section id="zacit" className="relative overflow-hidden border-t border-white/[0.06] py-24 md:py-32">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/4 top-0 h-[400px] w-[400px] rounded-full bg-blue-500/[0.08] blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-[300px] w-[300px] rounded-full bg-emerald-500/[0.06] blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-5xl">
            Připraveni začít?
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg text-white/50">
            Jeden příkaz. Dva minuty. 60 nástrojů pro AI asistenta vašich
            lékařů.
          </p>

          <div className="mx-auto mt-10 max-w-md overflow-hidden rounded-xl border border-white/[0.1] bg-white/[0.03] px-6 py-4 font-mono text-sm backdrop-blur">
            <span className="text-white/30">$</span>{' '}
            <span className="text-emerald-400">pip install czechmedmcp</span>
          </div>

          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="https://github.com/petrsovadina/biomcp"
              target="_blank"
              rel="noopener"
              className="w-full rounded-xl bg-white px-8 py-4 text-center font-semibold text-[#030303] shadow-lg shadow-white/10 transition hover:bg-white/90 sm:w-auto"
            >
              Zobrazit na GitHub
            </a>
            <a
              href="https://docs-sovadina.vercel.app"
              className="w-full rounded-xl border border-white/[0.1] px-8 py-4 text-center font-semibold text-white/70 transition hover:border-white/20 hover:text-white sm:w-auto"
            >
              Dokumentace
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
