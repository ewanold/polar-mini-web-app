from typing import Literal

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from polar_app.models.base import Base

MappingState = Literal["mapped", "ignored", "unmapped"]


class TrainingGroup(Base):
    __tablename__ = "training_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    mappings: Mapped[list["PolarSportTypeMapping"]] = relationship(
        back_populates="group", order_by="PolarSportTypeMapping.sport_type"
    )


class PolarSportTypeMapping(Base):
    __tablename__ = "polar_sport_type_mappings"

    sport_type: Mapped[str] = mapped_column(String(255), primary_key=True)
    state: Mapped[MappingState] = mapped_column(String(20), nullable=False, default="unmapped")
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("training_groups.id", ondelete="SET NULL")
    )

    group: Mapped[TrainingGroup | None] = relationship(back_populates="mappings")
