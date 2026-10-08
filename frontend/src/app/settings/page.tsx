import { Bell, Lock, MoonStar, ShieldCheck, SlidersHorizontal } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function SettingsPage() {
  const items = [
    { label: 'Appearance', value: 'Dark mode', icon: MoonStar },
    { label: 'Notifications', value: 'Enabled', icon: Bell },
    { label: 'Privacy', value: 'Private workspace', icon: Lock },
    { label: 'Automations', value: '4 rules active', icon: SlidersHorizontal },
  ];

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">Workspace</p>
        <h1 className="mt-2 text-3xl font-semibold">Settings</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {items.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-secondary p-2">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">{label}</div>
                  <div className="font-medium">{value}</div>
                </div>
              </div>
              <Button variant="ghost" size="sm">Configure</Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Workspace preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>Meeting notes auto-sync every 15 minutes and retain indexed transcript data for instant search.</p>
          <p>Action items are shared with the team in real time once they are marked complete.</p>
        </CardContent>
      </Card>
    </div>
  );
}
