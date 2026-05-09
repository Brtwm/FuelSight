import { Card, CardContent } from '@mui/material';
import type { ReactNode } from 'react';
import { alpha } from '@mui/material/styles';

type FilterPanelProps = {
  children: ReactNode;
};

export function FilterPanel({ children }: FilterPanelProps) {
  return (
    <Card
      variant="outlined"
      sx={{
        backgroundColor: (theme) => alpha(theme.palette.background.paper, 0.48),
        '& .MuiCardContent-root': {
          p: { xs: 1.5, sm: 2 },
          '&:last-child': { pb: { xs: 1.5, sm: 2 } },
        },
      }}
    >
      <CardContent>{children}</CardContent>
    </Card>
  );
}
