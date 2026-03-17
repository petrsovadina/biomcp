import { FadeIn } from '@/components/fade-in'

const stats = [
  { value: '60', label: 'MCP nástrojů' },
  { value: '23', label: 'Českých zdrojů' },
  { value: '30M+', label: 'PubMed článků' },
  { value: '400K+', label: 'Klinických studií' },
]

export function Testimonial() {
  return (
    <section className="border-t border-gray-200 dark:border-white/[0.06] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-12 md:grid-cols-2 md:items-center">
          <FadeIn direction="left">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white md:text-4xl">
              Čísla, která mluví
            </h2>
            <p className="mt-4 text-gray-600 dark:text-white/50 leading-relaxed">
              CzechMedMCP propojuje české zdravotnické registry se světovými
              biomedicínskými databázemi. Vše přístupné přes jeden MCP server —
              bez API klíčů, bez složité konfigurace.
            </p>
          </FadeIn>

          <div className="grid grid-cols-2 gap-6">
            {stats.map((s, i) => (
              <FadeIn
                key={s.label}
                delay={i * 0.1}
                direction="scale"
                className="rounded-2xl border border-gray-200 dark:border-white/[0.08] bg-gray-50 dark:bg-white/[0.03] p-6 text-center"
              >
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 md:text-4xl">
                  {s.value}
                </div>
                <div className="mt-2 text-sm text-gray-500 dark:text-white/40">
                  {s.label}
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
