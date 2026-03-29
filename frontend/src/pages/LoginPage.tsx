import { zodResolver } from '@hookform/resolvers/zod';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { Navigate } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from '../features/auth/AuthProvider';

const schema = z.object({
  email: z.string().email('Введите корректный email'),
  password: z.string().min(8, 'Минимум 8 символов'),
  role: z.enum(['admin', 'analyst']),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: 'admin@fuelsight.local',
      password: 'password123',
      role: 'admin',
    },
  });

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Stack spacing={3}>
        <Box sx={{ textAlign: 'center' }}>
          <Avatar sx={{ mx: 'auto', mb: 1, bgcolor: 'primary.main' }}>
            <LockOutlinedIcon />
          </Avatar>
          <Typography variant="h4" fontWeight={700}>
            FuelSight
          </Typography>
          <Typography color="text.secondary">Локальный MVP: вход в защищенный app shell</Typography>
        </Box>

        <Card>
          <CardContent>
            <Stack
              spacing={2}
              component="form"
              onSubmit={form.handleSubmit((values) => {
                login({
                  email: values.email,
                  role: values.role,
                });
              })}
            >
              <TextField
                label="Email"
                {...form.register('email')}
                error={Boolean(form.formState.errors.email)}
                helperText={form.formState.errors.email?.message}
              />
              <TextField
                label="Пароль"
                type="password"
                {...form.register('password')}
                error={Boolean(form.formState.errors.password)}
                helperText={form.formState.errors.password?.message}
              />
              <TextField select label="Роль (демо)" {...form.register('role')}>
                <MenuItem value="admin">admin</MenuItem>
                <MenuItem value="analyst">analyst</MenuItem>
              </TextField>
              <Button type="submit" variant="contained" size="large">
                Войти
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
}

