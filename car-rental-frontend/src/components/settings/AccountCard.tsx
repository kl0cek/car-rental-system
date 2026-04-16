import { User, ShieldCheck } from 'lucide-react';
import { formatDateLong, getInitials } from '@/lib/formatters';
import { Separator } from '@/components/ui/separator';
import { SettingsCard } from './SettingsCard';
import type { User as UserType } from '@/types/auth';

const ROLE_LABELS: Record<string, string> = {
  customer: 'Customer',
  employee: 'Employee',
  technician: 'Technician',
  admin: 'Administrator',
};

function StatField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-muted-foreground text-xs uppercase tracking-wider mb-1">{label}</p>
      {children}
    </div>
  );
}

interface AccountCardProps {
  user: UserType | null;
}

export function AccountCard({ user }: AccountCardProps) {
  return (
    <SettingsCard icon={User} title="Account" description="Your account details">
      {!user ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center shrink-0">
              <span className="text-base font-semibold text-secondary-foreground">
                {getInitials(user.firstName, user.lastName)}
              </span>
            </div>
            <div>
              <p className="font-medium text-foreground">
                {user.firstName} {user.lastName}
              </p>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
          </div>
          <Separator />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <StatField label="Role">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="font-medium text-foreground">
                  {ROLE_LABELS[user.role] ?? user.role}
                </span>
              </div>
            </StatField>
            <StatField label="Member since">
              <span className="font-medium text-foreground">{formatDateLong(user.createdAt)}</span>
            </StatField>
            <StatField label="Email verified">
              <span
                className={`font-medium ${user.isVerified ? 'text-green-600' : 'text-destructive'}`}
              >
                {user.isVerified ? 'Verified' : 'Not verified'}
              </span>
            </StatField>
          </div>
        </div>
      )}
    </SettingsCard>
  );
}
