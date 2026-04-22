'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { SectionHeader } from './SectionHeader';
import { StepNav } from './StepNav';

interface StepContactProps {
  onBack: () => void;
  onNext: () => void;
}

export function StepContact({ onBack, onNext }: StepContactProps) {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Contact details"
        description={
          <>
            These details will be used for your reservation. Update them in{' '}
            <Link href="/dashboard/settings" className="underline">
              Settings
            </Link>{' '}
            if needed.
          </>
        }
      />

      <Card>
        <CardContent className="p-5 space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Name</span>
            <span className="font-medium">
              {user?.firstName} {user?.lastName}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Account status</span>
            <Badge variant={user?.isVerified ? 'secondary' : 'outline'}>
              {user?.isVerified ? 'Verified' : 'Unverified'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
