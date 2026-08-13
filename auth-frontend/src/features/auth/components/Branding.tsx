import React from 'react';

function Branding(): JSX.Element {
  return (
    <div className="auth-branding">
      <div className="auth-branding__logo" aria-hidden="true">
        <svg
          width="48"
          height="48"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            width="48"
            height="48"
            rx="12"
            fill="var(--color-accent-primary)"
          />
          <path
            d="M24 12C18.477 12 14 16.477 14 22C14 25.394 15.671 28.394 18.25 30.25V34C18.25 34.966 19.034 35.75 20 35.75H28C28.966 35.75 29.75 34.966 29.75 34V30.25C32.329 28.394 34 25.394 34 22C34 16.477 29.523 12 24 12Z"
            fill="var(--color-surface-primary)"
          />
          <path
            d="M20.5 34V30.75H27.5V34C27.5 34.138 27.388 34.25 27.25 34.25H20.75C20.612 34.25 20.5 34.138 20.5 34Z"
            fill="var(--color-surface-primary)"
          />
        </svg>
      </div>
      <span className="auth-branding__wordmark">AuthStarter</span>
    </div>
  );
}

export default Branding;
