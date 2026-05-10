import { test, expect } from '@playwright/test';

/**
 * Cheap API smoke tests through nginx → backend.
 * Exercise the auth flow without UI to catch routing/proxy regressions
 * (CORS, cookie domain, nginx config) independently of the React app.
 */

test.describe('API smoke (via nginx proxy)', () => {
  test('health endpoint is reachable', async ({ request }) => {
    const resp = await request.get('/api/health');
    expect(resp.status()).toBe(200);
  });

  test('login → cookie set → /users/me returns user', async ({ request }) => {
    const login = await request.post('/api/auth/login', {
      data: { email: 'jan.kowalski@example.com', password: 'Password1' },
    });
    expect(login.status()).toBe(200);

    const me = await request.get('/api/users/me');
    expect(me.status()).toBe(200);

    const body = await me.json();
    expect(body.email).toBe('jan.kowalski@example.com');
    expect(body).toHaveProperty('created_at');
    expect(body.created_at).not.toBeNull();
    expect(body).toHaveProperty('updated_at');
    expect(body.updated_at).not.toBeNull();
  });

  test('unauthenticated /users/me returns 401', async ({ request }) => {
    // Fresh request context = no cookies
    const resp = await request.get('/api/users/me', {
      headers: { Cookie: '' },
    });
    expect([401, 403]).toContain(resp.status());
  });
});
