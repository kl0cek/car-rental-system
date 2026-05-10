import { Page, expect } from '@playwright/test';

export const SEED_CUSTOMER = {
  email: 'jan.kowalski@example.com',
  password: 'Password1',
};

export const SEED_ADMIN = {
  email: 'admin@driveease.com',
  password: 'Password1',
};

/**
 * Logs in via the UI on the home/login page.
 * Stable selectors: input ids `email` / `password` (set in LoginForm.tsx),
 * submit button by role+type.
 */
export async function login(page: Page, creds: { email: string; password: string }) {
  await page.goto('/');
  await page.locator('#email').fill(creds.email);
  await page.locator('#password').fill(creds.password);
  await page.locator('form button[type="submit"]').click();
  await page.waitForURL(/\/dashboard/, { timeout: 10_000 });
}

export async function expectLoggedIn(page: Page) {
  await expect(page).toHaveURL(/\/dashboard/);
}

export async function expectLoggedOut(page: Page) {
  // Login form visible only when unauthenticated.
  await expect(page.locator('#email')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();
}
