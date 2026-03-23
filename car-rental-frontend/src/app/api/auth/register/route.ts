import { NextResponse } from 'next/server';
import { backendFetch, ApiError } from '@/lib/api-client';
import type { RegisterApiRequest } from '@/types/auth';

export async function POST(request: Request) {
  try {
    const body: RegisterApiRequest = await request.json();

    await backendFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    return NextResponse.json({
      message: 'Registration successful. Please check your email to verify your account.',
    });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ error: error.detail }, { status: error.status });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
