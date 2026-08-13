import type { ApiError as ApiErrorType } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  code: string;
  details?: Record<string, string[]>;
  status: number;

  constructor(status: number, code: string, message: string, details?: Record<string, string[]>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

function notifyQueue(token: string | null): void {
  refreshQueue.forEach((resolve) => resolve(token));
  refreshQueue = [];
}

async function attemptSilentRefresh(): Promise<string | null> {
  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const token: string | null = data?.access_token ?? null;
    return token;
  } catch {
    return null;
  }
}

function getAccessToken(): string | null {
  return sessionStorage.getItem('access_token') ?? localStorage.getItem('access_token');
}

function setAccessToken(token: string): void {
  if (localStorage.getItem('access_token') !== null) {
    localStorage.setItem('access_token', token);
  } else {
    sessionStorage.setItem('access_token', token);
  }
}

function clearAccessToken(): void {
  sessionStorage.removeItem('access_token');
  localStorage.removeItem('access_token');
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  let code = 'UNKNOWN_ERROR';
  let message = response.statusText || 'An unexpected error occurred.';
  let details: Record<string, string[]> | undefined;

  try {
    const body = await response.json();
    const errorBody = body?.error as ApiErrorType['error'] | undefined;
    if (errorBody) {
      code = errorBody.code ?? code;
      message = errorBody.message ?? message;
      details = errorBody.details;
    }
  } catch {
    // ignore JSON parse failure
  }

  return new ApiError(response.status, code, message, details);
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const buildHeaders = (token: string | null): HeadersInit => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  const makeRequest = (token: string | null): Promise<Response> => {
    return fetch(url, {
      ...options,
      credentials: 'include',
      headers: buildHeaders(token),
    });
  };

  let accessToken = getAccessToken();
  let response = await makeRequest(accessToken);

  if (response.status === 401) {
    if (isRefreshing) {
      // Wait for the ongoing refresh
      const newToken = await new Promise<string | null>((resolve) => {
        refreshQueue.push(resolve);
      });

      if (!newToken) {
        clearAccessToken();
        throw new ApiError(401, 'UNAUTHORIZED', 'Session expired. Please log in again.');
      }

      response = await makeRequest(newToken);
    } else {
      isRefreshing = true;

      try {
        const newToken = await attemptSilentRefresh();

        if (newToken) {
          setAccessToken(newToken);
          notifyQueue(newToken);
          response = await makeRequest(newToken);
        } else {
          clearAccessToken();
          notifyQueue(null);
          throw new ApiError(401, 'UNAUTHORIZED', 'Session expired. Please log in again.');
        }
      } finally {
        isRefreshing = false;
      }
    }
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  // Handle no-content responses
  const contentType = response.headers.get('Content-Type') ?? '';
  if (response.status === 204 || !contentType.includes('application/json')) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export function storeAccessToken(token: string, remember: boolean): void {
  if (remember) {
    localStorage.setItem('access_token', token);
  } else {
    sessionStorage.setItem('access_token', token);
  }
}

export { clearAccessToken, getAccessToken };
