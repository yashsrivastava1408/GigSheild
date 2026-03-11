from app.db.session import SessionLocal
from app.services.scheduler import expire_policies


def main() -> None:
    db = SessionLocal()
    try:
        expired = expire_policies(db)
        print(f"Expired {expired} policies.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
