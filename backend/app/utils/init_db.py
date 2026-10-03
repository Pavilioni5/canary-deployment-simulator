"""
Database Initialization Utility Script.
Run via: python -m app.utils.init_db
"""
import sys
from app.database import init_db, check_db_tables, engine
from app.config import settings


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
    except Exception as e:
        print(f"[-] Database initialization error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
