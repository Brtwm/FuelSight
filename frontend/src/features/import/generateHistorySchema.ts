import { z } from 'zod';

export const PRODUCT_OPTIONS = ['AI_92', 'AI_95', 'DT_S', 'DT_W'] as const;

export const generateHistorySchema = z
  .object({
    startDate: z.string().min(1, 'Укажите дату начала'),
    endDate: z.string().min(1, 'Укажите дату окончания'),
    products: z.array(z.enum(PRODUCT_OPTIONS)).min(1, 'Выберите хотя бы один продукт'),
    seed: z.number().int('Seed должен быть целым числом'),
    replaceExisting: z.boolean(),
  })
  .refine((value) => value.startDate < value.endDate, {
    message: 'Дата начала должна быть раньше даты окончания',
    path: ['endDate'],
  });

/** Default period: 3 years back from today. */
export const DEFAULT_HISTORY_YEARS = 3;

export type GenerateHistoryFormValues = z.infer<typeof generateHistorySchema>;
