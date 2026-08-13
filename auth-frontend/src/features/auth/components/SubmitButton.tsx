import React from 'react';

interface SubmitButtonProps {
  label: string;
  isLoading?: boolean;
  disabled?: boolean;
}

function SubmitButton({
  label,
  isLoading = false,
  disabled = false,
}: SubmitButtonProps): JSX.Element {
  const isDisabled = disabled || isLoading;

  return (
    <button
      type="submit"
      className={`submit-button${isLoading ? ' submit-button--loading' : ''}`}
      disabled={isDisabled}
      aria-busy={isLoading ? 'true' : 'false'}
    >
      {isLoading && (
        <span className="submit-button__spinner" aria-hidden="true">
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="submit-button__spinner-icon"
          >
            <circle
              cx="9"
              cy="9"
              r="7"
              stroke="currentColor"
              strokeOpacity="0.3"
              strokeWidth="2"
            />
            <path
              d="M9 2C13.418 2 17 5.582 17 10"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </span>
      )}
      <span className="submit-button__label">
        {isLoading ? 'Please wait…' : label}
      </span>
    </button>
  );
}

export default SubmitButton;
