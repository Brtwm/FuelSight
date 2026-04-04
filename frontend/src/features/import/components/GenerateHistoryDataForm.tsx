import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import type { GenerateHistoryPayload } from '../../../lib/api/import.types';
import {
  generateHistorySchema,
  type GenerateHistoryFormValues,
  PRODUCT_OPTIONS,
  DEFAULT_HISTORY_YEARS,
} from '../generateHistorySchema';

type Props = {
  loading: boolean;
  onSubmit: (payload: GenerateHistoryPayload) => Promise<void>;
};

function formatDateForInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function defaultFormValues(): GenerateHistoryFormValues {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(endDate.getFullYear() - DEFAULT_HISTORY_YEARS);
  return {
    startDate: formatDateForInput(startDate),
    endDate: formatDateForInput(endDate),
    products: [...PRODUCT_OPTIONS],
    seed: 42,
    replaceExisting: false,
  };
}

export function GenerateHistoryDataForm({ loading, onSubmit }: Props) {
  const form = useForm<GenerateHistoryFormValues>({
    resolver: zodResolver(generateHistorySchema),
    defaultValues: defaultFormValues(),
  });

  return (
    <Card>
      <CardContent>
        <Stack
          spacing={2}
          component="form"
          onSubmit={form.handleSubmit(async (values) => {
            await onSubmit({
              start_date: values.startDate,
              end_date: values.endDate,
              products: values.products,
              seed: values.seed,
              replace_existing: values.replaceExisting,
            });
          })}
        >
          <Typography variant="h6" fontWeight={700}>
            Генерация исторических данных
          </Typography>
          <Typography color="text.secondary">
            Система создаст согласованные продажи и закупки с сезонностью и редкими шоками.
          </Typography>

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Дата начала"
              type="date"
              InputLabelProps={{ shrink: true }}
              {...form.register('startDate')}
              error={Boolean(form.formState.errors.startDate)}
              helperText={form.formState.errors.startDate?.message}
              disabled={loading}
              fullWidth
            />
            <TextField
              label="Дата окончания"
              type="date"
              InputLabelProps={{ shrink: true }}
              {...form.register('endDate')}
              error={Boolean(form.formState.errors.endDate)}
              helperText={form.formState.errors.endDate?.message}
              disabled={loading}
              fullWidth
            />
          </Stack>

          <TextField
            label="Seed"
            type="number"
            {...form.register('seed', { valueAsNumber: true })}
            error={Boolean(form.formState.errors.seed)}
            helperText={form.formState.errors.seed?.message}
            disabled={loading}
          />

          <Controller
            control={form.control}
            name="products"
            render={({ field }) => (
              <FormGroup row>
                {PRODUCT_OPTIONS.map((code) => {
                  const checked = field.value.includes(code);
                  return (
                    <FormControlLabel
                      key={code}
                      control={
                        <Checkbox
                          checked={checked}
                          disabled={loading}
                          onChange={(event) => {
                            if (event.target.checked) {
                              field.onChange([...field.value, code]);
                            } else {
                              field.onChange(field.value.filter((item) => item !== code));
                            }
                          }}
                        />
                      }
                      label={code}
                    />
                  );
                })}
              </FormGroup>
            )}
          />
          {form.formState.errors.products ? (
            <Alert severity="error">{form.formState.errors.products.message}</Alert>
          ) : null}

          <Controller
            control={form.control}
            name="replaceExisting"
            render={({ field }) => (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(field.value)}
                    disabled={loading}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                }
                label="Заменить существующие записи в выбранном периоде"
              />
            )}
          />

          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Идёт генерация...' : 'Сгенерировать'}
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}
