"""
Database Initialization & Admin Seeding Utility Script.
Run via: python -m app.utils.init_db
"""
import sys
from app.database import init_db, check_db_tables, SessionLocal
from app.config import settings
from app.models.user import User
from app.auth.security import hash_password


def seed_admin_user():
    """Seed default administrator user if not present."""
    db = SessionLocal()
    try:
        admin_email = settings.DEFAULT_ADMIN_EMAIL.lower().strip()
        existing = db.query(User).filter(User.email == admin_email).first()
        if not existing:
            admin = User(
                email=admin_email,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                full_name=settings.DEFAULT_ADMIN_NAME,
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"[+] Default Admin seeded: {admin_email} (Role: ADMIN)")
        else:
            print(f"[*] Admin user already exists: {admin_email}")
    finally:
        db.close()


def main():
    print(f"[*] Initializing database schema for: {settings.APP_NAME}")
    print(f"[*] Target Database URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    
    try:
        init_db()
        tables = check_db_tables()
        print("[+] Database tables initialized successfully:")
        for t in sorted(tables):
            print(f"    - {t}")
        
        expected_tables = {
            "users", "deployments", "deployment_versions",
            "traffic_configs", "metrics", "deployment_events", "logs"
        }
        missing = expected_tables - set(tables)
        if missing:
            print(f"[-] Warning: Missing tables: {missing}")
            sys.exit(1)
        else:
            print(f"[+] All {len(expected_tables)} required academic schema tables are verified!")

        # Seed initial admin user
        seed_admin_user()
    except Exception as e:
        print(f"[-] Database initialization error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
