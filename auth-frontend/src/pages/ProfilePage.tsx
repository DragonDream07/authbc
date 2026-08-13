import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../features/auth/context/AuthContext';

const styles = `
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
    --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
    --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
    --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-input: 8px;
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 48px;
  }

  .profile-layout {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-lg);
    font-family: var(--family-base);
  }

  .profile-branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .profile-branding__logo {
    font-size: 30px;
    font-weight: 700;
    color: var(--color-accent-primary);
    line-height: 1.2;
    letter-spacing: -0.5px;
  }

  .profile-card {
    background-color: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 480px;
  }

  .profile-card__title {
    font-size: 30px;
    font-weight: 700;
    color: var(--color-text-primary);
    line-height: 1.2;
    margin: 0 0 var(--space-xs) 0;
  }

  .profile-card__subtitle {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-xl) 0;
    line-height: 1.5;
  }

  .profile-card__section {
    margin-bottom: var(--space-lg);
  }

  .profile-card__label {
    display: block;
    font-size: 12px;
    font-weight: 400;
    color: var(--color-text-muted);
    line-height: 1.5;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: var(--space-xs);
  }

  .profile-card__value {
    font-size: 16px;
    font-weight: 400;
    color: var(--color-text-primary);
    line-height: 1.5;
    background-color: var(--color-muted-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    word-break: break-all;
  }

  .profile-card__divider {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: var(--space-lg) 0;
  }

  .profile-card__status {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
  }

  .profile-card__status--active {
    color: var(--color-success);
  }

  .profile-card__status--inactive {
    color: var(--color-error);
  }

  .profile-card__status-dot {
    width: 8px;
    height: 8px;
    border-radius: 9999px;
    display: inline-block;
  }

  .profile-card__status--active .profile-card__status-dot {
    background-color: var(--color-success);
  }

  .profile-card__status--inactive .profile-card__status-dot {
    background-color: var(--color-error);
  }

  .profile-card__actions {
    margin-top: var(--space-xl);
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .profile-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-button);
    font-family: var(--family-base);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    cursor: pointer;
    border: none;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
    text-decoration: none;
  }

  .profile-btn:focus-visible {
    outline: none;
    box-shadow: var(--elevation-focus);
  }

  .profile-btn--primary {
    background-color: var(--color-accent-primary);
    color: #ffffff;
  }

  .profile-btn--primary:hover {
    background-color: var(--color-accent-primary-hover);
  }

  .profile-btn--primary:active {
    background-color: var(--color-accent-primary-active);
  }

  .profile-btn--primary:disabled {
    background-color: var(--color-accent-disabled);
    cursor: not-allowed;
  }

  .profile-btn--secondary {
    background-color: transparent;
    color: var(--color-error);
    border: 1px solid var(--color-error);
  }

  .profile-btn--secondary:hover {
    background-color: rgba(220, 38, 38, 0.05);
  }

  .profile-btn--secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .profile-card__loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-2xl) 0;
    color: var(--color-text-muted);
    font-size: 16px;
    font-weight: 400;
    line-height: 1.5;
  }

  .profile-live-region {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
`;

const ProfilePage: React.FC = () => {
  const authContext = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (!authContext) return;
    if (!authContext.isLoading && !authContext.isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [authContext, navigate]);

  const handleLogout = async () => {
    if (!authContext) return;
    await authContext.logout();
    navigate('/login', { replace: true });
  };

  if (!authContext || authContext.isLoading) {
    return (
      <>
        <style>{styles}</style>
        <div className='profile-layout'>
          <div className='profile-card'>
            <div className='profile-card__loading' role='status' aria-live='polite'>
              Loading profile…
            </div>
          </div>
        </div>
      </>
    );
  }

  const { user } = authContext;

  if (!user) {
    return null;
  }

  const formattedCreatedAt = user.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : '—';

  return (
    <>
      <style>{styles}</style>
      <div className='profile-layout'>
        <div className='profile-branding' aria-label='auth-starter brand'>
          <span className='profile-branding__logo'>auth-starter</span>
        </div>

        <main className='profile-card' aria-label='Profile'>
          <h1 className='profile-card__title'>Your Profile</h1>
          <p className='profile-card__subtitle'>Manage your account information.</p>

          <section className='profile-card__section' aria-labelledby='label-fullname'>
            <span id='label-fullname' className='profile-card__label'>Full Name</span>
            <div className='profile-card__value' aria-labelledby='label-fullname'>
              {user.full_name}
            </div>
          </section>

          <section className='profile-card__section' aria-labelledby='label-email'>
            <span id='label-email' className='profile-card__label'>Email Address</span>
            <div className='profile-card__value' aria-labelledby='label-email'>
              {user.email}
            </div>
          </section>

          <hr className='profile-card__divider' />

          <section className='profile-card__section' aria-labelledby='label-status'>
            <span id='label-status' className='profile-card__label'>Account Status</span>
            <div
              className={`profile-card__status ${
                user.is_active
                  ? 'profile-card__status--active'
                  : 'profile-card__status--inactive'
              }`}
              aria-labelledby='label-status'
            >
              <span className='profile-card__status-dot' aria-hidden='true' />
              {user.is_active ? 'Active' : 'Inactive'}
            </div>
          </section>

          <section className='profile-card__section' aria-labelledby='label-member-since'>
            <span id='label-member-since' className='profile-card__label'>Member Since</span>
            <div className='profile-card__value' aria-labelledby='label-member-since'>
              {formattedCreatedAt}
            </div>
          </section>

          <div className='profile-card__actions'>
            <button
              type='button'
              className='profile-btn profile-btn--secondary'
              onClick={handleLogout}
            >
              Sign Out
            </button>
          </div>
        </main>

        <div aria-live='polite' className='profile-live-region' />
      </div>
    </>
  );
};

export default ProfilePage;
