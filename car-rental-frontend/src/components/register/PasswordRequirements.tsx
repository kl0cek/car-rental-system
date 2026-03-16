'use client';

import { Check } from 'lucide-react';
import type { PasswordRequirement } from '@/types/register/register';

interface PasswordRequirementsProps {
  requirements: PasswordRequirement[];
}

export function PasswordRequirements({ requirements }: PasswordRequirementsProps) {
  return (
    <ul className="space-y-1.5 pt-2" aria-label="Password requirements">
      {requirements.map((req) => (
        <li key={req.label} className="flex items-center gap-2 text-xs">
          <div
            className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
              req.met ? 'bg-accent text-accent-foreground' : 'bg-muted'
            }`}
            aria-hidden="true"
          >
            {req.met && <Check className="w-3 h-3" />}
          </div>
          <span
            className={req.met ? 'text-foreground' : 'text-muted-foreground'}
            aria-label={`${req.label}: ${req.met ? 'met' : 'not met'}`}
          >
            {req.label}
          </span>
        </li>
      ))}
    </ul>
  );
}
