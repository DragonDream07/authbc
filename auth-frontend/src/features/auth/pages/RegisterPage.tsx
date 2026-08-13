import React, { useState, useId } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../../../api/auth';

interface RegisterFormState {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

interface RegisterFormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  acceptTerms?: string;
}

function getPasswordStrength(password: string): { score: number; checks: { length: boolean; uppercase: boolean; lowercase: boolean; number: boolean } } {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
  };
  const score = Object.values(checks).filter(Boolean).length;
  return { score, checks };
}

function validateForm(form: RegisterFormState): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!form.fullName || form.fullName.trim().length < 1) {
    errors.fullName = 'Full name is required.';
  } else if (form.fullName.trim().length > 120) {
    errors.fullName = 'Full name is required.';
  }

  if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!form.password || form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(form.password)) {
    errors.password = 'Password must be at least 8 characters.';
  }

  if (!form.confirmPassword || form.confirmPassword !== form.password) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  if (!form.acceptTerms) {
    errors.acceptTerms = 'You must accept the Terms to continue.';
  }

  return errors;
}

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const idPrefix = useId();

  const [form, setForm] = useState<RegisterFormState>({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });

  const [errors, setErrors] = useState<RegisterFormErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const fullNameId = `${idPrefix}-fullName`;
  const emailId = `${idPrefix}-email`;
  const passwordId = `${idPrefix}-password`;
  const confirmPasswordId = `${idPrefix}-confirmPassword`;
  const acceptTermsId = `${idPrefix}-acceptTerms`;

  const fullNameErrId = `${idPrefix}-fullName-err`;
  const emailErrId = `${idPrefix}-email-err`;
  const passwordErrId = `${idPrefix}-password-err`;
  const confirmPasswordErrId = `${idPrefix}-confirmPassword-err`;
  const acceptTermsErrId = `${idPrefix}-acceptTerms-err`;
  const serverErrId = `${idPrefix}-server-err`;

  const { score: strengthScore, checks: strengthChecks } = getPasswordStrength(form.password);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name as keyof RegisterFormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
    if (serverError) setServerError(null);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const validationErrors = validateForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setIsSubmitting(true);
    setServerError(null);
    try {
      await register({
        fullName: form.fullName.trim(),
        email: form.email,
        password: form.password,
        confirmPassword: form.confirmPassword,
      });
      navigate('/login', { replace: true });
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        const apiErr = err as { message?: string; code?: string };
        if (apiErr.code === 'EMAIL_TAKEN') {
          setErrors(prev => ({ ...prev, email: 'That email is already registered.' }));
        } else {
          setServerError(apiErr.message ?? 'Something went wrong. Please try again.');
        }
      } else {
        setServerError('Something went wrong. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['', 'var(--color-error)', 'var(--color-warning)', 'var(--color-info)', 'var(--color-success)'];

  return (
    <div className="auth-bg">
      <style>{`
        :root {
          --color-accent-disabled: #c7d2fe;
          --color-accent-primary: #4f46e5;
          --color-accent-primary-active: #3730a3;
          --color-accent-primary-hover: #4338ca;
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
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --radius-button: 8px;
          --radius-card: 16px;
          --radius-full: 9999px;
          --radius-input: 8px;
          --space-xs: 4px;
          --space-sm: 8px;
          --space-md: 16px;
          --space-lg: 24px;
          --space-xl: 32px;
          --space-2xl: 48px;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--color-bg-app); }
        .auth-bg {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background: var(--color-bg-app);
          font-family: var(--family-base);
          padding: var(--space-md);
        }
        .auth-brand {
          margin-bottom: var(--space-lg);
          text-align: center;
        }
        .auth-brand__logo {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          border-radius: var(--radius-full);
          background: var(--color-accent-primary);
          margin-bottom: var(--space-sm);
        }
        .auth-brand__name {
          font-size: 18px;
          font-weight: 600;
          color: var(--color-text-primary);
          line-height: 1.25;
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
          margin-bottom: var(--space-xs);
          text-align: center;
        }
        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
          text-align: center;
          margin-bottom: var(--space-xl);
        }
        .auth-card__form {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }
        .auth-card__field {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }
        .auth-card__field label {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-primary);
        }
        .auth-card__input-wrap {
          position: relative;
          display: flex;
          align-items: center;
        }
        .auth-card__input {
          width: 100%;
          padding: 10px var(--space-md);
          font-size: 16px;
          font-family: var(--family-base);
          color: var(--color-text-primary);
          background: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
          line-height: 1.5;
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
        .auth-card__input--has-toggle {
          padding-right: 44px;
        }
        .toggle-btn {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          color: var(--color-text-muted);
          display: flex;
          align-items: center;
          padding: var(--space-xs);
          border-radius: var(--radius-sm);
          font-size: 12px;
        }
        .toggle-btn:focus {
          outline: none;
          box-shadow: var(--elevation-focus);
        }
        .field__error {
          font-size: 12px;
          color: var(--color-error);
          line-height: 1.5;
          display: flex;
          align-items: center;
          gap: var(--space-xs);
        }
        .strength-bar {
          display: flex;
          gap: var(--space-xs);
          margin-top: var(--space-xs);
        }
        .strength-bar__segment {
          height: 4px;
          flex: 1;
          border-radius: var(--radius-full);
          background: var(--color-border);
          transition: background 0.2s;
        }
        .strength-label {
          font-size: 12px;
          color: var(--color-text-muted);
          margin-top: var(--space-xs);
        }
        .strength-checklist {
          display: flex;
          flex-direction: column;
          gap: 2px;
          margin-top: var(--space-xs);
        }
        .strength-checklist__item {
          font-size: 12px;
          color: var(--color-text-muted);
          display: flex;
          align-items: center;
          gap: var(--space-xs);
        }
        .strength-checklist__item--ok {
          color: var(--color-success);
        }
        .terms-row {
          display: flex;
          align-items: flex-start;
          gap: var(--space-sm);
        }
        .terms-row__checkbox {
          margin-top: 2px;
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
          flex-shrink: 0;
        }
        .terms-row__label {
          font-size: 14px;
          color: var(--color-text-secondary);
          line-height: 1.5;
        }
        .link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }
        .link:hover {
          text-decoration: underline;
        }
        .auth-card__submit {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          width: 100%;
          padding: 11px var(--space-lg);
          font-size: 16px;
          font-weight: 600;
          font-family: var(--family-base);
          color: #fff;
          background: var(--color-accent-primary);
          border: none;
          border-radius: var(--radius-button);
          cursor: pointer;
          transition: background 0.15s;
          line-height: 1.5;
          margin-top: var(--space-xs);
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
          outline: none;
          box-shadow: var(--elevation-focus);
        }
        .spinner {
          display: inline-block;
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #fff;
          border-radius: var(--radius-full);
          animation: spin 0.7s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .auth-card__footer {
          text-align: center;
          font-size: 14px;
          color: var(--color-text-secondary);
          margin-top: var(--space-lg);
        }
        .server-error-banner {
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          font-size: 14px;
          color: var(--color-error);
          line-height: 1.5;
        }
      `}</style>

      <div className="auth-brand" aria-label="auth-starter">
        <div className="auth-brand__logo" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="auth-brand__name">auth-starter</div>
      </div>

      <div className="auth-card" role="main">
        <h1 className="auth-card__title">Create account</h1>
        <p className="auth-card__subtitle">Sign up to get started</p>

        <div aria-live="polite" aria-atomic="true">
          {serverError && (
            <div className="server-error-banner" id={serverErrId} role="alert">
              {serverError}
            </div>
          )}
        </div>

        <form className="auth-card__form" onSubmit={handleSubmit} noValidate>
          {/* Full Name */}
          <div className="auth-card__field">
            <label htmlFor={fullNameId}>Full name</label>
            <div className="auth-card__input-wrap">
              <input
                id={fullNameId}
                name="fullName"
                type="text"
                autoComplete="name"
                value={form.fullName}
                onChange={handleChange}
                aria-describedby={errors.fullName ? fullNameErrId : undefined}
                aria-invalid={!!errors.fullName}
                className={`auth-card__input${errors.fullName ? ' auth-card__input--error' : ''}`}
                disabled={isSubmitting}
                maxLength={120}
              />
            </div>
            {errors.fullName && (
              <p className="field__error" id={fullNameErrId} role="alert">
                {errors.fullName}
              </p>
            )}
          </div>

          {/* Email */}
          <div className="auth-card__field">
            <label htmlFor={emailId}>Email address</label>
            <div className="auth-card__input-wrap">
              <input
                id={emailId}
                name="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={handleChange}
                aria-describedby={errors.email ? emailErrId : undefined}
                aria-invalid={!!errors.email}
                className={`auth-card__input${errors.email ? ' auth-card__input--error' : ''}`}
                disabled={isSubmitting}
              />
            </div>
            {errors.email && (
              <p className="field__error" id={emailErrId} role="alert">
                {errors.email}
              </p>
            )}
          </div>

          {/* Password */}
          <div className="auth-card__field">
            <label htmlFor={passwordId}>Password</label>
            <div className="auth-card__input-wrap">
              <input
                id={passwordId}
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={form.password}
                onChange={handleChange}
                aria-describedby={errors.password ? passwordErrId : undefined}
                aria-invalid={!!errors.password}
                className={`auth-card__input auth-card__input--has-toggle${errors.password ? ' auth-card__input--error' : ''}`}
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="toggle-btn"
                onClick={() => setShowPassword(v => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={0}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            {form.password.length > 0 && (
              <>
                <div className="strength-bar" aria-hidden="true">
                  {[0, 1, 2, 3].map(i => (
                    <div
                      key={i}
                      className="strength-bar__segment"
                      style={{
                        background: i < strengthScore ? strengthColors[strengthScore] : 'var(--color-border)',
                      }}
                    />
                  ))}
                </div>
                {strengthScore > 0 && (
                  <div className="strength-label" aria-live="polite">
                    Password strength:{' '}
                    <span style={{ color: strengthColors[strengthScore], fontWeight: 500 }}>
                      {strengthLabels[strengthScore]}
                    </span>
                  </div>
                )}
                <div className="strength-checklist" aria-label="Password requirements">
                  <div className={`strength-checklist__item${strengthChecks.length ? ' strength-checklist__item--ok' : ''}`}>
                    {strengthChecks.length ? '✓' : '○'} At least 8 characters
                  </div>
                  <div className={`strength-checklist__item${strengthChecks.uppercase ? ' strength-checklist__item--ok' : ''}`}>
                    {strengthChecks.uppercase ? '✓' : '○'} Uppercase letter
                  </div>
                  <div className={`strength-checklist__item${strengthChecks.lowercase ? ' strength-checklist__item--ok' : ''}`}>
                    {strengthChecks.lowercase ? '✓' : '○'} Lowercase letter
                  </div>
                  <div className={`strength-checklist__item${strengthChecks.number ? ' strength-checklist__item--ok' : ''}`}>
                    {strengthChecks.number ? '✓' : '○'} Number
                  </div>
                </div>
              </>
            )}
            {errors.password && (
              <p className="field__error" id={passwordErrId} role="alert">
                {errors.password}
              </p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="auth-card__field">
            <label htmlFor={confirmPasswordId}>Confirm password</label>
            <div className="auth-card__input-wrap">
              <input
                id={confirmPasswordId}
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={form.confirmPassword}
                onChange={handleChange}
                aria-describedby={errors.confirmPassword ? confirmPasswordErrId : undefined}
                aria-invalid={!!errors.confirmPassword}
                className={`auth-card__input auth-card__input--has-toggle${errors.confirmPassword ? ' auth-card__input--error' : ''}`}
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="toggle-btn"
                onClick={() => setShowConfirmPassword(v => !v)}
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                tabIndex={0}
              >
                {showConfirmPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="field__error" id={confirmPasswordErrId} role="alert">
                {errors.confirmPassword}
              </p>
            )}
          </div>

          {/* Accept Terms */}
          <div className="auth-card__field">
            <div className="terms-row">
              <input
                id={acceptTermsId}
                name="acceptTerms"
                type="checkbox"
                className="terms-row__checkbox"
                checked={form.acceptTerms}
                onChange={handleChange}
                aria-describedby={errors.acceptTerms ? acceptTermsErrId : undefined}
                aria-invalid={!!errors.acceptTerms}
                disabled={isSubmitting}
              />
              <label htmlFor={acceptTermsId} className="terms-row__label">
                I agree to the{' '}
                <a href="/terms" className="link" target="_blank" rel="noopener noreferrer">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="/privacy" className="link" target="_blank" rel="noopener noreferrer">
                  Privacy Policy
                </a>
              </label>
            </div>
            {errors.acceptTerms && (
              <p className="field__error" id={acceptTermsErrId} role="alert">
                {errors.acceptTerms}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="auth-card__submit"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className="spinner" aria-hidden="true" />}
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-card__footer">
          Already have an account?{' '}
          <Link to="/login" className="link">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
