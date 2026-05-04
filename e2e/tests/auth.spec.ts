import { test, expect } from '@playwright/test';
import { login, expectLoggedIn, expectLoggedOut, SEED_CUSTOMER } from './helpers';

test.describe('Authentication', () => {
  test('valid credentials log the user in and land on /dashboard', async ({ page }) => {
    await login(page, SEED_CUSTOMER);
    await expectLoggedIn(page);
  });

  test('invalid credentials keep the user on the login page', async ({ page }) => {
    await page.goto('/');
    await page.locator('#email').fill(SEED_CUSTOMER.email);
    await page.locator('#password').fill('WrongPassword1');
    await page.locator('form button[type="submit"]').click();

    // We should NOT navigate away from "/"
    await page.waitForTimeout(1500);
    expect(new URL(page.url()).pathname).toBe('/');
  });

  test('regression: page refresh keeps the user logged in (no /users/me 500)', async ({
    page,
  }) => {
    // This pins the bug we fixed: cached User missing created_at/updated_at
    // caused /users/me to 500 → AuthContext logged the user out → forced relog.
    await login(page, SEED_CUSTOMER);
    await expectLoggedIn(page);

    // Hard refresh — AuthContext re-runs and calls /users/me from the cache.
    const meCalls: number[] = [];
    page.on('response', (resp) => {
      if (resp.url().includes('/api/users/me') || resp.url().includes('/users/me')) {
        meCalls.push(resp.status());
      }
    });

    await page.reload({ waitUntil: 'networkidle' });

    // Still on dashboard, not bounced to login.
    await expectLoggedIn(page);

    // /users/me may be called once or several times depending on caching;
    // none of them must be 5xx.
    for (const status of meCalls) {
      expect(status, '/users/me must not return 5xx').toBeLessThan(500);
    }
  });
});
