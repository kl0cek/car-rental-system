-- =============================================================================
-- DriveEase — schemat relacyjny PostgreSQL (czysty SQL, bez ORM).
--
-- Plik jest stosowany przy starcie aplikacji (app/db/bootstrap.py) w sposób
-- idempotentny — wszystkie obiekty tworzone są z IF NOT EXISTS, więc ponowne
-- uruchomienie nie psuje istniejącej bazy.
--
-- Konwencje:
--   * Klucze główne (id) to UUID generowane po stronie aplikacji.
--   * created_at / updated_at mają DEFAULT now(); updated_at jest dodatkowo
--     ustawiany jawnie (updated_at = now()) w każdej operacji UPDATE.
--   * Kolumny "enumowe" (role, status, type, severity...) trzymane są jako
--     VARCHAR — zbiór dozwolonych wartości waliduje warstwa aplikacji (Pydantic),
--     tak jak w pierwotnym modelu.
--   * Unikalność VIN i tablic rejestracyjnych to indeksy CZĘŚCIOWE
--     (WHERE is_active = true) — soft-delete nie blokuje ponownego wprowadzenia.
-- =============================================================================

-- ----------------------------------------------------------------------------
-- categories
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id               UUID NOT NULL PRIMARY KEY,
    name             VARCHAR(7) NOT NULL,
    description      TEXT,
    price_multiplier NUMERIC(5, 3) NOT NULL,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    UNIQUE (name)
);

-- ----------------------------------------------------------------------------
-- users
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              UUID NOT NULL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(10) NOT NULL,
    is_active       BOOLEAN NOT NULL,
    is_verified     BOOLEAN NOT NULL,
    phone           VARCHAR(20),
    avatar_url      TEXT,
    risk_score      NUMERIC(5, 2) NOT NULL,
    last_login_at   TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_user_risk_score_range CHECK (risk_score >= 0 AND risk_score <= 100),
    UNIQUE (email)
);
CREATE INDEX IF NOT EXISTS ix_users_last_login_at ON users (last_login_at);
CREATE INDEX IF NOT EXISTS ix_users_risk_score ON users (risk_score);
CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);

