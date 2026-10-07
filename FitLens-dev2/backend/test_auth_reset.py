"""
Automated Test Suite for FitLens Reset Password functionality:
- Dynamic LAN IP resolution
- Forgot password token generation and storage
- Standalone GET /reset-password HTML rendering
- POST /api/auth/reset-password (JSON and HTML Form POST)
- Token expiry and single-use invalidation
- Password verification in database
"""
import os
import sys

# Configure testing environment variables BEFORE backend.app is imported
os.environ['FLASK_ENV'] = 'testing'
os.environ['MONGO_DB_NAME'] = 'fitlens_test'
os.environ['FITLENS_DATA_ROOT'] = 'data_test'
os.environ['JWT_SECRET_KEY'] = 'fitlens_test_suite_dedicated_cryptographic_secret_key_32bytes_minimum_2026'

import unittest
import json
import datetime as dt
import bcrypt
from backend.app import (
    app, db, users_col, reset_tokens,
    get_machine_local_ip, get_network_frontend_url
)

class AuthResetPasswordTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.reset_tokens_col = db['reset_tokens']

    def setUp(self):
        # Create a fresh test user
        self.test_email = 'test_reset_user@example.com'
        self.test_password = 'OldPassword123!'
        users_col.delete_many({'email': self.test_email})
        self.reset_tokens_col.delete_many({'email': self.test_email})

        password_hash = bcrypt.hashpw(self.test_password.encode(), bcrypt.gensalt()).decode()
        self.user_doc = {
            'user_id': 'UTESTRESET1',
            'name': 'ResetTester',
            'email': self.test_email,
            'password_hash': password_hash
        }
        users_col.insert_one(self.user_doc)

    def tearDown(self):
        users_col.delete_many({'email': self.test_email})
        self.reset_tokens_col.delete_many({'email': self.test_email})

    def test_01_local_ip_and_frontend_url(self):
        """Verify LAN IP detection and automatic conversion of localhost in reset URLs"""
        ip = get_machine_local_ip()
        self.assertTrue(bool(ip))
        self.assertNotIn(' ', ip)

        url = get_network_frontend_url()
        self.assertNotIn('localhost', url)
        self.assertNotIn('127.0.0.1', url)
        self.assertTrue(url.startswith('http'))

    def test_02_forgot_password_generates_token(self):
        """POST /api/auth/forgot-password creates token document in DB and memory"""
        res = self.client.post('/api/auth/forgot-password', json={'email': self.test_email})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))

        token_doc = self.reset_tokens_col.find_one({'user_id': 'UTESTRESET1', 'used': False})
        self.assertIsNotNone(token_doc)
        token = token_doc['token']
        self.assertTrue(len(token) > 20)
        self.assertIn(token, reset_tokens)

    def test_03_get_reset_password_page(self):
        """GET /reset-password renders standalone responsive HTML page"""
        # Missing token
        res_no_tok = self.client.get('/reset-password')
        self.assertEqual(res_no_tok.status_code, 400)
        self.assertIn(b'No reset token provided', res_no_tok.data)

        # Invalid token
        res_bad_tok = self.client.get('/reset-password?token=invalid_dummy_token')
        self.assertEqual(res_bad_tok.status_code, 400)
        self.assertIn(b'Invalid Reset Link', res_bad_tok.data)

        # Valid token
        self.client.post('/api/auth/forgot-password', json={'email': self.test_email})
        token_doc = self.reset_tokens_col.find_one({'user_id': 'UTESTRESET1', 'used': False})
        valid_token = token_doc['token']

        res_valid = self.client.get(f'/reset-password?token={valid_token}')
        self.assertEqual(res_valid.status_code, 200)
        self.assertIn(b'Set New Password', res_valid.data)
        self.assertIn(b'FitLens AI', res_valid.data)
        self.assertIn(valid_token.encode(), res_valid.data)

    def test_04_reset_password_via_json(self):
        """POST /api/auth/reset-password via JSON payload updates password in database"""
        self.client.post('/api/auth/forgot-password', json={'email': self.test_email})
        token_doc = self.reset_tokens_col.find_one({'user_id': 'UTESTRESET1', 'used': False})
        token = token_doc['token']

        # Short password
        bad_res = self.client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'short',
            'confirm_password': 'short'
        })
        self.assertEqual(bad_res.status_code, 400)
        self.assertIn('at least 8 characters', bad_res.get_json()['error'])

        # Mismatched password
        mismatch_res = self.client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        })
        self.assertEqual(mismatch_res.status_code, 400)
        self.assertIn('do not match', mismatch_res.get_json()['error'])

        # Successful reset
        new_pass = 'BrandNewPassword2026!'
        success_res = self.client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': new_pass,
            'confirm_password': new_pass
        })
        self.assertEqual(success_res.status_code, 200)
        self.assertTrue(success_res.get_json()['success'])

        # Verify password in DB actually changed
        user_after = users_col.find_one({'user_id': 'UTESTRESET1'})
        self.assertTrue(bcrypt.checkpw(new_pass.encode(), user_after['password_hash'].encode()))

        # Token cannot be reused
        reuse_res = self.client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'AnotherPassword123!',
            'confirm_password': 'AnotherPassword123!'
        })
        self.assertEqual(reuse_res.status_code, 400)

    def test_05_reset_password_via_form_post(self):
        """POST /api/auth/reset-password via HTML Form data updates password and returns HTML"""
        self.client.post('/api/auth/forgot-password', json={'email': self.test_email})
        token_doc = self.reset_tokens_col.find_one({'user_id': 'UTESTRESET1', 'used': False})
        token = token_doc['token']

        new_pass = 'FormResetPassword2026!'
        res = self.client.post('/api/auth/reset-password', data={
            'token': token,
            'new_password': new_pass,
            'confirm_password': new_pass
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Password Reset!', res.data)

        # Verify in DB
        user_after = users_col.find_one({'user_id': 'UTESTRESET1'})
        self.assertTrue(bcrypt.checkpw(new_pass.encode(), user_after['password_hash'].encode()))

if __name__ == '__main__':
    unittest.main()
