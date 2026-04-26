'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/dashboard/PageHeader';
import { ReturnForm } from '@/components/rentals/ReturnForm';
import { ReturnSuccess } from '@/components/rentals/ReturnSuccess';
import type { RentalResponse } from '@/types/rental';
import { useTranslation } from '@/i18n/useTranslation';

const BACK_HREF = '/dashboard/bookings';

export default function ReturnPage() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<RentalResponse | null>(null);
  const { t } = useTranslation();

  if (result) {
    return (
      <div className="max-w-lg mx-auto space-y-6">
        <PageHeader backHref={BACK_HREF} title={t('return.processed')} />
        <ReturnSuccess result={result} />
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <PageHeader
        backHref={BACK_HREF}
        title={t('return.title')}
        subtitle={
          <>
            {t('return.rental')} <span className="font-mono text-xs">{id.slice(0, 8)}…</span>
          </>
        }
      />
      <ReturnForm rentalId={id} cancelHref={BACK_HREF} onSuccess={setResult} />
    </div>
  );
}
