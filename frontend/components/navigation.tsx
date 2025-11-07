'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './theme-toggle'

export function Navigation() {
  const pathname = usePathname()

  const navItems = [
    { href: '/upload', label: 'Upload' },
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/rca', label: 'RCA Analysis' },
    { href: '/ask-ai', label: 'Ask AI' },
    { href: '/help', label: 'Help' },
  ]

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-8">
          <Link href="/" className="text-xl font-bold">
            LTE Band 41 RCA
          </Link>
          <div className="flex space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'text-sm font-medium transition-colors hover:text-primary',
                  pathname === item.href
                    ? 'text-foreground'
                    : 'text-muted-foreground'
                )}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
        <ThemeToggle />
      </div>
    </nav>
  )
}

