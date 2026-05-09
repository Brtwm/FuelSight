import { Chip, Stack, Typography } from '@mui/material';

type ChipToggleOption<TValue extends string> = {
  label: string;
  value: TValue;
  disabled?: boolean;
};

type ChipToggleGroupProps<TValue extends string> = {
  label: string;
  value: TValue;
  options: Array<ChipToggleOption<TValue>>;
  onChange: (value: TValue) => void;
};

export function ChipToggleGroup<TValue extends string>({
  label,
  value,
  options,
  onChange,
}: ChipToggleGroupProps<TValue>) {
  return (
    <Stack spacing={0.75}>
      <Typography variant="caption" color="text.secondary" fontWeight={700}>
        {label}
      </Typography>
      <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <Chip
              key={option.value}
              label={option.label}
              color={selected ? 'primary' : 'default'}
              variant={selected ? 'filled' : 'outlined'}
              disabled={option.disabled}
              onClick={() => onChange(option.value)}
              sx={{
                minHeight: 40,
                borderRadius: 2,
                '& .MuiChip-label': {
                  px: 1.25,
                  fontSize: '0.78rem',
                },
              }}
            />
          );
        })}
      </Stack>
    </Stack>
  );
}
