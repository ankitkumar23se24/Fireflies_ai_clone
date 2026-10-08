import Link from 'next/link';
import { BarChart3, Calendar, Search, Settings, Sparkles, Video } from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/meetings', label: 'Meetings', icon: Calendar },
  { href: '/search', label: 'Search', icon: Search },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden w-72 border-r border-border bg-background/70 p-5 md:flex md:flex-col">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <div className="text-sm font-semibold">Meeting AI</div>
          <div className="text-xs text-muted-foreground">Workspace</div>
        </div>
      </div>

      <nav className="space-y-2">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="mt-auto rounded-2xl border border-dashed border-border bg-secondary/30 p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-medium">
          <Video className="h-4 w-4 text-primary" />
          AI meeting recap
        </div>
        <p className="text-xs text-muted-foreground">
          Auto-summarize calls and turn notes into action items with a single click.
        </p>
      </div>
    </aside>
  );
}
