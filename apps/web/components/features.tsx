'use client'

import { motion } from 'framer-motion'
import { Pill, FileText, Building2, CreditCard, BookOpen, Dna } from 'lucide-react'

const features = [
  {
    icon: Pill,
    title: 'SUKL',
    desc: 'Vyhledávání léků, dostupnost, SPC/PIL dokumenty, ATC klasifikace',
    count: '8 nástrojů',
    color: 'bg-blue-500/10 text-blue-400',
  },
  {
    icon: FileText,
    title: 'MKN-10',
    desc: 'Diagnostické kódy, hierarchie, fulltextové vyhledávání v češtině',
    count: '4 nástroje',
    color: 'bg-emerald-500/10 text-emerald-400',
  },
  {
    icon: Building2,
    title: 'NRPZS',
    desc: 'Registr poskytovatelů zdravotních služeb, vyhledávání lékařů',
    count: '4 nástroje',
    color: 'bg-violet-500/10 text-violet-400',
  },
  {
    icon: CreditCard,
    title: 'SZV + VZP',
    desc: 'Seznam zdravotních výkonů, úhrady VZP, bodové hodnoty',
    count: '4 nástroje',
    color: 'bg-amber-500/10 text-amber-400',
  },
  {
    icon: BookOpen,
    title: 'PubMed & Trials',
    desc: '30M+ článků a 400K+ klinických studií přes standardní API',
    count: '12 nástrojů',
    color: 'bg-rose-500/10 text-rose-400',
  },
  {
    icon: Dna,
    title: 'Genomika',
    desc: 'MyVariant.info, cBioPortal, OncoKB — varianty a mutace',
    count: '25 nástrojů',
    color: 'bg-cyan-500/10 text-cyan-400',
  },
]

export function Features() {
  return (
    <section id="funkce" className="border-t border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            60 nástrojů v jednom serveru
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/50">
            České zdravotnické registry i světové biomedicínské databáze —
            vše přístupné přes Model Context Protocol.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 transition hover:border-white/[0.15]"
            >
              <div className={`inline-flex rounded-xl p-3 ${f.color}`}>
                <f.icon className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/50">{f.desc}</p>
              <span className="mt-4 inline-block text-xs font-medium text-white/30">
                {f.count}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
