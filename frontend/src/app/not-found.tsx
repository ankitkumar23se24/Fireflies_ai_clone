import Link from 'next/link';

import { Button } from '@/components/ui/button';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
      <div className="text-sm uppercase tracking-[0.2em] text-muted-foreground">404</div>
      <h1 className="text-3xl font-semibold">This meeting isn’t in your workspace.</h1>
      <p className="max-w-md text-muted-foreground">
        The page you requested does not exist or has been removed from the workspace.
      </p>
      <Link href="/dashboard">
        <Button>Back to dashboard</Button>
      </Link>
    </div>
  );
}
