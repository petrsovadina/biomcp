import { FadeIn } from '@/components/fade-in'

export function CTA() {
  return (
    <section id="zacit" className="relative overflow-hidden border-t border-gray-200 dark:border-white/[0.06] py-24 md:py-32">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/4 top-0 h-[400px] w-[400px] rounded-full bg-blue-500/[0.08] blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-[300px] w-[300px] rounded-full bg-emerald-500/[0.06] blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <FadeIn>
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white md:text-5xl">
            Připraveni začít?
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg text-gray-400 dark:text-white/50">
            Jeden příkaz. Dva minuty. 60 nástrojů pro AI asistenta vašich
            lékařů.
          </p>

          {/* Code block - stays dark in both modes */}
          <div className="mx-auto mt-10 max-w-md overflow-hidden rounded-xl border border-white/[0.1] bg-[#0a0a0a] px-6 py-4 font-mono text-sm backdrop-blur">
            <span className="text-white/30">$</span>{' '}
            <span className="text-emerald-400">uv tool install git+https://github.com/petrsovadina/CzechMedMCP.git</span>
          </div>

          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="https://github.com/petrsovadina/CzechMedMCP"
              target="_blank"
              rel="noopener"
              className="w-full rounded-xl bg-gray-900 dark:bg-white px-8 py-4 text-center font-semibold text-white dark:text-[#030303] shadow-lg shadow-gray-900/10 dark:shadow-white/10 transition hover:bg-gray-800 dark:hover:bg-white/90 sm:w-auto"
            >
              Zobrazit na GitHub
            </a>
            <a
              href="https://czech-med-mcp-docs.vercel.app"
              className="w-full rounded-xl border border-gray-300 dark:border-white/[0.1] px-8 py-4 text-center font-semibold text-gray-600 dark:text-white/70 transition hover:border-gray-400 dark:hover:border-white/20 hover:text-gray-900 dark:hover:text-white sm:w-auto"
            >
              Dokumentace
            </a>
          </div>
        </FadeIn>
      </div>
    </section>
  )
}
