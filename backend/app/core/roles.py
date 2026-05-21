from __future__ import annotations

from typing import Literal

ROLE_ADMIN = "admin"
ROLE_SALES = "sales"
ROLE_ACCOUNTING = "accounting"
ROLE_ANALYST = "analyst"
ROLE_DIRECTOR = "director"

ALL_AUTHENTICATED_ROLES = (
    ROLE_ADMIN,
    ROLE_SALES,
    ROLE_ACCOUNTING,
    ROLE_ANALYST,
    ROLE_DIRECTOR,
)

KPI_READ_ROLES = ALL_AUTHENTICATED_ROLES

SALES_ANALYTICS_ROLES = (
    ROLE_ADMIN,
    ROLE_SALES,
    ROLE_ANALYST,
)
MARGIN_ANALYTICS_ROLES = (
    ROLE_ADMIN,
    ROLE_ACCOUNTING,
    ROLE_ANALYST,
    ROLE_DIRECTOR,
)

FORECAST_READ_ROLES = (
    ROLE_ADMIN,
    ROLE_SALES,
    ROLE_ANALYST,
    ROLE_DIRECTOR,
)
BACKTEST_READ_ROLES = FORECAST_READ_ROLES
BACKTEST_RUN_ROLES = (ROLE_ADMIN,)

NEWS_READ_ROLES = (
    ROLE_ADMIN,
    ROLE_SALES,
    ROLE_ANALYST,
    ROLE_DIRECTOR,
)
NEWS_REFRESH_ROLES = (ROLE_ADMIN,)

CHAT_ROLES = (
    ROLE_ADMIN,
    ROLE_ANALYST,
)

SALES_IMPORT_ROLES = (
    ROLE_ADMIN,
    ROLE_SALES,
)
PURCHASE_IMPORT_ROLES = (
    ROLE_ADMIN,
    ROLE_ACCOUNTING,
)
DEMO_GENERATION_ROLES = (ROLE_ADMIN,)
IMPORT_JOB_READ_ROLES = (
    ROLE_ADMIN,
    ROLE_SALES,
    ROLE_ACCOUNTING,
)

EXECUTIVE_REPORT_ROLES = (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_DIRECTOR,
)


def preferred_landing_route_for_role(role: str) -> str | None:
    if role == ROLE_DIRECTOR:
        return "/executive/dashboard"
    if role in ALL_AUTHENTICATED_ROLES:
        return "/dashboard"
    return None


def analytics_roles_for_metric(
    metric: Literal["sales", "margin", "purchase_price"],
) -> tuple[str, ...]:
    if metric == "sales":
        return SALES_ANALYTICS_ROLES
    return MARGIN_ANALYTICS_ROLES
