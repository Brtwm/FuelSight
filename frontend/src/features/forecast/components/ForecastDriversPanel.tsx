import { Card, CardContent, List, ListItem, ListItemText, Typography } from '@mui/material';

type Props = {
  drivers: string[];
};

export function ForecastDriversPanel({ drivers }: Props) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Драйверы прогноза
        </Typography>
        {drivers.length === 0 ? (
          <Typography color="text.secondary">Драйверы будут доступны после запуска прогноза.</Typography>
        ) : (
          <List dense disablePadding>
            {drivers.map((item, index) => (
              <ListItem key={`${item}-${index}`} disableGutters>
                <ListItemText primary={`${index + 1}. ${item}`} />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
}

