import os
import json
from shutil import copy2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ORDERS_FILE = BASE_DIR / "orders.json"

def load_json(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def backup(path):
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        copy2(path, bak)
        print(f"Backup criado: {bak}")


def main():
    import db

    db.init_db()

    products = []
    coupons = {}
    users = load_json(USERS_FILE)
    orders = load_json(ORDERS_FILE)

    # try to import PRODUCTS and COUPONS from store if available
    try:
        from store import PRODUCTS, COUPONS
        products = PRODUCTS
        coupons = COUPONS
    except Exception:
        print("Não foi possível importar PRODUCTS/COUPONS de store.py; migrando apenas JSONs se existirem.")

    db.migrate_from_memory(products, coupons, users, orders)
    print("Migração concluída.")

    # make backups
    backup(USERS_FILE)
    backup(ORDERS_FILE)


if __name__ == "__main__":
    main()
