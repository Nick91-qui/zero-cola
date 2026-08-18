import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function GET(request: NextRequest, context: { params: Promise<{ examId: string }> }) {
  const { examId } = await context.params;

  const upstreamResponse = await fetch(`${API_URL}/exams/${examId}/statistics`, {
    method: 'GET',
    headers: {
      cookie: request.headers.get('cookie') ?? '',
      authorization: request.headers.get('authorization') ?? '',
    },
    cache: 'no-store',
  });

  const body = await upstreamResponse.text();
  const headers = new Headers();
  const contentType = upstreamResponse.headers.get('content-type');

  if (contentType) {
    headers.set('content-type', contentType);
  }
  headers.set('cache-control', 'no-store');

  return new NextResponse(body, {
    status: upstreamResponse.status,
    headers,
  });
}
