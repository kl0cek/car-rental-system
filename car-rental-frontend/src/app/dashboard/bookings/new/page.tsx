'use client';

import { Suspense, useState } from 'react';
import { PageHeader } from '@/components/dashboard/PageHeader';
import { StepIndicator } from '@/components/bookings/new/StepIndicator';
import {
  WIZARD_STEPS,
  WIZARD_STEP_LABELS,
  type BookingFormState,
} from '@/components/bookings/new/wizardSteps';
import { Skeleton } from '@/components/ui/skeleton';
import { useWizardStep } from '@/hooks/useWizardStep';
import type { Vehicle } from '@/types/vehicle';

const BACK_HREF = '/dashboard/bookings';

export default function NewBookingPage() {
  return (
    <Suspense fallback={<WizardFallback />}>
      <NewBookingWizard />
    </Suspense>
  );
}

function WizardFallback() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

function useBookingForm() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);

  const form: BookingFormState = { startDate, endDate, selectedVehicle };
  const handlers = { setStartDate, setEndDate, setSelectedVehicle };

  return { form, handlers };
}

function NewBookingWizard() {
  const { form, handlers } = useBookingForm();
  const { step, goToStep } = useWizardStep({
    stepCount: WIZARD_STEPS.length,
    canEnterStep: (next) => next === 0 || form.selectedVehicle !== null,
  });

  const current = WIZARD_STEPS[step];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        backHref={BACK_HREF}
        title="New Booking"
        subtitle="Reserve a vehicle in a few steps"
      />
      <StepIndicator steps={WIZARD_STEP_LABELS} current={step} />
      {current.render({ form, handlers, goToStep })}
    </div>
  );
}
