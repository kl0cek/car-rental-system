import { NextResponse } from 'next/server';
import { backendFetch, ApiError } from '@/lib/api-client';
import { getAuthTokens, setAuthCookies, clearAuthCookies } from '@/lib/auth-cookies';
import type { TokenApiResponse, UserApiResponse } from '@/types/auth';
import { mapUserFromApi } from '@/types/auth';

export async function GET() {
  const { accessToken, refreshToken } = await getAuthTokens();

  if (!accessToken) {
    return NextResponse.json({ user: null }, { status: 401 });
  }

  try {
    const apiUser = await backendFetch<UserApiResponse>('/auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return NextResponse.json({ user: mapUserFromApi(apiUser) });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401 && refreshToken) {
      // Try refreshing the token
      try {
        const tokens = await backendFetch<TokenApiResponse>('/auth/refresh', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        await setAuthCookies(tokens.access_token, tokens.refresh_token);

        const apiUser = await backendFetch<UserApiResponse>('/auth/me', {
          headers: { Authorization: `Bearer ${tokens.access_token}` },
        });
        return NextResponse.json({ user: mapUserFromApi(apiUser) });
      } catch {
        await clearAuthCookies();
        return NextResponse.json({ user: null }, { status: 401 });
      }
    }

    await clearAuthCookies();
    return NextResponse.json({ user: null }, { status: 401 });
  }
}
