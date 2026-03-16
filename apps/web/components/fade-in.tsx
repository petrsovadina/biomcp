'use client'

import { useRef, useEffect, type ReactNode } from 'react'

interface FadeInProps {
  children: ReactNode
  className?: string
  delay?: number
  direction?: 'up' | 'left' | 'right' | 'scale'
}

export function FadeIn({
  children,
  className = '',
  delay = 0,
  direction = 'up',
}: FadeInProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.transitionDelay = `${delay}s`
          el.classList.add('fade-in-visible')
          observer.unobserve(el)
        }
      },
      { threshold: 0.1 },
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [delay])

  const dirClass =
    direction === 'left'
      ? 'fade-in-left'
      : direction === 'right'
        ? 'fade-in-right'
        : direction === 'scale'
          ? 'fade-in-scale'
          : 'fade-in-up'

  return (
    <div ref={ref} className={`fade-in ${dirClass} ${className}`}>
      {children}
    </div>
  )
}
