import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { resetPassword } from '../../../api/auth';

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ password?: string; confirmPassword?: string }>({})

  const validatePassword = (value: string): string => {
    if (!value) return 'Password is required.';
    if (value.length < 8) return 'Password must be at least 8 characters.';
    if (!/[A-Z]/.test(value)) return 'Password must contain at least one uppercase letter.';
    if (!/[a-z]/.test(value)) return 'Password must contain at least one lowercase letter.';
    if (!/[0-9]/.test(value)) return 'Password must contain at least one number.';
    return '';
  };

  const getStrengthScore = (value: string): number => {
    let score = 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value)) score += 1;
    if (/[a-z]/.test(value)) score += 1;
    if (/[0-9]/.test(value)) score += 1;
    return score;
  };

  const strengthScore = getStrengthScore(password);
  const strengthLabel = ['', 'Weak', 'Fair', 'Good', 'Strong'][strengthScore];
  const strengthColor = ['', 'var(--color-error)', 'var(--color-warning)', 'var(--color-info)', 'var(--color-success)'][strengthScore];

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    const errors: { password?: string; confirmPassword?: string } = {};

    const passwordError = validatePassword(password);
    if (passwordError) errors.password = passwordError;

    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    if (!token) {
      setErrorMessage('Reset token is missing or invalid.');
      return;
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setFieldErrors({});
    setIsSubmitting(true);

    try {
      await resetPassword({ token, password, confirmPassword });
      setSuccessMessage('Your password has been reset. You can now log in with your new password.');
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const apiErr = err as { response?: { data?: { error?: { message?: string } } } };
        setErrorMessage(apiErr.response?.data?.error?.message ?? 'Something went wrong. Please try again.');
      } else {
        setErrorMessage('Something went wrong. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-layout">
      <style>{`
        :root {
          --color-accent-primary: #4f46e5;
          --color-accent-primary-hover: #4338ca;
          --color-accent-primary-active: #3730a3;
          --color-accent-disabled: #c7d2fe;
          --color-bg-app: #f1f5f9;
          --color-border: #E2E8F0;
          --color-border-strong: #CBD5E1;
          --color-error: #DC2626;
          --color-focus-ring: #818cf8;
          --color-info: #2563EB;
          --color-link: #4f46e5;
          --color-muted-surface: #f8fafc;
          --color-success: #16A34A;
          --color-surface: #FFFFFF;
          --color-text-muted: #94A3B8;
          --color-text-primary: #0F172A;
          --color-text-secondary: #475569;
          --color-warning: #D97706;
          --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
          --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
          --radius-card: 16px;
          --radius-button: 8px;
          --radius-input: 8px;
          --space-xs: 4px;
          --space-sm: 8px;
          --space-md: 16px;
          --space-lg: 24px;
          --space-xl: 32px;
          --space-2xl: 48px;
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        .auth-layout {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-lg);
          font-family: var(--family-base);
          color: var(--color-text-primary);
        }

        .auth-layout__branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .auth-layout__brand-name {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-accent-primary);
        }

        .auth-card {
          background: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-xl);
          width: 100%;
          max-width: 420px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin-bottom: var(--space-sm);
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-xl);
        }

        .auth-card__field {
          margin-bottom: var(--space-md);
        }

        .auth-card__label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-primary);
          margin-bottom: var(--space-xs);
        }

        .auth-card__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .auth-card__input {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          padding-right: 44px;
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          font-size: 16px;
          font-family: var(--family-base);
          color: var(--color-text-primary);
          background: var(--color-surface);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .auth-card__input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .auth-card__input--error {
          border-color: var(--color-error);
        }

        .auth-card__input--error:focus {
          box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
        }

        .auth-card__toggle-btn {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--space-xs);
          color: var(--color-text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-sm);
        }

        .auth-card__toggle-btn:focus {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .field--error {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
          margin-top: var(--space-xs);
        }

        .auth-card__strength {
          margin-top: var(--space-xs);
        }

        .auth-card__strength-bar {
          display: flex;
          gap: var(--space-xs);
          margin-bottom: var(--space-xs);
        }

        .auth-card__strength-segment {
          height: 4px;
          flex: 1;
          border-radius: var(--radius-full, 9999px);
          background: var(--color-border);
          transition: background 0.2s;
        }

        .auth-card__strength-label {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-secondary);
        }

        .auth-card__submit {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          background: var(--color-accent-primary);
          color: var(--color-surface);
          border: none;
          border-radius: var(--radius-button);
          font-size: 16px;
          font-family: var(--family-base);
          font-weight: 600;
          cursor: pointer;
          transition: background 0.15s;
          margin-top: var(--space-md);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
        }

        .auth-card__submit:hover:not(:disabled) {
          background: var(--color-accent-primary-hover);
        }

        .auth-card__submit:active:not(:disabled) {
          background: var(--color-accent-primary-active);
        }

        .auth-card__submit:disabled {
          background: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .auth-card__submit:focus {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .auth-card__banner {
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          margin-bottom: var(--space-md);
        }

        .auth-card__banner--error {
          background: #fef2f2;
          color: var(--color-error);
          border: 1px solid #fecaca;
        }

        .auth-card__banner--success {
          background: #f0fdf4;
          color: var(--color-success);
          border: 1px solid #bbf7d0;
        }

        .auth-card__footer {
          margin-top: var(--space-lg);
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
        }

        .auth-card__link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }

        .auth-card__link:hover {
          text-decoration: underline;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="auth-layout__branding">
        <span className="auth-layout__brand-name">AuthStarter</span>
      </div>

      <div className="auth-card">
        <h1 className="auth-card__title">Reset password</h1>
        <p className="auth-card__subtitle">Enter your new password below.</p>

        <div aria-live="polite">
          {errorMessage && (
            <div className="auth-card__banner auth-card__banner--error" role="alert">
              {errorMessage}
            </div>
          )}
          {successMessage && (
            <div className="auth-card__banner auth-card__banner--success" role="status">
              {successMessage}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-card__field">
            <label htmlFor="password" className="auth-card__label">
              New password
            </label>
            <div className="auth-card__input-wrapper">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className={`auth-card__input${fieldErrors.password ? ' auth-card__input--error' : ''}`}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                aria-invalid={!!fieldErrors.password}
                disabled={isSubmitting || !!successMessage}
              />
              <button
                type="button"
                className="auth-card__toggle-btn"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={0}
              >
                {showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {password && (
              <div className="auth-card__strength" aria-label={`Password strength: ${strengthLabel}`}>
                <div className="auth-card__strength-bar">
                  {[1, 2, 3, 4].map((level) => (
                    <div
                      key={level}
                      className="auth-card__strength-segment"
                      style={{
                        background: strengthScore >= level ? strengthColor : 'var(--color-border)',
                      }}
                    />
                  ))}
                </div>
                {strengthLabel && (
                  <span className="auth-card__strength-label" style={{ color: strengthColor }}>
                    {strengthLabel}
                  </span>
                )}
              </div>
            )}
            {fieldErrors.password && (
              <p id="password-error" className="field--error" role="alert">
                {fieldErrors.password}
              </p>
            )}
          </div>

          <div className="auth-card__field">
            <label htmlFor="confirmPassword" className="auth-card__label">
              Confirm new password
            </label>
            <div className="auth-card__input-wrapper">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                className={`auth-card__input${fieldErrors.confirmPassword ? ' auth-card__input--error' : ''}`}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                aria-describedby={fieldErrors.confirmPassword ? 'confirmPassword-error' : undefined}
                aria-invalid={!!fieldErrors.confirmPassword}
                disabled={isSubmitting || !!successMessage}
              />
              <button
                type="button"
                className="auth-card__toggle-btn"
                onClick={() => setShowConfirmPassword((v) => !v)}
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                tabIndex={0}
              >
                {showConfirmPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {fieldErrors.confirmPassword && (
              <p id="confirmPassword-error" className="field--error" role="alert">
                {fieldErrors.confirmPassword}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="auth-card__submit"
            disabled={isSubmitting || !!successMessage}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className="spinner" aria-hidden="true" />}
            {isSubmitting ? 'Resetting…' : 'Reset password'}
          </button>
        </form>

        <div className="auth-card__footer">
          <a href="/login" className="auth-card__link">Back to sign in</a>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
