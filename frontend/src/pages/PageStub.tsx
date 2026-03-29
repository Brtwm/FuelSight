import { Alert, Stack, Typography } from '@mui/material';

type Props = {
  title: string;
  description: string;
};

export function PageStub({ title, description }: Props) {
  return (
    <Stack spacing={2}>
      <Typography variant="h4" fontWeight={700}>
        {title}
      </Typography>
      <Alert severity="info">{description}</Alert>
    </Stack>
  );
}

