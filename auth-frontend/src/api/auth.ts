import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL ?? 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: UserResponse;
}

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export interface RegisterResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface UserResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
}

export interface RefreshResponse {
  accessToken: string;
  tokenType: string;
}

export interface LogoutResponse {
  message: string;
}

export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/login', data);
  return response.data;
};

export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  const response = await apiClient.post<RegisterResponse>('/auth/register', data);
  return response.data;
};

export const forgotPassword = async (
  data: ForgotPasswordRequest
): Promise<ForgotPasswordResponse> => {
  const response = await apiClient.post<ForgotPasswordResponse>(
    '/auth/forgot-password',
    data
  );
  return response.data;
};

export const resetPassword = async (
  data: ResetPasswordRequest
): Promise<ResetPasswordResponse> => {
  const response = await apiClient.post<ResetPasswordResponse>(
    '/auth/reset-password',
    data
  );
  return response.data;
};

export const me = async (): Promise<UserResponse> => {
  const response = await apiClient.get<UserResponse>('/auth/me');
  return response.data;
};

export const logout = async (): Promise<LogoutResponse> => {
  const response = await apiClient.post<LogoutResponse>('/auth/logout');
  return response.data;
};

export const refresh = async (): Promise<RefreshResponse> => {
  const response = await apiClient.post<RefreshResponse>('/auth/refresh');
  return response.data;
};

export default apiClient;
