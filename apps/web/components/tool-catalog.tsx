import { FadeIn } from '@/components/fade-in'

const tools = [
  { name: 'czechmed_search_medicine', group: 'SUKL', desc: 'Vyhledání léku podle názvu nebo účinné látky' },
  { name: 'czechmed_get_medicine_detail', group: 'SUKL', desc: 'Detail léku včetně SPC a PIL' },
  { name: 'czechmed_check_availability', group: 'SUKL', desc: 'Kontrola dostupnosti léku v lékárnách' },
  { name: 'czechmed_search_diagnosis', group: 'MKN-10', desc: 'Vyhledání diagnózy podle kódu nebo popisu' },
  { name: 'czechmed_browse_diagnosis', group: 'MKN-10', desc: 'Procházení hierarchie MKN-10' },
  { name: 'czechmed_search_providers', group: 'NRPZS', desc: 'Vyhledání poskytovatele zdravotních služeb' },
  { name: 'czechmed_search_procedures', group: 'SZV', desc: 'Vyhledání zdravotních výkonů' },
  { name: 'czechmed_diagnosis_assist', group: 'Workflow', desc: 'Asistovaná diagnostika s MKN-10 kódy' },
  { name: 'search_articles', group: 'Global', desc: 'Prohledání 30M+ PubMed článků' },
  { name: 'search_trials', group: 'Global', desc: 'Vyhledání klinických studií' },
  { name: 'search_variants', group: 'Global', desc: 'Genomické varianty z MyVariant.info' },
  { name: 'get_drug_info', group: 'Global', desc: 'Informace o léku z OpenFDA' },
]

const groupColors: Record<string, string> = {
  'SUKL': 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  'MKN-10': 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  'NRPZS': 'bg-violet-500/15 text-violet-400 border-violet-500/20',
  'SZV': 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  'Workflow': 'bg-rose-500/15 text-rose-400 border-rose-500/20',
  'Global': 'bg-white/5 text-white/50 border-white/10',
}

export function ToolCatalog() {
  return (
    <section id="nastroje" className="border-t border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <FadeIn className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            Ukázka nástrojů
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/50">
            12 z 60 dostupných nástrojů. Každý přijímá strukturované parametry
            a vrací formátovaný markdown.
          </p>
        </FadeIn>

        <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tools.map((t, i) => (
            <FadeIn
              key={t.name}
              delay={i * 0.05}
              direction="left"
              className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-4 transition hover:border-white/[0.15]"
            >
              <div className="flex items-start justify-between gap-2">
                <code className="text-sm font-medium text-white/90">{t.name}</code>
                <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${groupColors[t.group]}`}>
                  {t.group}
                </span>
              </div>
              <p className="mt-2 text-xs text-white/40">{t.desc}</p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
