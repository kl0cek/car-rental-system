"""Test Alembic migrations on a real PostgreSQL database.

The migration chain starts with an empty baseline (tables pre-exist outside
Alembic).  We simulate this by creating tables via metadata, stamping Alembic
at the appropriate revision, then running the target migration.
"""

from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from testcontainers.postgres import PostgresContainer

from app.db.base import Base

POSTGRES_IMAGE = "postgres:17-alpine"

pytestmark = pytest.mark.integration


def _alembic_cfg(async_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", async_url)
    return cfg


def _create_pre_migration_schema(sync_url: str) -> None:
    """Create the schema as it looked BEFORE the categories migration.

    This simulates the state after the empty baseline + is_verified migration.
    We create users/vehicles/rentals tables (without categories) using raw DDL.
    """
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'customer',
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false NOT NULL,
                phone VARCHAR(20),
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE vehicles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                brand VARCHAR(100) NOT NULL,
                model VARCHAR(100) NOT NULL,
                year INTEGER NOT NULL,
                license_plate VARCHAR(20) UNIQUE NOT NULL,
                engine_type VARCHAR(20) NOT NULL,
                seats INTEGER NOT NULL,
                daily_rate NUMERIC(10,2) NOT NULL,
                color VARCHAR(50) NOT NULL,
                mileage INTEGER DEFAULT 0,
                image_url TEXT,
                status VARCHAR(20) DEFAULT 'available',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """))
        conn.execute(text("""
            CREATE TABLE rentals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id),
                vehicle_id UUID NOT NULL REFERENCES vehicles(id),
                start_date TIMESTAMPTZ NOT NULL,
                end_date TIMESTAMPTZ NOT NULL,
                total_price NUMERIC(10,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """))
        conn.execute(text("""
            INSERT INTO vehicles (id, brand, model, year, license_plate,
                                  engine_type, seats, daily_rate, color)
            VALUES (gen_random_uuid(), 'TestBrand', 'TestModel', 2020,
                    'TEST001', 'petrol', 5, 100.00, 'Red')
        """))
    engine.dispose()


class TestCategoriesMigration:
    """Test the b3c4d5e6f7a8 migration (add categories + update vehicles)."""

    @pytest.fixture(autouse=True)
    def _fresh_pg(self):
        with PostgresContainer(POSTGRES_IMAGE, driver="asyncpg") as pg:
            self.async_url = pg.get_connection_url()
            self.sync_url = self.async_url.replace("+asyncpg", "", 1)
            yield

    def _stamp_and_upgrade(self, from_rev: str, to_rev: str):
        cfg = _alembic_cfg(self.async_url)
        with patch("app.config.settings.DATABASE_URL", self.async_url):
            command.stamp(cfg, from_rev)
            command.upgrade(cfg, to_rev)

    def _downgrade(self, to_rev: str):
        cfg = _alembic_cfg(self.async_url)
        with patch("app.config.settings.DATABASE_URL", self.async_url):
            command.downgrade(cfg, to_rev)

    def test_upgrade_creates_categories_table(self):
        # Given
        _create_pre_migration_schema(self.sync_url)

        # When
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # Then
        engine = create_engine(self.sync_url)
        tables = set(inspect(engine).get_table_names())
        engine.dispose()
        assert "categories" in tables

    def test_upgrade_adds_new_vehicle_columns(self):
        # Given
        _create_pre_migration_schema(self.sync_url)

        # When
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # Then
        engine = create_engine(self.sync_url)
        columns = {c["name"] for c in inspect(engine).get_columns("vehicles")}
        engine.dispose()
        assert "vin" in columns
        assert "horsepower" in columns
        assert "trunk_capacity" in columns
        assert "daily_base_price" in columns
        assert "category_id" in columns

    def test_upgrade_backfills_existing_vehicle(self):
        # Given
        _create_pre_migration_schema(self.sync_url)

        # When
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # Then
        engine = create_engine(self.sync_url)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT vin, horsepower, category_id FROM vehicles")
            ).first()
        engine.dispose()
        assert row is not None
        assert row.vin is not None
        assert row.horsepower == 100
        assert row.category_id is not None

    def test_upgrade_creates_check_constraints(self):
        # Given
        _create_pre_migration_schema(self.sync_url)

        # When
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # Then
        engine = create_engine(self.sync_url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid = 'vehicles'::regclass AND contype = 'c'"
                )
            )
            names = {r[0] for r in result.all()}
        engine.dispose()
        assert "ck_vehicle_horsepower_positive" in names
        assert "ck_vehicle_seats_positive" in names
        assert "ck_vehicle_trunk_capacity_non_negative" in names

    def test_upgrade_creates_foreign_key(self):
        # Given
        _create_pre_migration_schema(self.sync_url)

        # When
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # Then
        engine = create_engine(self.sync_url)
        fks = inspect(engine).get_foreign_keys("vehicles")
        engine.dispose()
        fk_names = {fk["name"] for fk in fks if fk.get("name")}
        assert "fk_vehicles_category_id" in fk_names

    def test_downgrade_removes_categories_and_columns(self):
        # Given
        _create_pre_migration_schema(self.sync_url)
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # When
        self._downgrade("a1b2c3d4e5f6")

        # Then
        engine = create_engine(self.sync_url)
        tables = set(inspect(engine).get_table_names())
        columns = {c["name"] for c in inspect(engine).get_columns("vehicles")}
        engine.dispose()
        assert "categories" not in tables
        assert "vin" not in columns
        assert "category_id" not in columns
        assert "daily_rate" in columns

    def test_upgrade_downgrade_upgrade_cycle(self):
        # Given
        _create_pre_migration_schema(self.sync_url)

        # When
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")
        self._downgrade("a1b2c3d4e5f6")
        self._stamp_and_upgrade("a1b2c3d4e5f6", "b3c4d5e6f7a8")

        # Then
        engine = create_engine(self.sync_url)
        tables = set(inspect(engine).get_table_names())
        engine.dispose()
        assert "categories" in tables
