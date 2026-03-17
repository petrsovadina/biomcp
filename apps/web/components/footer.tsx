export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] py-12">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
          <div>
            <span className="text-lg font-bold text-white">
              <span className="text-blue-400">Czech</span>Med
              <span className="text-blue-400">MCP</span>
            </span>
            <p className="mt-1 text-sm text-white/40">
              Open source MCP server pro české zdravotnictví
            </p>
          </div>

          <div className="flex gap-8 text-sm text-white/40">
            <a href="https://czech-med-mcp-docs.vercel.app" className="transition hover:text-white">
              Dokumentace
            </a>
            <a
              href="https://github.com/petrsovadina/CzechMedMCP"
              target="_blank"
              rel="noopener"
              className="transition hover:text-white"
            >
              GitHub
            </a>
            <a
              href="https://github.com/petrsovadina/CzechMedMCP/issues"
              target="_blank"
              rel="noopener"
              className="transition hover:text-white"
            >
              Issues
            </a>
            <a
              href="https://medevio.com"
              target="_blank"
              rel="noopener"
              className="transition hover:text-white"
            >
              Medevio
            </a>
          </div>
        </div>

        <div className="mt-8 border-t border-white/[0.06] pt-8 text-center text-xs text-white/30">
          MIT {new Date().getFullYear()} &copy;{' '}
          <a
            href="https://github.com/petrsovadina"
            target="_blank"
            rel="noopener"
            className="underline underline-offset-4"
          >
            Petr Sovadina
          </a>
        </div>
      </div>
    </footer>
  )
}
