from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from typing import Any

from app.core.logging import setup_logging
from app.pipeline import (
    build_feature_store_daily,
    generate_demo_data,
    ingest_external_indicators_daily,
    ingest_internal_purchases_daily,
    ingest_internal_sales_daily,
    train_models_weekly,
)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _emit(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False))


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(description="FuelSight pipeline command runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ingest-sales-daily")
    subparsers.add_parser("ingest-purchases-daily")

    feature_parser = subparsers.add_parser("build-feature-store-daily")
    feature_parser.add_argument("--run-date", type=_parse_date, default=None)

    train_parser = subparsers.add_parser("train-models-weekly")
    train_parser.add_argument("--window-type", choices=["rolling", "expanding"], default="rolling")
    train_parser.add_argument("--product", action="append", default=[])
    train_parser.add_argument("--horizon", type=int, action="append", default=[])

    external_parser = subparsers.add_parser("ingest-external-indicators-daily")
    external_parser.add_argument(
        "--provider",
        choices=["auto", "live", "cached", "manual_snapshot"],
        default="auto",
    )
    external_parser.add_argument("--run-date", type=_parse_date, default=None)
    external_parser.add_argument("--lookback-days", type=int, default=365)

    demo_parser = subparsers.add_parser("generate-demo-data")
    demo_parser.add_argument("--start-date", type=_parse_date, default=None)
    demo_parser.add_argument("--end-date", type=_parse_date, default=None)
    demo_parser.add_argument("--seed", type=int, default=42)
    demo_parser.add_argument("--replace-existing", action="store_true")
    demo_parser.add_argument("--product", action="append", default=[])

    args = parser.parse_args()

    try:
        if args.command == "ingest-sales-daily":
            result = ingest_internal_sales_daily()
        elif args.command == "ingest-purchases-daily":
            result = ingest_internal_purchases_daily()
        elif args.command == "build-feature-store-daily":
            result = build_feature_store_daily(run_date=args.run_date)
        elif args.command == "train-models-weekly":
            result = train_models_weekly(
                window_type=args.window_type,
                product_codes=args.product or None,
                horizons=args.horizon or None,
            )
        elif args.command == "ingest-external-indicators-daily":
            result = ingest_external_indicators_daily(
                provider=args.provider,
                run_date=args.run_date,
                lookback_days=args.lookback_days,
            )
        elif args.command == "generate-demo-data":
            end_date = args.end_date or date.today()
            start_date = args.start_date or (end_date - timedelta(days=365))
            result = generate_demo_data(
                start_date=start_date,
                end_date=end_date,
                products=args.product or None,
                seed=args.seed,
                replace_existing=args.replace_existing,
            )
        else:
            raise ValueError(f"Unsupported command: {args.command}")

        _emit({"status": "ok", "command": args.command, "result": result})
    except Exception as exc:
        _emit(
            {
                "status": "error",
                "command": args.command,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            }
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
