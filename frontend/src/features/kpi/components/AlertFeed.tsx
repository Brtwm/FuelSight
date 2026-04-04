import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import {
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import type { KpiAlert } from '../../../lib/api/kpi.types';

type Props = {
  alerts: KpiAlert[];
  onOpenAlert: (alert: KpiAlert) => void;
};

function severityChipColor(severity: KpiAlert['severity']): 'error' | 'warning' | 'default' {
  if (severity === 'high') {
    return 'error';
  }
  if (severity === 'medium') {
    return 'warning';
  }
  return 'default';
}

function severityIconColor(severity: KpiAlert['severity']): 'error' | 'warning' | 'action' {
  if (severity === 'high') {
    return 'error';
  }
  if (severity === 'medium') {
    return 'warning';
  }
  return 'action';
}

export function AlertFeed({ alerts, onOpenAlert }: Props) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="h6" fontWeight={700}>
            Активные алерты
          </Typography>
          {alerts.length === 0 ? (
            <Typography color="text.secondary">
              За выбранный период аномалий не найдено.
            </Typography>
          ) : (
            <List disablePadding>
              {alerts.map((alert, index) => (
                <div key={`${alert.type}-${alert.product_code}-${alert.date}-${index}`}>
                  <ListItem disablePadding sx={{ py: 0.5 }}>
                    <CardActionArea onClick={() => onOpenAlert(alert)} sx={{ px: 1 }}>
                      <Stack direction="row" spacing={1} alignItems="center" width="100%">
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <WarningAmberOutlinedIcon
                            color={severityIconColor(alert.severity)}
                            fontSize="small"
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={`${alert.product_code} · ${alert.message}`}
                          secondary={new Date(alert.date).toLocaleDateString('ru-RU')}
                        />
                        <Chip label={alert.severity} color={severityChipColor(alert.severity)} size="small" />
                      </Stack>
                    </CardActionArea>
                  </ListItem>
                  {index < alerts.length - 1 ? <Divider component="li" /> : null}
                </div>
              ))}
            </List>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
