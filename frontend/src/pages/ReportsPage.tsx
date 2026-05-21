import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import PaidOutlinedIcon from '@mui/icons-material/PaidOutlined';
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined';
import TrendingUpOutlinedIcon from '@mui/icons-material/TrendingUpOutlined';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import type { ReactNode } from 'react';
import { useState } from 'react';
import {
  DataStatePanel,
  MetricCard,
  PageHeader,
  type DataState,
} from '../components/common';
import { useAuth } from '../features/auth/AuthProvider';
import { generateExecutiveReport } from '../lib/api/reports';
import type { ExecutiveReportData } from '../lib/api/reports.types';

const numberFormatter = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 });
const percentFormatter = new Intl.NumberFormat('ru-RU', {
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});

function formatRub(value: number): string {
  return `${numberFormatter.format(value)} ₽`;
}

function formatLiters(value: number): string {
  return `${numberFormatter.format(value)} л`;
}

function formatPercent(value: number): string {
  return `${percentFormatter.format(value)}%`;
}

function riskLabel(value: ExecutiveReportData['demand_forecast'][number]['risk_level']): string {
  if (value === 'high') {
    return 'Высокий';
  }
  if (value === 'medium') {
    return 'Средний';
  }
  return 'Низкий';
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardContent>
        <Stack spacing={1.5}>
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

function EmptyListText({ children }: { children: ReactNode }) {
  return <Typography color="text.secondary">{children}</Typography>;
}

function ReportContent({ report }: { report: ExecutiveReportData }) {
  const hasWarnings = report.data_quality.warnings.length > 0;

  return (
    <Stack spacing={3}>
      {hasWarnings ? (
        <Alert severity="warning">
          <Stack spacing={0.5}>
            <Typography fontWeight={700}>Ограничения данных</Typography>
            {report.data_quality.warnings.map((warning) => (
              <Typography key={warning} variant="body2">
                {warning}
              </Typography>
            ))}
          </Stack>
        </Alert>
      ) : null}

      <SectionCard title="Краткие выводы">
        <Typography color="text.secondary">
          Период: {report.period.date_from} - {report.period.date_to}
        </Typography>
        <Typography>{report.executive_summary}</Typography>
      </SectionCard>

      <Stack spacing={1}>
        <Typography variant="h6" fontWeight={700}>
          Сводка KPI
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
            <MetricCard
              label="Выручка"
              value={formatRub(report.kpi.revenue_rub)}
              icon={<PaidOutlinedIcon fontSize="small" />}
              tone="revenue"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
            <MetricCard
              label="Объем продаж"
              value={formatLiters(report.kpi.sales_volume_liters)}
              icon={<AssessmentOutlinedIcon fontSize="small" />}
              tone="volume"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
            <MetricCard
              label="Валовая маржа"
              value={formatRub(report.kpi.gross_margin_rub)}
              helper={formatPercent(report.kpi.gross_margin_pct)}
              icon={<InsightsOutlinedIcon fontSize="small" />}
              tone="margin"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
            <MetricCard
              label="Риски по марже"
              value={numberFormatter.format(report.margin_risks.length)}
              helper="активных сигналов"
              icon={<ReportProblemOutlinedIcon fontSize="small" />}
              tone={report.margin_risks.length > 0 ? 'risk' : 'margin'}
            />
          </Grid>
        </Grid>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Проблемные продукты">
            {report.problem_products.length > 0 ? (
              <List disablePadding>
                {report.problem_products.map((item) => (
                  <ListItem key={item.product_code} disableGutters divider>
                    <ListItemText
                      primary={`${item.product_name} (${item.product_code})`}
                      secondary={`${item.reason} Рекомендация: ${item.recommendation}`}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <EmptyListText>Проблемные продукты не выявлены.</EmptyListText>
            )}
          </SectionCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Прогноз спроса">
            {report.demand_forecast.length > 0 ? (
              <Stack spacing={1}>
                {report.demand_forecast.map((item) => (
                  <Box key={`${item.product_code}-${item.forecast_period}`}>
                    <Stack direction="row" justifyContent="space-between" spacing={1}>
                      <Typography fontWeight={700}>
                        {item.product_name} ({item.product_code})
                      </Typography>
                      <Chip size="small" label={riskLabel(item.risk_level)} />
                    </Stack>
                    <Typography color="text.secondary">
                      {item.forecast_period}: {formatLiters(item.forecast_volume_liters)}
                    </Typography>
                    <Divider sx={{ mt: 1 }} />
                  </Box>
                ))}
              </Stack>
            ) : (
              <EmptyListText>Сохраненный прогноз спроса пока недоступен.</EmptyListText>
            )}
          </SectionCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Риски по марже">
            {report.margin_risks.length > 0 ? (
              <List disablePadding>
                {report.margin_risks.map((item) => (
                  <ListItem key={item.product_code} disableGutters divider>
                    <ListItemText
                      primary={`${item.product_code}: ${item.risk}`}
                      secondary={`${item.impact} ${item.recommendation}`}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <EmptyListText>Критичных рисков по марже не выявлено.</EmptyListText>
            )}
          </SectionCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Рыночные факторы">
            {report.market_context.length > 0 ? (
              <List disablePadding>
                {report.market_context.map((item) => (
                  <ListItem key={`${item.title}-${item.published_at ?? item.source ?? ''}`} disableGutters divider>
                    <ListItemText primary={item.title} secondary={item.summary} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <EmptyListText>Рыночный контекст и новости пока недоступны.</EmptyListText>
            )}
          </SectionCard>
        </Grid>
      </Grid>

      <SectionCard title="Рекомендации">
        <List disablePadding>
          {report.recommendations.map((item) => (
            <ListItem key={item} disableGutters>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      </SectionCard>
    </Stack>
  );
}

export function ReportsPage() {
  const { authFetch } = useAuth();
  const [report, setReport] = useState<ExecutiveReportData | null>(null);
  const [state, setState] = useState<DataState>('empty');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleGenerate = async () => {
    setState('loading');
    setErrorMessage(null);
    try {
      const result = await generateExecutiveReport(authFetch);
      setReport(result);
      setState('ready');
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : 'Не удалось сформировать управленческий отчет.';
      setErrorMessage(message);
      setState('error');
    }
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Управленческий отчет"
        description="Сводка KPI, маржи, прогноза спроса и рыночных факторов для руководителя."
        actionSlot={(
          <Button
            variant="contained"
            startIcon={<TrendingUpOutlinedIcon fontSize="small" />}
            onClick={() => void handleGenerate()}
            disabled={state === 'loading'}
            sx={{ width: { xs: '100%', md: 'auto' }, textTransform: 'none' }}
          >
            Сформировать управленческий отчет
          </Button>
        )}
      />

      <DataStatePanel
        state={state}
        loadingLabel="Формируем управленческий отчет..."
        emptyTitle="Отчет пока не сформирован"
        emptyDescription="Нажмите кнопку формирования, чтобы собрать KPI, маржу, прогноз и рыночные факторы за текущий период."
        errorMessage={errorMessage ?? 'Не удалось сформировать управленческий отчет.'}
        onRetry={() => void handleGenerate()}
      >
        {report ? <ReportContent report={report} /> : null}
      </DataStatePanel>
    </Stack>
  );
}
