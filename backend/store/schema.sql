-- Cordillera: esquema de la base.
--
-- Nucleo relacional para lo que tiene logica de negocio (saldos, vencimientos, agregados),
-- y una columna `extra` JSON en cada tabla para propiedades que el cliente quiera sumar sin
-- migrar nada. Los tipos de documento nuevos que todavia no tienen forma viven en `document`.
--
-- Todo monto se guarda en centavos enteros. Ninguna cuenta pasa por un float.
-- Toda fecha se guarda como texto ISO `YYYY-MM-DD`.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- identidad y acceso

CREATE TABLE IF NOT EXISTS app_user (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    display_name  TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('duenio', 'compras', 'ventas')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    extra         TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,            -- JSON
    label       TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_by  TEXT NOT NULL DEFAULT ''
);

-- ---------------------------------------------------------------- procedencia

-- Cada fila que entra del portal queda guardada tal cual vino, para poder rehacer la
-- normalizacion sin volver a pedirla y para mostrar de donde salio cada dato.
CREATE TABLE IF NOT EXISTS raw_record (
    id           INTEGER PRIMARY KEY,
    dataset      TEXT NOT NULL,
    external_id  TEXT NOT NULL,
    payload      TEXT NOT NULL,           -- JSON tal como lo sirvio el portal
    content_hash TEXT NOT NULL,
    fetched_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (dataset, external_id, content_hash)
);
CREATE INDEX IF NOT EXISTS raw_record_dataset ON raw_record (dataset, external_id);

CREATE TABLE IF NOT EXISTS sync_run (
    id          INTEGER PRIMARY KEY,
    started_at  TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    trigger     TEXT NOT NULL,            -- 'programada' | 'manual' | 'agente'
    status      TEXT NOT NULL DEFAULT 'corriendo',
    summary     TEXT NOT NULL DEFAULT '{}'
);

-- ---------------------------------------------------------------- proveedores

