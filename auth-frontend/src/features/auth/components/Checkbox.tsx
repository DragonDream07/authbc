import React from 'react';

interface CheckboxProps {
  id: string;
  label: React.ReactNode;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

function Checkbox({
  id,
  label,
  checked,
  onChange,
  onBlur,
  error,
  disabled = false,
  required = false,
}: CheckboxProps): JSX.Element {
  const errorId = `${id}-error`;

  return (
    <div className={`auth-card__field checkbox${error ? ' checkbox--error' : ''}`}>
      <label className="checkbox__label" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
          required={required}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? errorId : undefined}
          className="checkbox__input"
        />
        <span className="checkbox__box" aria-hidden="true" />
        <span className="checkbox__text">
          {label}
          {required && (
            <span className="field__required" aria-hidden="true">
              {' '}*
            </span>
          )}
        </span>
      </label>
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export default Checkbox;
