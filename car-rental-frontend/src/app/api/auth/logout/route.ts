import { NextResponse } from 'next/server';
import { backendFetch, ApiError } from '@/lib/api-client';
import { getAuthTokens, clearAuthCookies } from '@/lib/auth-cookies';

export async function POST() {
  try {
    const { accessToken, refreshToken } = await getAuthTokens();

    if (accessToken && refreshToken) {
      await backendFetch('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({
          access_token: accessToken,
          refresh_token: refreshToken,
        }),
      }).catch(() => {
        // Ignore backend errors on logout - clear cookies anyway
      });
    }

    await clearAuthCookies();
    return NextResponse.json({ message: 'Logged out' });
  } catch {
    await clearAuthCookies();
    return NextResponse.json({ message: 'Logged out' });
  }
}
