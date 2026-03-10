'use client'

import { motion } from 'framer-motion'

const items = [
  {
    problem: 'Ruční vyhledávání v SUKL databázi',
    solution: 'AI najde lék, zkontroluje dostupnost a porovná alternativy za sekundy',
  },
  {
    problem: 'Kopírování kódů z MKN-10 tabulek',
    solution: 'Přirozený dotaz v češtině → přesný kód s hierarchií',
  },
  {
    problem: 'Přepínání mezi PubMed, ClinicalTrials a dalšími',
    solution: 'Jeden AI asistent prohledá všechny zdroje najednou',
  },
  {
    problem: 'Žádné AI nástroje pro české zdravotnictví',
    solution: '23 nástrojů specificky pro SUKL, MKN-10, NRPZS, SZV a VZP',
  },
]

export function ProblemSolution() {
  return (
    <section className="border-t border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            Problém → Řešení
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/50">
            AI asistenti jsou mocní, ale bez přístupu k českým zdravotnickým
            datům jsou slepí. CzechMedMCP jim dává oči.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-6 md:grid-cols-2">
          {items.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6"
            >
              <p className="text-white/40 line-through decoration-red-400/50">
                {item.problem}
              </p>
              <p className="mt-3 font-semibold text-white">
                {item.solution}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
