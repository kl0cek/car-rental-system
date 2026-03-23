import { NextResponse } from 'next/server';
import { backendFetch, ApiError } from '@/lib/api-client';
import { setAuthCookies } from '@/lib/auth-cookies';
import type { LoginApiRequest, TokenApiResponse, UserApiResponse } from '@/types/auth';
import { mapUserFromApi } from '@/types/auth';

export async function POST(request: Request) {
  try {
    const body: LoginApiRequest = await request.json();

    const tokens = await backendFetch<TokenApiResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    await setAuthCookies(tokens.access_token, tokens.refresh_token);

    const apiUser = await backendFetch<UserApiResponse>('/auth/me', {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });

    return NextResponse.json({ user: mapUserFromApi(apiUser) });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ error: error.detail }, { status: error.status });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
