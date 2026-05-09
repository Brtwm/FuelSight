import { Box, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

type PageHeaderProps = {
  title: string;
  description?: string;
  badgeSlot?: ReactNode;
  actionSlot?: ReactNode;
};

export function PageHeader({ title, description, badgeSlot, actionSlot }: PageHeaderProps) {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      alignItems={{ xs: 'flex-start', md: 'flex-end' }}
      justifyContent="space-between"
      sx={{ minWidth: 0 }}
    >
      <Stack spacing={1} sx={{ minWidth: 0, maxWidth: 760 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            overflowWrap: 'anywhere',
          }}
        >
          {title}
        </Typography>
        {description ? (
          <Typography color="text.secondary" sx={{ maxWidth: 680 }}>
            {description}
          </Typography>
        ) : null}
        {badgeSlot ? (
          <Box sx={{ pt: 0.25 }}>
            {badgeSlot}
          </Box>
        ) : null}
      </Stack>
      {actionSlot ? (
        <Box sx={{ flexShrink: 0, width: { xs: '100%', md: 'auto' } }}>
          {actionSlot}
        </Box>
      ) : null}
    </Stack>
  );
}
