import argparse
import os

try:
    import mysql.connector
except ImportError as exc:
    raise SystemExit(
        "mysql-connector-python is required. Install it with "
        "`pip install mysql-connector-python`."
    ) from exc

MIGRATION = [
    """
    CREATE TABLE IF NOT EXISTS decks (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        session_id  VARCHAR(64)  NOT NULL,
        user_id     BIGINT       NULL,
        name        VARCHAR(128) NOT NULL DEFAULT 'Unnamed Deck',
        format      ENUM('premier','eternal','twin_suns') NOT NULL DEFAULT 'premier',
        created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_decks_session_id (session_id),
        INDEX idx_decks_user_id    (user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS deck_cards (
        id        INT AUTO_INCREMENT PRIMARY KEY,
        deck_id   INT         NOT NULL,
        card_uid  VARCHAR(64) NOT NULL,
        quantity  TINYINT     NOT NULL DEFAULT 1,
        UNIQUE KEY uq_deck_card (deck_id, card_uid),
        FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
        INDEX idx_deck_cards_deck_id (deck_id)
    )
    """,
]

STEP_NAMES = [
    "CREATE TABLE decks",
    "CREATE TABLE deck_cards",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Create deck tables in MySQL.")
    parser.add_argument("--mysql-host",     default=os.environ.get("MYSQL_HOST"))
    parser.add_argument("--mysql-port",     type=int, default=int(os.environ.get("MYSQL_PORT", "3306")))
    parser.add_argument("--mysql-database", default=os.environ.get("MYSQL_DATABASE", "swudb"))
    parser.add_argument("--mysql-user",     default=os.environ.get("MYSQL_USER"))
    parser.add_argument("--mysql-password", default=os.environ.get("MYSQL_PASSWORD"))
    parser.add_argument("--ssl-ca",         default=os.environ.get("MYSQL_SSL_CA"))
    parser.add_argument("--ssl-disabled",   action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.mysql_host or not args.mysql_user or not args.mysql_password:
        raise SystemExit(
            "Missing MySQL connection details. Set MYSQL_HOST, MYSQL_USER, "
            "MYSQL_PASSWORD or pass the corresponding flags."
        )

    kwargs = {
        "host": args.mysql_host,
        "port": args.mysql_port,
        "user": args.mysql_user,
        "password": args.mysql_password,
        "database": args.mysql_database,
    }
    if args.ssl_disabled:
        kwargs["ssl_disabled"] = True
    elif args.ssl_ca:
        kwargs["ssl_disabled"] = False
        kwargs["ssl_ca"] = args.ssl_ca

    connection = mysql.connector.connect(**kwargs)
    try:
        cursor = connection.cursor()
        try:
            for i, sql in enumerate(MIGRATION):
                step = i + 1
                print(f"[{step}/{len(MIGRATION)}] {STEP_NAMES[i]} ...", end=" ", flush=True)
                cursor.execute(sql)
                connection.commit()
                print("done")
        finally:
            cursor.close()
    finally:
        connection.close()

    print("Migration complete.")


if __name__ == "__main__":
    main()
