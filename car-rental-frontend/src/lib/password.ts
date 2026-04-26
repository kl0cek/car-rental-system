import type { PasswordRequirement } from '@/types/register';

export function getPasswordRequirements(password: string): PasswordRequirement[] {
  return [
    { label: 'pwd.min8', met: password.length >= 8 },
    { label: 'pwd.number', met: /\d/.test(password) },
    { label: 'pwd.uppercase', met: /[A-Z]/.test(password) },
  ];
}

export function isPasswordValid(password: string): boolean {
  return getPasswordRequirements(password).every((r) => r.met);
}
