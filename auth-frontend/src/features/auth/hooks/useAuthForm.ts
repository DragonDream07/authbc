import { useState, useCallback, ChangeEvent, FocusEvent, FormEvent } from 'react';

export type FieldErrors<T> = Partial<Record<keyof T, string>>;
export type TouchedFields<T> = Partial<Record<keyof T, boolean>>;

export type Validator<T> = (values: T) => FieldErrors<T>;

export interface UseAuthFormOptions<T extends Record<string, string | boolean>> {
  initialValues: T;
  validate: Validator<T>;
  onSubmit: (values: T) => Promise<void>;
}

export interface UseAuthFormReturn<T extends Record<string, string | boolean>> {
  values: T;
  errors: FieldErrors<T>;
  touched: TouchedFields<T>;
  isSubmitting: boolean;
  submitError: string | null;
  submitSuccess: boolean;
  handleChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleBlur: (e: FocusEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  setFieldValue: (field: keyof T, value: string | boolean) => void;
  setSubmitError: (message: string | null) => void;
  reset: () => void;
}

export function useAuthForm<T extends Record<string, string | boolean>>(
  options: UseAuthFormOptions<T>,
): UseAuthFormReturn<T> {
  const { initialValues, validate, onSubmit } = options;

  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FieldErrors<T>>({});
  const [touched, setTouched] = useState<TouchedFields<T>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { name, value, type, checked } = e.target;
      const fieldValue: string | boolean = type === 'checkbox' ? checked : value;

      setValues((prev) => ({ ...prev, [name]: fieldValue }));
      setSubmitError(null);
      setSubmitSuccess(false);

      setTouched((prev) => {
        if (!prev[name as keyof T]) return prev;
        const updated = { ...prev, [name]: true } as TouchedFields<T>;
        const nextValues = { ...values, [name]: fieldValue } as T;
        const nextErrors = validate(nextValues);
        setErrors(nextErrors);
        return updated;
      });
    },
    [values, validate],
  );

  const handleBlur = useCallback(
    (e: FocusEvent<HTMLInputElement>) => {
      const { name } = e.target;
      setTouched((prev) => ({ ...prev, [name]: true } as TouchedFields<T>));
      const nextErrors = validate(values);
      setErrors(nextErrors);
    },
    [values, validate],
  );

  const setFieldValue = useCallback(
    (field: keyof T, value: string | boolean) => {
      setValues((prev) => ({ ...prev, [field]: value }));
      setSubmitError(null);
      setSubmitSuccess(false);

      setTouched((prev) => {
        if (!prev[field]) return prev;
        const nextValues = { ...values, [field]: value } as T;
        const nextErrors = validate(nextValues);
        setErrors(nextErrors);
        return { ...prev, [field]: true } as TouchedFields<T>;
      });
    },
    [values, validate],
  );

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      const allTouched = Object.keys(values).reduce(
        (acc, key) => ({ ...acc, [key]: true }),
        {} as TouchedFields<T>,
      );
      setTouched(allTouched);

      const validationErrors = validate(values);
      setErrors(validationErrors);

      if (Object.keys(validationErrors).length > 0) {
        return;
      }

      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      try {
        await onSubmit(values);
        setSubmitSuccess(true);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setSubmitError(err.message);
        } else {
          setSubmitError('An unexpected error occurred. Please try again.');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validate, onSubmit],
  );

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
    setSubmitError(null);
    setSubmitSuccess(false);
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    submitSuccess,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    setSubmitError,
    reset,
  };
}
