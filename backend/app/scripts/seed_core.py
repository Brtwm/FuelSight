from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.models import Product, Role, User
from app.repositories import EventCatalogRepository, EventCatalogUpsertRow
from app.services.data_generator_config import CURATED_EVENT_CATALOG


@dataclass(frozen=True)
class RoleSeed:
    slug: str
    name: str


@dataclass(frozen=True)
class UserSeed:
    email: str
    password: str
    display_name: str
    role_slug: str
    is_active: bool = True


@dataclass(frozen=True)
class ProductSeed:
    code: str
    name: str
    unit: str = "liter"


ROLE_SEEDS = [
    RoleSeed(slug="admin", name="Системный администратор"),
    RoleSeed(slug="sales", name="Отдел продаж"),
    RoleSeed(slug="accounting", name="Бухгалтерия"),
    RoleSeed(slug="analyst", name="Аналитический отдел"),
    RoleSeed(slug="director", name="Генеральный директор"),
]

USER_SEEDS = [
    UserSeed(
        email="admin@fuelsight.local",
        password="admin12345",
        display_name="FuelSight Admin",
        role_slug="admin",
    ),
    UserSeed(
        email="sales@fuelsight.local",
        password="sales12345",
        display_name="FuelSight Sales",
        role_slug="sales",
    ),
    UserSeed(
        email="accounting@fuelsight.local",
        password="accounting12345",
        display_name="FuelSight Accounting",
        role_slug="accounting",
    ),
    UserSeed(
        email="analyst@fuelsight.local",
        password="analyst12345",
        display_name="FuelSight Analyst",
        role_slug="analyst",
    ),
    UserSeed(
        email="director@fuelsight.local",
        password="director12345",
        display_name="FuelSight Director",
        role_slug="director",
    ),
]

PIPELINE_USER_SEEDS = [
    UserSeed(
        email="pipeline@fuelsight.local",
        password="pipeline-service-account-disabled",
        display_name="FuelSight Pipeline",
        role_slug="admin",
        is_active=False,
    ),
]

PRODUCT_SEEDS = [
    ProductSeed(code="AI_92", name="Бензин АИ-92"),
    ProductSeed(code="AI_95", name="Бензин АИ-95"),
    ProductSeed(code="DT_S", name="ДТ летнее ЕВРО"),
    ProductSeed(code="DT_W", name="ДТ зимнее ЕВРО"),
]


def should_seed_demo_users(settings: Settings) -> bool:
    return settings.fuelsight_seed_demo_users


def upsert_roles(session: Session) -> tuple[int, int]:
    created = 0
    updated = 0

    role_slugs = [item.slug for item in ROLE_SEEDS]
    existing = {
        role.slug: role for role in session.scalars(select(Role).where(Role.slug.in_(role_slugs)))
    }

    for item in ROLE_SEEDS:
        current = existing.get(item.slug)
        if current is None:
            session.add(Role(slug=item.slug, name=item.name))
            created += 1
            continue

        if current.name != item.name:
            current.name = item.name
            updated += 1

    return created, updated


def upsert_users(session: Session) -> tuple[int, int]:
    return _upsert_user_seeds(session=session, seeds=USER_SEEDS)


def upsert_pipeline_users(session: Session) -> tuple[int, int]:
    return _upsert_user_seeds(session=session, seeds=PIPELINE_USER_SEEDS)


def _upsert_user_seeds(session: Session, seeds: list[UserSeed]) -> tuple[int, int]:
    created = 0
    updated = 0

    roles_by_slug = {role.slug: role for role in session.scalars(select(Role))}
    user_emails = [item.email for item in seeds]
    existing = {
        user.email: user
        for user in session.scalars(select(User).where(User.email.in_(user_emails)))
    }

    for item in seeds:
        role = roles_by_slug[item.role_slug]
        current = existing.get(item.email)

        if current is None:
            session.add(
                User(
                    email=item.email,
                    password_hash=hash_password(item.password),
                    display_name=item.display_name,
                    role_id=role.id,
                    is_active=item.is_active,
                )
            )
            created += 1
            continue

        changed = False
        if current.display_name != item.display_name:
            current.display_name = item.display_name
            changed = True
        if current.role_id != role.id:
            current.role_id = role.id
            changed = True
        if current.is_active != item.is_active:
            current.is_active = item.is_active
            changed = True
        if not verify_password(item.password, current.password_hash):
            current.password_hash = hash_password(item.password)
            changed = True
        if changed:
            updated += 1

    return created, updated


def upsert_products(session: Session) -> tuple[int, int]:
    created = 0
    updated = 0

    existing = {
        product.code: product
        for product in session.scalars(
            select(Product).where(Product.code.in_([item.code for item in PRODUCT_SEEDS]))
        )
    }

    for item in PRODUCT_SEEDS:
        current = existing.get(item.code)
        if current is None:
            session.add(Product(code=item.code, name=item.name, unit=item.unit, is_active=True))
            created += 1
            continue

        changed = False
        if current.name != item.name:
            current.name = item.name
            changed = True
        if current.unit != item.unit:
            current.unit = item.unit
            changed = True
        if not current.is_active:
            current.is_active = True
            changed = True
        if changed:
            updated += 1

    return created, updated


def upsert_event_catalog(session: Session) -> tuple[int, int]:
    repository = EventCatalogRepository(session)
    rows = [
        EventCatalogUpsertRow(
            event_code=item.code,
            title=item.title,
            start_month=item.start_month,
            start_day=item.start_day,
            end_month=item.end_month,
            end_day=item.end_day,
            pressure_score=item.pressure_score,
            demand_delta_pct=item.demand_delta_pct,
            purchase_delta_pct=item.purchase_delta_pct,
            source_mode="db",
            is_active=True,
            metadata_json={"seed": "seed_core"},
        )
        for item in CURATED_EVENT_CATALOG
    ]
    changed = repository.upsert_many(rows)
    return changed, 0


def run_seed() -> None:
    settings = get_settings()
    with SessionLocal() as session:
        roles_created, roles_updated = upsert_roles(session)
        session.flush()
        if should_seed_demo_users(settings):
            users_created, users_updated = upsert_users(session)
        else:
            users_created, users_updated = 0, 0
        pipeline_users_created, pipeline_users_updated = upsert_pipeline_users(session)
        products_created, products_updated = upsert_products(session)
        events_created, events_updated = upsert_event_catalog(session)
        session.commit()

    print(
        "Seed completed: "
        f"roles(created={roles_created}, updated={roles_updated}), "
        f"users(created={users_created}, updated={users_updated}), "
        f"pipeline_users(created={pipeline_users_created}, updated={pipeline_users_updated}), "
        f"products(created={products_created}, updated={products_updated}), "
        f"event_catalog(changed={events_created}, updated={events_updated})"
    )


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
