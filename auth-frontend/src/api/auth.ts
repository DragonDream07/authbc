const API_BASE = '/api';

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface AuthUser {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  tokenType: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

class AuthApiError extends Error {
  code: string;
  details?: Record<string, unknown>;

  constructor(code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'AuthApiError';
    this.code = code;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    const text = await response.text();
    if (!text) return undefined as unknown as T;
    return JSON.parse(text) as T;
  }

  let errorBody: { error?: ApiError } | null = null;
  try {
    errorBody = await response.json();
  } catch {
    throw new AuthApiError('UNKNOWN_ERROR', 'Something went wrong. Please try again.');
  }

  const apiErr = errorBody?.error;
  throw new AuthApiError(
    apiErr?.code ?? 'UNKNOWN_ERROR',
    apiErr?.message ?? 'Something went wrong. Please try again.',
    apiErr?.details,
  );
}

export async function register(data: RegisterRequest): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      full_name: data.fullName,
      email: data.email,
      password: data.password,
      confirm_password: data.confirmPassword,
    }),
  });
  return handleResponse<void>(response);
}

export async function login(data: LoginRequest): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      email: data.email,
      password: data.password,
      remember_me: data.rememberMe ?? false,
    }),
  });
  return handleResponse<AuthTokens>(response);
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email: data.email }),
  });
  return handleResponse<void>(response);
}

export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      token: data.token,
      password: data.password,
      confirm_password: data.confirmPassword,
    }),
  });
  return handleResponse<void>(response);
}

export async function me(): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  return handleResponse<AuthUser>(response);
}

export async function logout(): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  return handleResponse<void>(response);
}

export async function refresh(): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  return handleResponse<AuthTokens>(response);
}

export { AuthApiError };
