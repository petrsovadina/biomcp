'use client'

import { motion } from 'framer-motion'

const stats = [
  { value: '60', label: 'MCP nástrojů' },
  { value: '23', label: 'Českých zdrojů' },
  { value: '30M+', label: 'PubMed článků' },
  { value: '400K+', label: 'Klinických studií' },
]

export function Testimonial() {
  return (
    <section className="border-t border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-12 md:grid-cols-2 md:items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
              Čísla, která mluví
            </h2>
            <p className="mt-4 text-white/50 leading-relaxed">
              CzechMedMCP propojuje české zdravotnické registry se světovými
              biomedicínskými databázemi. Vše přístupné přes jeden MCP server —
              bez API klíčů, bez složité konfigurace.
            </p>
            <p className="mt-4 text-white/50 leading-relaxed">
              Postaveno pro platformu{' '}
              <a
                href="https://medevio.com"
                target="_blank"
                rel="noopener"
                className="font-medium text-white underline underline-offset-4"
              >
                Medevio
              </a>{' '}
              — AI asistent pro české lékaře.
            </p>
          </motion.div>

          <div className="grid grid-cols-2 gap-6">
            {stats.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 text-center"
              >
                <div className="text-3xl font-bold text-blue-400 md:text-4xl">
                  {s.value}
                </div>
                <div className="mt-2 text-sm text-white/40">
                  {s.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
