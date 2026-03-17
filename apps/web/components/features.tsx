import { FadeIn } from '@/components/fade-in'

const features = [
  {
    icon: '💊',
    title: 'SUKL',
    desc: 'Vyhledávání léků, dostupnost, SPC/PIL dokumenty, ATC klasifikace',
    count: '8 nástrojů',
    color: 'bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400',
  },
  {
    icon: '📋',
    title: 'MKN-10',
    desc: 'Diagnostické kódy, hierarchie, fulltextové vyhledávání v češtině',
    count: '4 nástroje',
    color: 'bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  },
  {
    icon: '🏥',
    title: 'NRPZS',
    desc: 'Registr poskytovatelů zdravotních služeb, vyhledávání lékařů',
    count: '4 nástroje',
    color: 'bg-violet-100 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400',
  },
  {
    icon: '💳',
    title: 'SZV + VZP',
    desc: 'Seznam zdravotních výkonů, úhrady VZP, bodové hodnoty',
    count: '4 nástroje',
    color: 'bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400',
  },
  {
    icon: '📖',
    title: 'PubMed & Trials',
    desc: '30M+ článků a 400K+ klinických studií přes standardní API',
    count: '12 nástrojů',
    color: 'bg-rose-100 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400',
  },
  {
    icon: '🧬',
    title: 'Genomika',
    desc: 'MyVariant.info, cBioPortal, OncoKB — varianty a mutace',
    count: '25 nástrojů',
    color: 'bg-cyan-100 dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
  },
]

export function Features() {
  return (
    <section id="funkce" className="border-t border-gray-200 dark:border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <FadeIn className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white md:text-4xl">
            60 nástrojů v jednom serveru
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-gray-500 dark:text-white/50">
            České zdravotnické registry i světové biomedicínské databáze —
            vše přístupné přes Model Context Protocol.
          </p>
        </FadeIn>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <FadeIn
              key={f.title}
              delay={i * 0.08}
              className="rounded-2xl border border-gray-200 dark:border-white/[0.08] bg-gray-50 dark:bg-white/[0.03] p-6 transition hover:border-gray-300 dark:hover:border-white/[0.15]"
            >
              <div className={`inline-flex rounded-xl p-3 text-2xl ${f.color}`}>
                {f.icon}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-500 dark:text-white/50">{f.desc}</p>
              <span className="mt-4 inline-block text-xs font-medium text-gray-400 dark:text-white/30">
                {f.count}
              </span>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