-- ----------------------------------------------------------------------------
-- customer_notes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_notes (
    id          UUID NOT NULL PRIMARY KEY,
    customer_id UUID NOT NULL,
    author_id   UUID NOT NULL,
    body        TEXT NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_customer_notes_author_id ON customer_notes (author_id);
CREATE INDEX IF NOT EXISTS ix_customer_notes_customer_id ON customer_notes (customer_id);

-- ----------------------------------------------------------------------------
-- vehicles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    id               UUID NOT NULL PRIMARY KEY,
    brand            VARCHAR(100) NOT NULL,
    model            VARCHAR(100) NOT NULL,
    year             INTEGER NOT NULL,
    license_plate    VARCHAR(20) NOT NULL,
    vin              VARCHAR(17) NOT NULL,
    engine_type      VARCHAR(8) NOT NULL,
    horsepower       INTEGER NOT NULL,
    seats            INTEGER NOT NULL,
    trunk_capacity   INTEGER NOT NULL,
    daily_base_price NUMERIC(10, 2) NOT NULL,
    color            VARCHAR(6) NOT NULL,
    mileage          INTEGER NOT NULL,
    status           VARCHAR(14) NOT NULL,
    is_active        BOOLEAN NOT NULL,
    avg_rating       NUMERIC(3, 2),
    ratings_count    INTEGER DEFAULT 0 NOT NULL,
    category_id      UUID NOT NULL,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_vehicle_horsepower_positive CHECK (horsepower > 0),
    CONSTRAINT ck_vehicle_seats_positive CHECK (seats > 0),
    CONSTRAINT ck_vehicle_trunk_capacity_non_negative CHECK (trunk_capacity >= 0),
    CONSTRAINT ck_vehicle_mileage_non_negative CHECK (mileage >= 0),
    CONSTRAINT ck_vehicle_avg_rating_range CHECK (avg_rating IS NULL OR (avg_rating >= 1 AND avg_rating <= 5)),
    CONSTRAINT ck_vehicle_ratings_count_non_negative CHECK (ratings_count >= 0),
    FOREIGN KEY (category_id) REFERENCES categories (id)
);
CREATE INDEX IF NOT EXISTS ix_vehicles_brand ON vehicles (brand);
CREATE INDEX IF NOT EXISTS ix_vehicles_category_id ON vehicles (category_id);
CREATE INDEX IF NOT EXISTS ix_vehicles_color ON vehicles (color);
CREATE INDEX IF NOT EXISTS ix_vehicles_daily_base_price ON vehicles (daily_base_price);
CREATE INDEX IF NOT EXISTS ix_vehicles_engine_type ON vehicles (engine_type);
CREATE INDEX IF NOT EXISTS ix_vehicles_status ON vehicles (status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicles_license_plate_active ON vehicles (license_plate) WHERE is_active = true;
CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicles_vin_active ON vehicles (vin) WHERE is_active = true;

-- ----------------------------------------------------------------------------
-- vehicle_images
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_images (
    id         UUID NOT NULL PRIMARY KEY,
    vehicle_id UUID NOT NULL,
    url        TEXT NOT NULL,
    position   INTEGER NOT NULL,
    is_primary BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_vehicle_images_vehicle_id ON vehicle_images (vehicle_id);
CREATE INDEX IF NOT EXISTS ix_vehicle_images_vehicle_id_position ON vehicle_images (vehicle_id, position);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicle_images_one_primary_per_vehicle ON vehicle_images (vehicle_id) WHERE is_primary = true;

-- ----------------------------------------------------------------------------
-- reservations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations (
    id          UUID NOT NULL PRIMARY KEY,
    user_id     UUID NOT NULL,
    vehicle_id  UUID NOT NULL,
    start_date  TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date    TIMESTAMP WITH TIME ZONE NOT NULL,
    status      VARCHAR(9) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
);
CREATE INDEX IF NOT EXISTS ix_reservations_end_date ON reservations (end_date);
CREATE INDEX IF NOT EXISTS ix_reservations_start_date ON reservations (start_date);
CREATE INDEX IF NOT EXISTS ix_reservations_status ON reservations (status);
CREATE INDEX IF NOT EXISTS ix_reservations_user_id ON reservations (user_id);
CREATE INDEX IF NOT EXISTS ix_reservations_vehicle_id ON reservations (vehicle_id);

-- ----------------------------------------------------------------------------
-- rentals
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rentals (
    id               UUID NOT NULL PRIMARY KEY,
    reservation_id   UUID NOT NULL,
    pickup_date      TIMESTAMP WITH TIME ZONE NOT NULL,
    return_date      TIMESTAMP WITH TIME ZONE,
    mileage_start    INTEGER NOT NULL,
    mileage_end      INTEGER,
    fuel_level_start NUMERIC(5, 2) NOT NULL,
    fuel_level_end   NUMERIC(5, 2),
    damage_notes     TEXT,
    employee_id      UUID NOT NULL,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at       TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_rental_mileage_start_non_negative CHECK (mileage_start >= 0),
    CONSTRAINT ck_rental_mileage_end_gte_start CHECK (mileage_end IS NULL OR mileage_end >= mileage_start),
    CONSTRAINT ck_rental_fuel_level_start_range CHECK (fuel_level_start >= 0 AND fuel_level_start <= 100),
    CONSTRAINT ck_rental_fuel_level_end_range CHECK (fuel_level_end IS NULL OR (fuel_level_end >= 0 AND fuel_level_end <= 100)),
    CONSTRAINT ck_rental_return_after_pickup CHECK (return_date IS NULL OR return_date > pickup_date),
    UNIQUE (reservation_id),
    FOREIGN KEY (reservation_id) REFERENCES reservations (id),
    FOREIGN KEY (employee_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_rentals_employee_id ON rentals (employee_id);

-- ----------------------------------------------------------------------------
-- rental_price_breakdowns
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rental_price_breakdowns (
    id              UUID NOT NULL PRIMARY KEY,
    rental_id       UUID NOT NULL,
    base_price      NUMERIC(10, 2) NOT NULL,
    risk_multiplier NUMERIC(6, 4) NOT NULL,
    final_price     NUMERIC(10, 2) NOT NULL,
    calculated_at   TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_price_breakdown_base_price_non_negative CHECK (base_price >= 0),
    CONSTRAINT ck_price_breakdown_risk_multiplier_non_negative CHECK (risk_multiplier >= 0),
    CONSTRAINT ck_price_breakdown_final_price_non_negative CHECK (final_price >= 0),
    UNIQUE (rental_id),
    FOREIGN KEY (rental_id) REFERENCES rentals (id)
);

-- ----------------------------------------------------------------------------
-- incidents
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incidents (
    id             UUID NOT NULL PRIMARY KEY,
    customer_id    UUID NOT NULL,
    rental_id      UUID,
    reported_by_id UUID NOT NULL,
    type           VARCHAR(17) NOT NULL,
    severity       VARCHAR(8) NOT NULL,
    title          TEXT NOT NULL,
    description    TEXT NOT NULL,
    cost           NUMERIC(10, 2),
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_incident_cost_non_negative CHECK (cost IS NULL OR cost >= 0),
    FOREIGN KEY (customer_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (rental_id) REFERENCES rentals (id) ON DELETE SET NULL,
    FOREIGN KEY (reported_by_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_incidents_customer_id ON incidents (customer_id);
CREATE INDEX IF NOT EXISTS ix_incidents_rental_id ON incidents (rental_id);
CREATE INDEX IF NOT EXISTS ix_incidents_reported_by_id ON incidents (reported_by_id);
CREATE INDEX IF NOT EXISTS ix_incidents_severity ON incidents (severity);
CREATE INDEX IF NOT EXISTS ix_incidents_type ON incidents (type);

-- ----------------------------------------------------------------------------
-- service_orders
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS service_orders (
    id             UUID NOT NULL PRIMARY KEY,
    vehicle_id     UUID NOT NULL,
    type           VARCHAR(10) NOT NULL,
    status         VARCHAR(11) NOT NULL,
    description    TEXT NOT NULL,
    cost           NUMERIC(10, 2),
    scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_date TIMESTAMP WITH TIME ZONE,
    technician_id  UUID NOT NULL,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_service_order_cost_non_negative CHECK (cost IS NULL OR cost >= 0),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
    CONSTRAINT fk_service_orders_technician_id FOREIGN KEY (technician_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_service_orders_scheduled_date ON service_orders (scheduled_date);
CREATE INDEX IF NOT EXISTS ix_service_orders_status ON service_orders (status);
CREATE INDEX IF NOT EXISTS ix_service_orders_technician_id ON service_orders (technician_id);
CREATE INDEX IF NOT EXISTS ix_service_orders_type ON service_orders (type);
CREATE INDEX IF NOT EXISTS ix_service_orders_vehicle_id ON service_orders (vehicle_id);

-- ----------------------------------------------------------------------------
-- service_history
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS service_history (
    id                 UUID NOT NULL PRIMARY KEY,
    vehicle_id         UUID NOT NULL,
    service_order_id   UUID NOT NULL,
    notes              TEXT NOT NULL,
    parts_replaced     TEXT[] DEFAULT '{}' NOT NULL,
    mileage_at_service INTEGER NOT NULL,
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at         TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT ck_service_history_mileage_non_negative CHECK (mileage_at_service >= 0),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
    FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_service_history_service_order_id ON service_history (service_order_id);
CREATE INDEX IF NOT EXISTS ix_service_history_vehicle_id ON service_history (vehicle_id);
