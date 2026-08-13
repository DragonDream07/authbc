// Client-side mirror of validation-rules.md
// Messages are VERBATIM from validation-rules.md; order matches exactly.
// Password policy mirrors capabilities.yaml:
//   min_length=8, require_uppercase=true, require_lowercase=true,
//   require_number=true, require_special_character=false

export interface ValidationResult {
  valid: boolean;
  message: string | null;
}

export interface PasswordStrength {
  score: number; // 0-4 (number of passing rules)
  rules: PasswordRuleResult[];
}

export interface PasswordRuleResult {
  label: string;
  passing: boolean;
}

// ---------------------------------------------------------------------------
// Password policy constants (from capabilities.yaml)
// ---------------------------------------------------------------------------
const PASSWORD_MIN_LENGTH = 8;

// ---------------------------------------------------------------------------
// Individual field validators
// ---------------------------------------------------------------------------

/** RULE: full_name — required */
export function validateFullName(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Full name is required.' };
  }
  return { valid: true, message: null };
}

/** RULE: email — required, must be valid format */
export function validateEmail(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Email is required.' };
  }
  // Simple RFC-5322-ish pattern sufficient for client feedback
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value.trim())) {
    return { valid: false, message: 'Enter a valid email address.' };
  }
  return { valid: true, message: null };
}

/** RULE: password — required, then each policy rule in order */
export function validatePassword(value: string): ValidationResult {
  if (!value || value.length === 0) {
    return { valid: false, message: 'Password is required.' };
  }
  if (value.length < PASSWORD_MIN_LENGTH) {
    return {
      valid: false,
      message: `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`,
    };
  }
  if (!/[A-Z]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter.',
    };
  }
  if (!/[a-z]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter.',
    };
  }
  if (!/[0-9]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one number.',
    };
  }
  // require_special_character=false — no special-character rule
  return { valid: true, message: null };
}

/** RULE: confirm_password — must match password */
export function validateConfirmPassword(
  value: string,
  password: string,
): ValidationResult {
  if (!value || value.length === 0) {
    return { valid: false, message: 'Please confirm your password.' };
  }
  if (value !== password) {
    return { valid: false, message: 'Passwords do not match.' };
  }
  return { valid: true, message: null };
}

/** RULE: terms — must be accepted on registration */
export function validateTerms(accepted: boolean): ValidationResult {
  if (!accepted) {
    return {
      valid: false,
      message: 'You must accept the Terms of Service to register.',
    };
  }
  return { valid: true, message: null };
}

/** RULE: token — required (reset-password flow) */
export function validateResetToken(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Reset token is required.' };
  }
  return { valid: true, message: null };
}

// ---------------------------------------------------------------------------
// Login form validator (email + password required, no policy on login password)
// ---------------------------------------------------------------------------

export interface LoginFields {
  email: string;
  password: string;
}

export interface LoginErrors {
  email: string | null;
  password: string | null;
}

export function validateLoginForm(fields: LoginFields): LoginErrors {
  const emailResult = validateEmail(fields.email);
  // On login, password only needs to be non-empty (policy checked server-side)
  const passwordPresent: ValidationResult =
    !fields.password || fields.password.length === 0
      ? { valid: false, message: 'Password is required.' }
      : { valid: true, message: null };

  return {
    email: emailResult.message,
    password: passwordPresent.message,
  };
}

// ---------------------------------------------------------------------------
// Register form validator
// ---------------------------------------------------------------------------

export interface RegisterFields {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  terms: boolean;
}

export interface RegisterErrors {
  fullName: string | null;
  email: string | null;
  password: string | null;
  confirmPassword: string | null;
  terms: string | null;
}

export function validateRegisterForm(fields: RegisterFields): RegisterErrors {
  return {
    fullName: validateFullName(fields.fullName).message,
    email: validateEmail(fields.email).message,
    password: validatePassword(fields.password).message,
    confirmPassword: validateConfirmPassword(
      fields.confirmPassword,
      fields.password,
    ).message,
    terms: validateTerms(fields.terms).message,
  };
}

// ---------------------------------------------------------------------------
// Forgot-password form validator
// ---------------------------------------------------------------------------

export interface ForgotPasswordFields {
  email: string;
}

export interface ForgotPasswordErrors {
  email: string | null;
}

export function validateForgotPasswordForm(
  fields: ForgotPasswordFields,
): ForgotPasswordErrors {
  return {
    email: validateEmail(fields.email).message,
  };
}

// ---------------------------------------------------------------------------
// Reset-password form validator
// ---------------------------------------------------------------------------

export interface ResetPasswordFields {
  password: string;
  confirmPassword: string;
}

export interface ResetPasswordErrors {
  password: string | null;
  confirmPassword: string | null;
}

export function validateResetPasswordForm(
  fields: ResetPasswordFields,
): ResetPasswordErrors {
  return {
    password: validatePassword(fields.password).message,
    confirmPassword: validateConfirmPassword(
      fields.confirmPassword,
      fields.password,
    ).message,
  };
}

// ---------------------------------------------------------------------------
// Password strength meter
// Checks exactly the four active policy rules (no special-character rule).
// ---------------------------------------------------------------------------

export function getPasswordStrength(password: string): PasswordStrength {
  const rules: PasswordRuleResult[] = [
    {
      label: `At least ${PASSWORD_MIN_LENGTH} characters`,
      passing: password.length >= PASSWORD_MIN_LENGTH,
    },
    {
      label: 'One uppercase letter',
      passing: /[A-Z]/.test(password),
    },
    {
      label: 'One lowercase letter',
      passing: /[a-z]/.test(password),
    },
    {
      label: 'One number',
      passing: /[0-9]/.test(password),
    },
  ];

  const score = rules.filter((r) => r.passing).length;

  return { score, rules };
}
