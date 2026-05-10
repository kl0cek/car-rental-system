import { test, expect } from '@playwright/test';
import { login, SEED_CUSTOMER, SEED_ADMIN } from './helpers';

test.describe('Role-based access control', () => {
  test('customer hitting /api/admin/users gets 403', async ({ page }) => {
    await login(page, SEED_CUSTOMER);

    const resp = await page.request.get('/api/admin/users');
    expect(resp.status()).toBe(403);
  });

  test('admin can list users via /api/admin/users', async ({ page }) => {
    await login(page, SEED_ADMIN);

    const resp = await page.request.get('/api/admin/users?limit=5');
    expect(resp.status()).toBe(200);

    const body = await resp.json();
    expect(body).toHaveProperty('items');
    expect(Array.isArray(body.items)).toBe(true);
    expect(body).toHaveProperty('total');
  });
});
