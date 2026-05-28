import os
import random
import string
import unittest

import db
import store


def random_email():
    token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"test_{token}@example.com"


class DummyHandler:
    def __init__(self, token):
        self.headers = {"Authorization": f"Bearer {token}"}


class StoreAuthTests(unittest.TestCase):
    def setUp(self):
        db.init_db()
        self.session = db.SessionLocal()
        self.clean_emails = []

    def tearDown(self):
        for email in self.clean_emails:
            user = self.session.query(db.User).filter_by(email=email).first()
            if user:
                self.session.delete(user)
        self.session.commit()
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        db.ENGINE.dispose()

    def test_create_user_session_and_refresh_token(self):
        email = random_email()
        password = "senha123"
        user = db.User(
            name="Teste Unitário",
            email=email,
            password_hash=store.hash_password(password),
            cpf="00000000000",
            address="Rua Teste, 123",
            is_admin=False,
        )
        self.session.add(user)
        self.session.commit()
        self.clean_emails.append(email)

        session_db = db.SessionLocal()
        try:
            user_session = store.create_user_session(session_db, user)
            access_token = user_session.access_token
            refresh_token = user_session.refresh_token
            access_expires_at = user_session.access_expires_at
            refresh_expires_at = user_session.refresh_expires_at
        finally:
            session_db.close()

        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertGreater(access_expires_at, store.datetime.now())
        self.assertGreater(refresh_expires_at, store.datetime.now())

        loaded_user = store.get_user_by_access_token(access_token)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user["email"], email)
        self.assertFalse(loaded_user["is_admin"])

        refresh_session = store.get_user_by_refresh_token(refresh_token)
        self.assertIsNotNone(refresh_session)
        self.assertEqual(refresh_session.user_id, user.id)

        handler = DummyHandler(access_token)
        auth_user = store.get_auth_user(handler)
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user["email"], email)

    def test_access_token_revocation_and_refresh_cycle(self):
        email = random_email()
        user = db.User(
            name="Admin Teste",
            email=email,
            password_hash=store.hash_password("adminpass"),
            cpf="11122233344",
            address="Avenida Teste, 987",
            is_admin=True,
        )
        self.session.add(user)
        self.session.commit()
        self.clean_emails.append(email)

        session_db = db.SessionLocal()
        try:
            user_session = store.create_user_session(session_db, user)
            access_token = user_session.access_token
            refresh_token = user_session.refresh_token
        finally:
            session_db.close()

        # Revoke via logout-style update
        session_db = db.SessionLocal()
        try:
            stored = session_db.query(db.UserSession).filter_by(access_token=access_token).first()
            self.assertIsNotNone(stored)
            stored.revoked = True
            session_db.commit()
        finally:
            session_db.close()

        self.assertIsNone(store.get_user_by_access_token(access_token))
        self.assertIsNone(store.get_user_by_refresh_token(refresh_token))


if __name__ == "__main__":
    unittest.main()
