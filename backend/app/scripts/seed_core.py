from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Product, Role, User


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


@dataclass(frozen=True)
class ProductSeed:
    code: str
    name: str
    unit: str = "liter"


ROLE_SEEDS = [
    RoleSeed(slug="admin", name="Administrator"),
    RoleSeed(slug="analyst", name="Analyst"),
]

USER_SEEDS = [
    UserSeed(
        email="admin@fuelsight.local",
        password="admin12345",
        display_name="FuelSight Admin",
        role_slug="admin",
    ),
    UserSeed(
        email="analyst@fuelsight.local",
        password="analyst12345",
        display_name="FuelSight Analyst",
        role_slug="analyst",
    ),
]

PRODUCT_SEEDS = [
    ProductSeed(code="AI_92", name="Бензин АИ-92"),
    ProductSeed(code="AI_95", name="Бензин АИ-95"),
    ProductSeed(code="DT_S", name="ДТ летнее ЕВРО"),
    ProductSeed(code="DT_W", name="ДТ зимнее ЕВРО"),
]


def upsert_roles(session: Session) -> tuple[int, int]:
    created = 0
    updated = 0

    role_slugs = [item.slug for item in ROLE_SEEDS]
    existing = {
        role.slug: role
        for role in session.scalars(select(Role).where(Role.slug.in_(role_slugs)))
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
    created = 0
    updated = 0

    roles_by_slug = {role.slug: role for role in session.scalars(select(Role))}
    user_emails = [item.email for item in USER_SEEDS]
    existing = {
        user.email: user
        for user in session.scalars(select(User).where(User.email.in_(user_emails)))
    }

    for item in USER_SEEDS:
        role = roles_by_slug[item.role_slug]
        password_hash = hash_password(item.password)
        current = existing.get(item.email)

        if current is None:
            session.add(
                User(
                    email=item.email,
                    password_hash=password_hash,
                    display_name=item.display_name,
                    role_id=role.id,
                    is_active=True,
                )
            )
            created += 1
            continue

        current.display_name = item.display_name
        current.role_id = role.id
        current.is_active = True
        current.password_hash = password_hash
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


def run_seed() -> None:
    with SessionLocal() as session:
        roles_created, roles_updated = upsert_roles(session)
        session.flush()
        users_created, users_updated = upsert_users(session)
        products_created, products_updated = upsert_products(session)
        session.commit()

    print(
        "Seed completed: "
        f"roles(created={roles_created}, updated={roles_updated}), "
        f"users(created={users_created}, updated={users_updated}), "
        f"products(created={products_created}, updated={products_updated})"
    )


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