CREATE TABLE IF NOT EXISTS supplier (
    id            INTEGER PRIMARY KEY,
    slug          TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    cuit          TEXT,
    email         TEXT,
    phone         TEXT,
    address       TEXT,
    terms_days    INTEGER,                -- 30, 45, 60: lo acordado con el proveedor
    terms_raw     TEXT,
    confirmed     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    extra         TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS supplier_cuit ON supplier (cuit);

-- Cada forma en que alguien escribio el nombre de un proveedor, y a quien resolvio.
CREATE TABLE IF NOT EXISTS supplier_alias (
    id          INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES supplier (id) ON DELETE CASCADE,
    spelling    TEXT NOT NULL UNIQUE,
    method      TEXT NOT NULL,            -- exact | signature | fuzzy | persona
    confidence  REAL NOT NULL DEFAULT 1.0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------- productos y rubros

CREATE TABLE IF NOT EXISTS category (
    id         INTEGER PRIMARY KEY,
    slug       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    extra      TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS category_alias (
    id          INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES category (id) ON DELETE CASCADE,
    spelling    TEXT NOT NULL UNIQUE,
    method      TEXT NOT NULL,
    confidence  REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS product (
    id           INTEGER PRIMARY KEY,
    external_id  TEXT NOT NULL UNIQUE,    -- p1, p2... el id del portal
    code         TEXT NOT NULL,           -- COR-0001
    description  TEXT NOT NULL DEFAULT '',
    category_id  INTEGER REFERENCES category (id) ON DELETE SET NULL,
    subcategory  TEXT,
    price_cents  INTEGER,
    stock        INTEGER,
    image_url    TEXT,
    first_seen   TEXT NOT NULL DEFAULT (date('now')),
    last_seen    TEXT NOT NULL DEFAULT (date('now')),
    extra        TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS product_code ON product (code);
CREATE INDEX IF NOT EXISTS product_category ON product (category_id);

-- El portal solo publica el precio de hoy. La evolucion se construye guardando una foto
-- por dia: sin esto no hay historia posible.
CREATE TABLE IF NOT EXISTS price_snapshot (
    id          INTEGER PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES product (id) ON DELETE CASCADE,
    taken_on    TEXT NOT NULL,
    price_cents INTEGER,
    stock       INTEGER,
    source      TEXT NOT NULL DEFAULT 'portal',
    UNIQUE (product_id, taken_on, source)
);
CREATE INDEX IF NOT EXISTS price_snapshot_date ON price_snapshot (taken_on);

-- ---------------------------------------------------------------- facturas y plata

CREATE TABLE IF NOT EXISTS invoice (
    id            INTEGER PRIMARY KEY,
    external_id   TEXT UNIQUE,            -- f89 en el portal, NULL si entro por archivo
    number        TEXT NOT NULL,
    supplier_id   INTEGER REFERENCES supplier (id) ON DELETE SET NULL,
    product_id    INTEGER REFERENCES product (id) ON DELETE SET NULL,
    issued_on     TEXT,
    due_on        TEXT,
    amount_cents  INTEGER NOT NULL DEFAULT 0,
    paid_cents    INTEGER NOT NULL DEFAULT 0,
    source_kind   TEXT NOT NULL DEFAULT 'portal',   -- portal | pdf | pdf-escaneado | excel | manual
    source_file   TEXT,
    status        TEXT NOT NULL DEFAULT 'vigente',  -- vigente | en-revision | anulada
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    extra         TEXT NOT NULL DEFAULT '{}',
    UNIQUE (supplier_id, number)
);
CREATE INDEX IF NOT EXISTS invoice_due ON invoice (due_on);
CREATE INDEX IF NOT EXISTS invoice_supplier ON invoice (supplier_id);

-- Pagos a cuenta: una factura puede tener varios, y el saldo sale de sumarlos.
CREATE TABLE IF NOT EXISTS payment (
    id          INTEGER PRIMARY KEY,
    external_id TEXT UNIQUE,
    reference   TEXT NOT NULL,
    invoice_id  INTEGER REFERENCES invoice (id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES supplier (id) ON DELETE SET NULL,
    paid_on     TEXT,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    created_by  TEXT NOT NULL DEFAULT 'portal',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    extra       TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS payment_invoice ON payment (invoice_id);

-- El recibo es el comprobante de recepcion de la factura, no un pago. Se emite hasta la
-- fecha de vencimiento.
CREATE TABLE IF NOT EXISTS receipt (
    id          INTEGER PRIMARY KEY,
    number      TEXT NOT NULL UNIQUE,
    invoice_id  INTEGER NOT NULL REFERENCES invoice (id) ON DELETE CASCADE,
    issued_on   TEXT NOT NULL DEFAULT (date('now')),
    issued_by   TEXT NOT NULL DEFAULT '',
    pdf_path    TEXT,
    extra       TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS receipt_invoice ON receipt (invoice_id);

CREATE TABLE IF NOT EXISTS purchase_order (
    id             INTEGER PRIMARY KEY,
    external_id    TEXT UNIQUE,
    number         TEXT NOT NULL,
    supplier_id    INTEGER REFERENCES supplier (id) ON DELETE SET NULL,
    product_id     INTEGER REFERENCES product (id) ON DELETE SET NULL,
    ordered_on     TEXT,
    quantity       INTEGER,
    estimated_cents INTEGER,
    status         TEXT NOT NULL DEFAULT '',
    status_raw     TEXT,
    extra          TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS purchase_order_supplier ON purchase_order (supplier_id);

-- ---------------------------------------------------------------- ventas

CREATE TABLE IF NOT EXISTS sale (
    id           INTEGER PRIMARY KEY,
    code         TEXT NOT NULL,
    sold_on      TEXT,
    product_id   INTEGER REFERENCES product (id) ON DELETE SET NULL,
    customer     TEXT,
    quantity     INTEGER,
    unit_cents   INTEGER,
    total_cents  INTEGER,
    -- 'valida' suma; 'duplicada' y 'conflicto' no suman nunca
    status       TEXT NOT NULL DEFAULT 'valida' CHECK (status IN ('valida', 'duplicada', 'conflicto', 'rota')),
    status_note  TEXT NOT NULL DEFAULT '',
    row_hash     TEXT NOT NULL,
    extra        TEXT NOT NULL DEFAULT '{}',
    UNIQUE (code, row_hash)
);
CREATE INDEX IF NOT EXISTS sale_date ON sale (sold_on);
CREATE INDEX IF NOT EXISTS sale_code ON sale (code);
CREATE INDEX IF NOT EXISTS sale_status ON sale (status);

-- ---------------------------------------------------------------- bandeja y avisos

CREATE TABLE IF NOT EXISTS message (
    id           INTEGER PRIMARY KEY,
    external_id  TEXT UNIQUE,
    received_on  TEXT,
    sender       TEXT NOT NULL DEFAULT '',
    supplier_id  INTEGER REFERENCES supplier (id) ON DELETE SET NULL,
    subject      TEXT NOT NULL DEFAULT '',
    body         TEXT NOT NULL DEFAULT '',
    invoice_id   INTEGER REFERENCES invoice (id) ON DELETE SET NULL,
    -- los avisos de stock apuntan a un producto, no a una factura
    product_id   INTEGER REFERENCES product (id) ON DELETE SET NULL,
    kind         TEXT NOT NULL DEFAULT 'otro',   -- reclamo | vencimiento | stock | otro
    resolved     INTEGER NOT NULL DEFAULT 0,
    resolved_by  TEXT,
    resolved_at  TEXT,
    extra        TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS message_resolved ON message (resolved, received_on);

-- Un evento es algo que paso y hay que avisar. La entrega es aparte: un evento puede
-- salir por varios canales y se reintenta sin volver a dispararlo.
CREATE TABLE IF NOT EXISTS alert_event (
    id           INTEGER PRIMARY KEY,
    rule         TEXT NOT NULL,
    dedupe_key   TEXT NOT NULL UNIQUE,
    severity     TEXT NOT NULL DEFAULT 'aviso',  -- aviso | urgente
    title        TEXT NOT NULL,
    body         TEXT NOT NULL DEFAULT '',
    entity_kind  TEXT,
    entity_id    INTEGER,
    due_on       TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    acknowledged INTEGER NOT NULL DEFAULT 0,
    extra        TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS alert_event_created ON alert_event (created_at);

CREATE TABLE IF NOT EXISTS alert_delivery (
    id         INTEGER PRIMARY KEY,
    event_id   INTEGER NOT NULL REFERENCES alert_event (id) ON DELETE CASCADE,
    channel    TEXT NOT NULL,             -- whatsapp | bandeja
    recipient  TEXT NOT NULL DEFAULT '',
    status     TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente | entregado | fallido
    detail     TEXT NOT NULL DEFAULT '',
    sent_at    TEXT,
    UNIQUE (event_id, channel, recipient)
);

-- ---------------------------------------------------------------- calendario

CREATE TABLE IF NOT EXISTS calendar_event (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    on_date     TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'vencimiento',  -- vencimiento | recordatorio
    invoice_id  INTEGER REFERENCES invoice (id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES supplier (id) ON DELETE SET NULL,
    amount_cents INTEGER,
    note        TEXT NOT NULL DEFAULT '',
    moved_from  TEXT,
    created_by  TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    extra       TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS calendar_event_date ON calendar_event (on_date);

-- ---------------------------------------------------------------- revision humana

-- Todo lo que la normalizacion no pudo resolver sola cae aca en vez de adivinarse.
CREATE TABLE IF NOT EXISTS review_item (
    id           INTEGER PRIMARY KEY,
    kind         TEXT NOT NULL,           -- proveedor | rubro | venta-duplicada | factura | fecha | monto
    dedupe_key   TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    detail       TEXT NOT NULL DEFAULT '',
    raw          TEXT NOT NULL DEFAULT '{}',        -- lo que vino
    candidates   TEXT NOT NULL DEFAULT '[]',        -- que propone el sistema, con su puntaje
    entity_kind  TEXT,
    entity_id    INTEGER,
    status       TEXT NOT NULL DEFAULT 'pendiente', -- pendiente | resuelto | descartado
    resolution   TEXT NOT NULL DEFAULT '{}',
    resolved_by  TEXT,
    resolved_at  TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS review_item_status ON review_item (status, kind);

-- ---------------------------------------------------------------- documentos sueltos

-- Archivos que entran por el portal o que sube una persona, y cualquier tipo de documento
-- que todavia no tiene tabla propia. Lo que se le extrajo vive en `parsed` como JSON.
CREATE TABLE IF NOT EXISTS document (
    id           INTEGER PRIMARY KEY,
    kind         TEXT NOT NULL DEFAULT 'factura',
    filename     TEXT NOT NULL,
    mime         TEXT NOT NULL DEFAULT '',
    stored_path  TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    parsed       TEXT NOT NULL DEFAULT '{}',
    parser       TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'nuevo',   -- nuevo | leido | aplicado | en-revision | fallido
    invoice_id   INTEGER REFERENCES invoice (id) ON DELETE SET NULL,
    uploaded_by  TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    extra        TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS document_status ON document (status, kind);

-- ---------------------------------------------------------------- vistas de negocio

-- Saldo real de cada factura: lo facturado menos lo efectivamente pagado.
CREATE VIEW IF NOT EXISTS invoice_balance AS
SELECT
    i.id,
    i.number,
    i.supplier_id,
    i.issued_on,
    i.due_on,
    i.amount_cents,
    COALESCE(SUM(p.amount_cents), 0)                        AS paid_cents,
    i.amount_cents - COALESCE(SUM(p.amount_cents), 0)       AS balance_cents,
    CASE
        WHEN COALESCE(SUM(p.amount_cents), 0) <= 0                THEN 'impaga'
        WHEN COALESCE(SUM(p.amount_cents), 0) >= i.amount_cents   THEN 'saldada'
        ELSE 'parcial'
    END                                                     AS payment_state,
    EXISTS (SELECT 1 FROM receipt r WHERE r.invoice_id = i.id) AS has_receipt,
    CAST(julianday('now') - julianday(i.due_on) AS INTEGER) AS days_overdue
FROM invoice i
LEFT JOIN payment p ON p.invoice_id = i.id
WHERE i.status <> 'anulada'
GROUP BY i.id;

-- Lo que le debemos a cada proveedor, y hace cuanto.
CREATE VIEW IF NOT EXISTS supplier_position AS
SELECT
    s.id                                        AS supplier_id,
    s.slug,
    s.name,
    s.cuit,
    s.email,
    s.terms_days,
    COUNT(b.id)                                 AS invoice_count,
    COALESCE(SUM(b.amount_cents), 0)            AS purchased_cents,
    COALESCE(SUM(b.paid_cents), 0)              AS paid_cents,
    COALESCE(SUM(b.balance_cents), 0)           AS owed_cents,
    MAX(CASE WHEN b.balance_cents > 0 THEN b.days_overdue END) AS oldest_overdue_days
FROM supplier s
LEFT JOIN invoice_balance b ON b.supplier_id = s.id
GROUP BY s.id;

-- Ventas que se pueden sumar: las duplicadas y las rotas quedan afuera a proposito.
CREATE VIEW IF NOT EXISTS sale_valid AS
SELECT * FROM sale WHERE status = 'valida';
