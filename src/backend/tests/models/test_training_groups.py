from sqlalchemy.exc import IntegrityError

from polar_app.config import Settings
from polar_app.db import create_session_factory, create_sqlite_engine
from polar_app.models.base import Base
from polar_app.models.training_groups import PolarSportTypeMapping, TrainingGroup


def test_multiple_polar_sport_types_can_map_to_one_training_group(tmp_path) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        running = TrainingGroup(name="Running", slug="running", color="#006f7b", position=1)
        session.add(running)
        session.flush()
        session.add_all(
            [
                PolarSportTypeMapping(sport_type="RUNNING", state="mapped", group_id=running.id),
                PolarSportTypeMapping(
                    sport_type="RUNNING_TRAIL", state="mapped", group_id=running.id
                ),
                PolarSportTypeMapping(sport_type="WALKING", state="ignored"),
            ]
        )
        session.commit()

    with session_factory() as session:
        running = session.query(TrainingGroup).filter_by(slug="running").one()
        assert [mapping.sport_type for mapping in running.mappings] == ["RUNNING", "RUNNING_TRAIL"]
        walking = session.query(PolarSportTypeMapping).filter_by(sport_type="WALKING").one()
        assert walking.state == "ignored"

    engine.dispose()


def test_training_group_slug_is_unique(tmp_path) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        session.add_all(
            [
                TrainingGroup(name="Running", slug="running", color="#006f7b", position=1),
                TrainingGroup(name="Other running", slug="running", color="#006f7b", position=2),
            ]
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate training-group slug was accepted")

    engine.dispose()
