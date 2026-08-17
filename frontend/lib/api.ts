const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const AUTH_REFRESH_PATH = '/auth/refresh';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function shouldRetryAfterAuthError(path: string): boolean {
  return !path.startsWith('/auth/login') && !path.startsWith('/auth/logout') && path !== AUTH_REFRESH_PATH;
}

async function refreshAccessToken(): Promise<boolean> {
  const response = await fetch(`${API_URL}${AUTH_REFRESH_PATH}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
    credentials: 'include',
  });

  return response.ok;
}

async function requestWithAuthRefresh(
  path: string,
  options: RequestInit,
): Promise<Response> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: 'include',
  });

  if (response.status !== 401 || !shouldRetryAfterAuthError(path)) {
    return response;
  }

  const refreshed = await refreshAccessToken();
  if (!refreshed) {
    return response;
  }

  return fetch(`${API_URL}${path}`, {
    ...options,
    credentials: 'include',
  });
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((item: { msg?: string }) => item.msg || JSON.stringify(item)).join('; ');
    }
    return JSON.stringify(data);
  } catch {
    return response.statusText || 'Request failed';
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await requestWithAuthRefresh(path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json() as Promise<T>;
  }

  return response as unknown as T;
}

export async function apiFetchBlob(path: string): Promise<Blob> {
  const headers = new Headers();

  const response = await requestWithAuthRefresh(path, {
    headers,
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  return response.blob();
}

export { API_URL };
