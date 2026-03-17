import { FadeIn } from '@/components/fade-in'

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
    <section className="border-t border-gray-200 dark:border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <FadeIn className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white md:text-4xl">
            Problém → Řešení
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-gray-500 dark:text-white/50">
            AI asistenti jsou mocní, ale bez přístupu k českým zdravotnickým
            datům jsou slepí. CzechMedMCP jim dává oči.
          </p>
        </FadeIn>

        <div className="mt-16 grid gap-6 md:grid-cols-2">
          {items.map((item, i) => (
            <FadeIn
              key={i}
              delay={i * 0.1}
              className="rounded-2xl border border-gray-200 dark:border-white/[0.08] bg-gray-50 dark:bg-white/[0.03] p-6"
            >
              <p className="text-gray-400 dark:text-white/40 line-through decoration-red-500 dark:decoration-red-400/50">
                {item.problem}
              </p>
              <p className="mt-3 font-semibold text-gray-900 dark:text-white">
                {item.solution}
              </p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
