import { zodResolver } from '@hookform/resolvers/zod';
import { Alert, Button, CircularProgress, Stack, TextField } from '@mui/material';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { ENABLE_DEMO_CREDENTIALS } from '../../../lib/config/env';
import type { LoginCredentials } from '../../../lib/api/auth.types';

const loginFormSchema = z.object({
  email: z.string().email('Введите корректный email'),
  password: z.string().min(8, 'Минимум 8 символов'),
});

type LoginFormValues = z.infer<typeof loginFormSchema>;

type LoginFormProps = {
  loading: boolean;
  errorMessage?: string | null;
  onSubmit: (credentials: LoginCredentials) => Promise<void>;
  demoCredentialsEnabled?: boolean;
};

export function LoginForm({
  loading,
  errorMessage,
  onSubmit,
  demoCredentialsEnabled = ENABLE_DEMO_CREDENTIALS,
}: LoginFormProps) {
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: {
      email: demoCredentialsEnabled ? 'analyst@fuelsight.local' : '',
      password: demoCredentialsEnabled ? 'analyst12345' : '',
    },
  });

  return (
    <Stack
      spacing={2}
      component="form"
      onSubmit={form.handleSubmit(async (values) => {
        await onSubmit(values);
      })}
    >
      <TextField
        label="Email"
        autoComplete="email"
        {...form.register('email')}
        error={Boolean(form.formState.errors.email)}
        helperText={form.formState.errors.email?.message}
        disabled={loading}
      />
      <TextField
        label="Пароль"
        type="password"
        autoComplete="current-password"
        {...form.register('password')}
        error={Boolean(form.formState.errors.password)}
        helperText={form.formState.errors.password?.message}
        disabled={loading}
      />
      {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
      <Button type="submit" variant="contained" size="large" disabled={loading}>
        {loading ? <CircularProgress size={20} color="inherit" /> : 'Войти'}
      </Button>
    </Stack>
  );
}
