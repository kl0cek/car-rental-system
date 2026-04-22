'use client';

import type { ReactNode } from 'react';
import type { Vehicle } from '@/types/vehicle';
import { StepDatesAndVehicle } from './StepDatesAndVehicle';
import { StepPriceSummary } from './StepPriceSummary';
import { StepContact } from './StepContact';
import { StepConfirm } from './StepConfirm';

export interface BookingFormState {
  startDate: string;
  endDate: string;
  selectedVehicle: Vehicle | null;
}

export interface BookingFormHandlers {
  setStartDate: (value: string) => void;
  setEndDate: (value: string) => void;
  setSelectedVehicle: (vehicle: Vehicle) => void;
}

export interface WizardContext {
  form: BookingFormState;
  handlers: BookingFormHandlers;
  goToStep: (step: number) => void;
}

interface WizardStep {
  key: string;
  label: string;
  render: (ctx: WizardContext) => ReactNode;
}

export const WIZARD_STEPS: readonly WizardStep[] = [
  {
    key: 'choose-vehicle',
    label: 'Choose vehicle',
    render: ({ form, handlers, goToStep }) => (
      <StepDatesAndVehicle
        startDate={form.startDate}
        endDate={form.endDate}
        selectedVehicle={form.selectedVehicle}
        onStartDate={handlers.setStartDate}
        onEndDate={handlers.setEndDate}
        onSelectVehicle={handlers.setSelectedVehicle}
        onNext={() => goToStep(1)}
      />
    ),
  },
  {
    key: 'price-summary',
    label: 'Price summary',
    render: ({ form, goToStep }) =>
      form.selectedVehicle && (
        <StepPriceSummary
          startDate={form.startDate}
          endDate={form.endDate}
          vehicle={form.selectedVehicle}
          onBack={() => goToStep(0)}
          onNext={() => goToStep(2)}
        />
      ),
  },
  {
    key: 'contact',
    label: 'Contact',
    render: ({ goToStep }) => <StepContact onBack={() => goToStep(1)} onNext={() => goToStep(3)} />,
  },
  {
    key: 'confirm',
    label: 'Confirm',
    render: ({ form, goToStep }) =>
      form.selectedVehicle && (
        <StepConfirm
          startDate={form.startDate}
          endDate={form.endDate}
          vehicle={form.selectedVehicle}
          onBack={() => goToStep(2)}
        />
      ),
  },
] as const;

export const WIZARD_STEP_LABELS = WIZARD_STEPS.map((s) => s.label);
