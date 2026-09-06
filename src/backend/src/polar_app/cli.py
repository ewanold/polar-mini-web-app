import argparse

from polar_app.aggregation.rebuild import rebuild_all_training_aggregates
from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine


def main() -> None:
    parser = argparse.ArgumentParser(prog="polar-app")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("rebuild-training-aggregates")
    args = parser.parse_args()

    if args.command == "rebuild-training-aggregates":
        settings = Settings()
        engine = create_sqlite_engine(settings)
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            rebuilt = rebuild_all_training_aggregates(session, timezone=settings.timezone)
            session.commit()
        engine.dispose()
        print(f"Rebuilt {rebuilt} training aggregate buckets.")
