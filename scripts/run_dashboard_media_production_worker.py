"""Opt-in runner for the hosted dashboard media pre-production queue."""

from __future__ import annotations

import argparse
import os

from core.content_factory.dashboard_media_production_worker import DashboardMediaProductionWorker
from core.events.bus import EventBus
from core.tools.http.real_client import RealHttpClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--endpoint", required=True)
    args = parser.parse_args()
    worker = DashboardMediaProductionWorker(RealHttpClient(EventBus()), args.endpoint)
    print(worker.run_once(token=os.getenv("DASHBOARD_INTAKE_TOKEN", ""), enabled=args.enabled))


if __name__ == "__main__":
    main()
