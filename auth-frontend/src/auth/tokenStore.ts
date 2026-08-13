let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setTokens(token: string): void {
  accessToken = token;
}

export function clearTokens(): void {
  accessToken = null;
}
