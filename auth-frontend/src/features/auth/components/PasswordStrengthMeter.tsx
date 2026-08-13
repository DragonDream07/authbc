import React from 'react';

interface Rule {
  key: string;
  label: string;
  test: (password: string) => boolean;
}

const RULES: Rule[] = [
  {
    key: 'length',
    label: 'At least 8 characters',
    test: (password) => password.length >= 8,
  },
  {
    key: 'uppercase',
    label: 'At least one uppercase letter',
    test: (password) => /[A-Z]/.test(password),
  },
  {
    key: 'lowercase',
    label: 'At least one lowercase letter',
    test: (password) => /[a-z]/.test(password),
  },
  {
    key: 'number',
    label: 'At least one number',
    test: (password) => /[0-9]/.test(password),
  },
];

interface PasswordStrengthMeterProps {
  password: string;
}

function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps): JSX.Element {
  const results = RULES.map((rule) => ({
    key: rule.key,
    label: rule.label,
    passed: rule.test(password),
  }));

  const passedCount = results.filter((r) => r.passed).length;
  const total = RULES.length;

  const strengthClass =
    passedCount === 0
      ? 'strength--empty'
      : passedCount === 1
      ? 'strength--weak'
      : passedCount === 2
      ? 'strength--fair'
      : passedCount === 3
      ? 'strength--good'
      : 'strength--strong';

  const strengthLabel =
    passedCount === 0
      ? ''
      : passedCount === 1
      ? 'Weak'
      : passedCount === 2
      ? 'Fair'
      : passedCount === 3
      ? 'Good'
      : 'Strong';

  return (
    <div className={`password-strength ${strengthClass}`} aria-label="Password strength">
      <div className="password-strength__bar" aria-hidden="true">
        {Array.from({ length: total }).map((_, index) => (
          <div
            key={index}
            className={`password-strength__segment${
              index < passedCount ? ' password-strength__segment--filled' : ''
            }`}
          />
        ))}
      </div>
      {strengthLabel && (
        <span className="password-strength__label" aria-live="polite">
          {strengthLabel}
        </span>
      )}
      <ul className="password-strength__checklist" aria-label="Password requirements">
        {results.map((result) => (
          <li
            key={result.key}
            className={`password-strength__check${
              result.passed ? ' password-strength__check--passed' : ''
            }`}
          >
            <span
              className="password-strength__check-icon"
              aria-hidden="true"
            >
              {result.passed ? '✓' : '○'}
            </span>
            <span className="password-strength__check-label">{result.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PasswordStrengthMeter;
