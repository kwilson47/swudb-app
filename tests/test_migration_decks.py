import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parent.parent / 'scripts' / 'run_migration_decks.py'


def _load_migration_module():
    spec = importlib.util.spec_from_file_location('run_migration_decks', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MigrationDecksStructureTests(unittest.TestCase):
    """Structural assertions only — no live MySQL service exists in CI, so this
    checks the DDL text itself rather than executing it (matches the
    mock/stub-only posture already used in tests/test_smoke.py)."""

    @classmethod
    def setUpClass(cls):
        cls.module = _load_migration_module()

    def test_migration_has_exactly_two_create_table_statements(self):
        self.assertEqual(len(self.module.MIGRATION), 2)
        self.assertEqual(
            self.module.STEP_NAMES,
            ['CREATE TABLE decks', 'CREATE TABLE deck_cards'],
        )

    def test_decks_table_ddl(self):
        decks_sql = self.module.MIGRATION[0]
        self.assertRegex(decks_sql, r'CREATE TABLE IF NOT EXISTS decks\s*\(')
        for fragment in (
            'session_id',
            'user_id',
            'name',
            "format      ENUM('premier','eternal','twin_suns')",
            'created_at',
            'updated_at',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, decks_sql)

    def test_deck_cards_table_ddl(self):
        deck_cards_sql = self.module.MIGRATION[1]
        self.assertRegex(deck_cards_sql, r'CREATE TABLE IF NOT EXISTS deck_cards\s*\(')
        for fragment in (
            'deck_id',
            'card_uid',
            'quantity',
            'UNIQUE KEY uq_deck_card (deck_id, card_uid)',
            'FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, deck_cards_sql)

    def test_main_exits_cleanly_without_mysql_env_vars(self):
        """The script's own guard must fail safely (SystemExit) rather than
        hang or crash when run with no MySQL credentials configured — this is
        what keeps accidental invocation in CI (no service container) inert."""
        env_without_mysql = {
            k: v for k, v in os.environ.items() if not k.startswith('MYSQL_')
        }
        old_argv = sys.argv
        sys.argv = ['run_migration_decks.py']
        try:
            with mock.patch.dict(os.environ, env_without_mysql, clear=True):
                with self.assertRaises(SystemExit):
                    self.module.main()
        finally:
            sys.argv = old_argv


if __name__ == '__main__':
    unittest.main()
