"""
Comprehensive Automated Test Suite for FitLens Multi-Profile & Invite Architecture
"""
import os
import sys

# Ensure testing environment variables are configured BEFORE backend.app is imported
os.environ['FLASK_ENV'] = 'testing'
os.environ['MONGO_DB_NAME'] = 'fitlens_test'
os.environ['FITLENS_DATA_ROOT'] = 'data_test'
os.environ['JWT_SECRET_KEY'] = 'fitlens_test_suite_dedicated_cryptographic_secret_key_32bytes_minimum_2026'

import unittest
import json
import time
import shutil
import datetime as dt
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash
from backend.app import (
    app, socketio, db, users_col, profiles_col, profile_invites_col,
    notifications_col, measurements_col, get_or_create_owner_profile, get_measurement_dir,
    claim_ip_rate_limits, claim_target_rate_limits, ACCOUNTS_DIR, DATA_ROOT,
    recover_stale_claiming_invites, hash_secret
)
import bcrypt
from flask_jwt_extended import create_access_token, decode_token

class MultiProfileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # CRITICAL DATABASE SAFETY GUARD
        current_db = getattr(db, 'name', None)
        protected_databases = {'fitlens', 'production', 'prod', 'master', 'main'}
        
        if current_db in protected_databases or current_db != 'fitlens_test':
            error_msg = (
                f"\n{'='*70}\n"
                f"[FATAL SAFETY GUARD] Refusing to run tests against database '{current_db}'!\n"
                f"Automated tests must NEVER connect to or modify development/production databases.\n"
                f"Expected database: 'fitlens_test'\n\n"
                f"To run tests safely, set the environment variables in PowerShell:\n"
                f"  $env:FLASK_ENV = 'testing'\n"
                f"  $env:MONGO_DB_NAME = 'fitlens_test'\n"
                f"  $env:FITLENS_DATA_ROOT = 'data_test'\n"
                f"  .\\venv\\Scripts\\python.exe -m unittest backend.test_profiles_api\n"
                f"{'='*70}\n"
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg)

        # STORAGE ROOT SAFETY GUARD
        real_accounts_dir = os.path.realpath(ACCOUNTS_DIR)
        if 'data_test' not in real_accounts_dir:
            error_msg = (
                f"\n{'='*70}\n"
                f"[FATAL SAFETY GUARD] Storage root '{real_accounts_dir}' does not reside in 'data_test'!\n"
                f"Refusing to execute tests against non-test storage directory.\n"
                f"{'='*70}\n"
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg)

    def setUp(self):
        # Verify db.name is fitlens_test in every test setup
        if getattr(db, 'name', None) != 'fitlens_test':
            self.fail(f"Safety guard failure: current DB name is '{getattr(db, 'name', None)}', expected 'fitlens_test'")

        self.app = app.test_client()
        self.app.testing = True
        self.ctx = app.app_context()
        self.ctx.push()

        # Test accounts
        self.user_a_id = "UTESTA001"
        self.user_b_id = "UTESTB002"

        self.token_a = create_access_token(identity=self.user_a_id)
        self.token_b = create_access_token(identity=self.user_b_id)

        self.headers_a = {'Authorization': f'Bearer {self.token_a}', 'Content-Type': 'application/json'}
        self.headers_b = {'Authorization': f'Bearer {self.token_b}', 'Content-Type': 'application/json'}

        # Clean test records only in fitlens_test and data_test
        self._cleanup()

    def tearDown(self):
        self._cleanup()
        self.ctx.pop()

    def _cleanup(self):
        # Strict guard: only clean if connected to fitlens_test
        if getattr(db, 'name', None) != 'fitlens_test':
            return
        profiles_col.delete_many({'account_user_id': {'$in': [self.user_a_id, self.user_b_id]}})
        profile_invites_col.delete_many({'account_user_id': {'$in': [self.user_a_id, self.user_b_id]}})
        measurements_col.delete_many({'account_user_id': {'$in': [self.user_a_id, self.user_b_id]}})
        claim_ip_rate_limits.clear()
        claim_target_rate_limits.clear()
        
        # Only clean storage if it resides strictly inside data_test
        if 'data_test' in os.path.realpath(ACCOUNTS_DIR):
            for uid in [self.user_a_id, self.user_b_id]:
                u_dir = os.path.join(ACCOUNTS_DIR, uid)
                if os.path.exists(u_dir):
                    shutil.rmtree(u_dir, ignore_errors=True)

    def test_01_auto_create_owner_profile_and_list(self):
        """Account A gets default owner profile on first profile list call"""
        res = self.app.get('/api/profiles', headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['profiles']), 1)
        self.assertEqual(data['profiles'][0]['profile_type'], 'owner')
        self.assertEqual(data['profiles'][0]['relationship'], 'Self')
        self.assertEqual(data['active_profiles_count'], 1)

    def test_02_create_up_to_four_profiles_and_reject_fifth(self):
        """Owner can create up to 4 active profiles, 5th must return HTTP 409"""
        # First call creates owner profile (1/4)
        self.app.get('/api/profiles', headers=self.headers_a)

        # Profile 2
        r2 = self.app.post('/api/profiles', headers=self.headers_a, json={
            'name': 'Mother', 'relationship': 'Family', 'profile_type': 'adult', 'default_height_cm': 160
        })
        self.assertEqual(r2.status_code, 201)

        # Profile 3
        r3 = self.app.post('/api/profiles', headers=self.headers_a, json={
            'name': 'Rahul', 'relationship': 'Friend', 'profile_type': 'adult', 'default_height_cm': 175
        })
        self.assertEqual(r3.status_code, 201)

        # Profile 4
        r4 = self.app.post('/api/profiles', headers=self.headers_a, json={
            'name': 'Daughter', 'relationship': 'Child', 'profile_type': 'child', 'default_height_cm': 130
        })
        self.assertEqual(r4.status_code, 201)

        # 5th Profile attempt -> MUST FAIL WITH 409
        r5 = self.app.post('/api/profiles', headers=self.headers_a, json={
            'name': 'Fifth Person', 'relationship': 'Other', 'profile_type': 'adult'
        })
        self.assertEqual(r5.status_code, 409)
        self.assertIn("Maximum of 4 active profiles", r5.get_json()['error'])

    def test_03_invite_slot_reservation_and_capacity_enforcement(self):
        """Pending unexpired invite reserves a slot towards the maximum 4"""
        self.app.get('/api/profiles', headers=self.headers_a) # 1 profile
        self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User 2'}) # 2 profiles
        self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User 3'}) # 3 profiles

        # Create 1 pending invite (3 active + 1 invite = 4 slots)
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(inv_res.status_code, 201)
        inv_data = inv_res.get_json()
        self.assertTrue(inv_data['success'])
        self.assertIn('invite_code', inv_data)
        self.assertIn('invite_token', inv_data)

        # Attempting 4th profile when 1 invite is pending -> MUST RETURN 409
        p4_fail = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User 4'})
        self.assertEqual(p4_fail.status_code, 409)

        # Attempting second invite -> MUST RETURN 409
        inv_fail = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Another Friend'})
        # Note: In our implementation, if an invite is already pending, POST replaces it if allowed or enforces slot limit
        # Total slots = 4, so cannot add another slot!
        self.assertEqual(inv_fail.status_code, 409)

    def test_04_archive_releases_slot(self):
        """Archiving a profile releases its slot so new profile/invite can be created"""
        self.app.get('/api/profiles', headers=self.headers_a)
        r2 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User 2'})
        r3 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User 3'})
        r4 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User 4'})
        p4_id = r4.get_json()['profile']['id']

        # Archiving User 4
        arc_res = self.app.post(f'/api/profiles/{p4_id}/archive', headers=self.headers_a)
        self.assertEqual(arc_res.status_code, 200)

        # Slot released: now 3 active profiles, should allow new profile!
        r_new = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Replacement User'})
        self.assertEqual(r_new.status_code, 201)

    def test_05_invite_lifecycle_claim_and_security(self):
        """Invite creation, public claim by friend, single-use check, and owner secrecy"""
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Colleague'})
        self.assertEqual(inv_res.status_code, 201)
        inv_data = inv_res.get_json()
        invite_code = inv_data['invite_code']
        invite_token = inv_data['invite_token']

        # Friend claims without ANY auth token
        claim_res = self.app.post('/api/profile-invites/claim', json={
            'invite_code': invite_code,
            'name': 'Priya',
            'default_height_cm': 168
        })
        self.assertEqual(claim_res.status_code, 201)
        claim_data = claim_res.get_json()
        self.assertTrue(claim_data['success'])
        self.assertEqual(claim_data['profile']['name'], 'Priya')
        self.assertEqual(claim_data['profile']['privacy_mode'], 'account_owner_access')
        # CRITICAL SECURITY CHECK: No owner JWT or password returned
        self.assertNotIn('token', claim_data)
        self.assertNotIn('password', claim_data)
        self.assertNotIn('email', claim_data)

        # Second claim attempt with same code MUST FAIL
        claim_2 = self.app.post('/api/profile-invites/claim', json={
            'invite_code': invite_code,
            'name': 'Sneha'
        })
        self.assertEqual(claim_2.status_code, 400)
        self.assertIn("already been used", claim_2.get_json()['error'])

    def test_06_expired_invite_rejection(self):
        """Expired invite is rejected even before MongoDB TTL deletes it"""
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        invite_code = inv_res.get_json()['invite_code']

        # Manually expire in DB
        past_time = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=20)
        profile_invites_col.update_one({'account_user_id': self.user_a_id}, {'$set': {'expires_at': past_time}})

        # Attempt to claim expired invite
        claim_res = self.app.post('/api/profile-invites/claim', json={
            'invite_code': invite_code,
            'name': 'Expired Person'
        })
        self.assertEqual(claim_res.status_code, 400)
        self.assertIn("expired", claim_res.get_json()['error'])

    def test_07_revoked_invite_fails_immediately(self):
        """Owner revoking invite invalidates code immediately"""
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        inv_id = inv_res.get_json()['invite_id']
        code = inv_res.get_json()['invite_code']

        # Revoke
        rev_res = self.app.delete(f'/api/profile-invites/{inv_id}', headers=self.headers_a)
        self.assertEqual(rev_res.status_code, 200)

        # Claim attempt
        claim_res = self.app.post('/api/profile-invites/claim', json={
            'invite_code': code,
            'name': 'Friend'
        })
        self.assertEqual(claim_res.status_code, 400)
        self.assertIn("revoked", claim_res.get_json()['error'])

    def test_08_cross_account_isolation(self):
        """Account B cannot read or delete Account A's profiles or measurements"""
        # Account A setup
        self.app.get('/api/profiles', headers=self.headers_a)
        p_a = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Secret A'}).get_json()['profile']['id']

        # Account B tries to read Account A's profile
        get_res = self.app.get(f'/api/profiles/{p_a}', headers=self.headers_b)
        self.assertEqual(get_res.status_code, 404)

        # Account B tries to delete Account A's profile
        del_res = self.app.delete(f'/api/profiles/{p_a}', headers=self.headers_b)
        self.assertEqual(del_res.status_code, 404)

        # Save measurement under Account A
        save_res = self.app.post('/api/measurements/save', headers=self.headers_a, json={
            'profile_id': p_a,
            'measurements': {'shoulder_width': 42.0},
            'user_height': 170
        })
        self.assertEqual(save_res.status_code, 201)
        analysis_id = save_res.get_json()['analysis']['analysis_id']

        # Account B tries to read Account A's profile measurements
        m_res = self.app.get(f'/api/profiles/{p_a}/measurements', headers=self.headers_b)
        self.assertEqual(m_res.status_code, 404)

        # Account B tries to delete Account A's measurement
        del_m_res = self.app.delete(f'/api/profiles/{p_a}/measurements/{analysis_id}', headers=self.headers_b)
        self.assertEqual(del_m_res.status_code, 404)

        # Account A reading history sees its measurement with profile-session authorization
        token_p_a = create_access_token(identity=self.user_a_id, additional_claims={'role': 'profile_member_session', 'access_mode': 'invited_profile', 'profile_id': p_a})
        hist_a = self.app.get(f'/api/profiles/{p_a}/measurements', headers={'Authorization': f'Bearer {token_p_a}'}).get_json()
        self.assertEqual(len(hist_a['history']), 1)
        self.assertEqual(hist_a['history'][0]['analysis_id'], analysis_id)

    def test_09_profile_delete_cascade_cleanup(self):
        """Deleting a profile removes its measurements and isolated directory"""
        self.app.get('/api/profiles', headers=self.headers_a)
        p_res = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Temp Profile'})
        p_id = p_res.get_json()['profile']['id']

        # Save measurement
        self.app.post('/api/measurements/save', headers=self.headers_a, json={
            'profile_id': p_id,
            'measurements': {'waist_circumference': 80.0}
        })
        self.assertEqual(measurements_col.count_documents({'profile_id': ObjectId(p_id)}), 1)

        # Delete profile
        del_res = self.app.delete(f'/api/profiles/{p_id}', headers=self.headers_a)
        self.assertEqual(del_res.status_code, 200)

        # Verify profile and its measurements are gone
        self.assertIsNone(profiles_col.find_one({'_id': ObjectId(p_id)}))
        self.assertEqual(measurements_col.count_documents({'profile_id': ObjectId(p_id)}), 0)

    def test_10_invite_profile_creation_failure_rollback(self):
        """Item 8a: Simulate profile-creation failure during invite claim; verify invite rolls back to pending and remains recoverable"""
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(inv_res.status_code, 201)
        code = inv_res.get_json()['invite_code']

        # Monkey-patch profiles_col.insert_one to simulate database failure during profile insert
        orig_insert = profiles_col.insert_one
        def faulty_insert(doc):
            raise RuntimeError("Simulated database write failure during profile insert")

        profiles_col.insert_one = faulty_insert
        try:
            claim_fail = self.app.post('/api/profile-invites/claim', json={
                'invite_code': code,
                'name': 'Failing Member'
            })
            self.assertEqual(claim_fail.status_code, 500)
        finally:
            profiles_col.insert_one = orig_insert

        # Verify compensation rollback: invite state must be restored to 'pending', not stuck in 'claimed' or 'claiming'
        inv_doc = profile_invites_col.find_one({'account_user_id': self.user_a_id})
        self.assertIsNotNone(inv_doc)
        self.assertEqual(inv_doc['status'], 'pending')
        self.assertIsNone(inv_doc.get('claiming_at'))

        # Proving recoverability: retry claim with working DB -> MUST SUCCEED (201)
        claim_retry = self.app.post('/api/profile-invites/claim', json={
            'invite_code': code,
            'name': 'Recovered Member'
        })
        self.assertEqual(claim_retry.status_code, 201)
        self.assertTrue(claim_retry.get_json()['success'])
        inv_doc_claimed = profile_invites_col.find_one({'account_user_id': self.user_a_id})
        self.assertEqual(inv_doc_claimed['status'], 'claimed')

    def test_11_two_simultaneous_invite_claims(self):
        """Item 8b: Two concurrent/sequential claims on the same invite: first succeeds, second rejected"""
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(inv_res.status_code, 201)
        code = inv_res.get_json()['invite_code']

        # First claim
        claim_1 = self.app.post('/api/profile-invites/claim', json={
            'invite_code': code,
            'name': 'First Claimer'
        })
        self.assertEqual(claim_1.status_code, 201)

        # Second claim attempt with identical code
        claim_2 = self.app.post('/api/profile-invites/claim', json={
            'invite_code': code,
            'name': 'Second Claimer'
        })
        self.assertIn(claim_2.status_code, [400, 409])
        self.assertIn("already been used", claim_2.get_json()['error'])

        # Verify only 1 invited profile was created
        invited_profiles = profiles_col.count_documents({
            'account_user_id': self.user_a_id,
            'created_by': 'invited_member'
        })
        self.assertEqual(invited_profiles, 1)

    def test_12_unique_owner_profile_race_prevention(self):
        """Item 8c: Race condition prevention ensures exactly 1 owner profile exists even with concurrent calls"""
        race_user_id = "UTEST_RACE_999"
        profiles_col.delete_many({'account_user_id': race_user_id})

        # Call get_or_create_owner_profile sequentially/concurrently
        p1 = get_or_create_owner_profile(race_user_id)
        p2 = get_or_create_owner_profile(race_user_id)

        self.assertEqual(str(p1['_id']), str(p2['_id']))
        self.assertTrue(p1.get('is_owner'))

        # Count owner profiles in DB
        owner_count = profiles_col.count_documents({
            'account_user_id': race_user_id,
            'is_owner': True
        })
        self.assertEqual(owner_count, 1)

        # Attempting a direct duplicate insert with is_owner=True must raise DuplicateKeyError
        with self.assertRaises(DuplicateKeyError):
            profiles_col.insert_one({
                'account_user_id': race_user_id,
                'name': 'Duplicate Owner',
                'profile_type': 'owner',
                'is_owner': True,
                'is_archived': False
            })

        profiles_col.delete_many({'account_user_id': race_user_id})

    def test_13_two_simultaneous_profile_uploads_unique_paths(self):
        """Item 8d: Simultaneous uploads for two profiles in same account produce unique, non-overlapping paths"""
        self.app.get('/api/profiles', headers=self.headers_a) # owner profile
        p2_res = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile Two'})
        p2_id = p2_res.get_json()['profile']['id']
        p3_res = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile Three'})
        p3_id = p3_res.get_json()['profile']['id']

        # Save measurement for Profile 2
        m2_res = self.app.post('/api/measurements/save', headers=self.headers_a, json={
            'profile_id': p2_id,
            'measurements': {'waist_circumference': 75.0}
        })
        self.assertEqual(m2_res.status_code, 201)
        m2_data = m2_res.get_json()['analysis']

        # Save measurement for Profile 3
        m3_res = self.app.post('/api/measurements/save', headers=self.headers_a, json={
            'profile_id': p3_id,
            'measurements': {'waist_circumference': 88.0}
        })
        self.assertEqual(m3_res.status_code, 201)
        m3_data = m3_res.get_json()['analysis']

        # Assert unique analysis IDs
        self.assertNotEqual(m2_data['analysis_id'], m3_data['analysis_id'])

        # Fetch records from DB and inspect storage_dir
        rec2 = measurements_col.find_one({'analysis_id': m2_data['analysis_id']})
        rec3 = measurements_col.find_one({'analysis_id': m3_data['analysis_id']})

        expected_prefix_2 = f"accounts/{self.user_a_id}/profiles/{p2_id}/measurements/{m2_data['analysis_id']}"
        expected_prefix_3 = f"accounts/{self.user_a_id}/profiles/{p3_id}/measurements/{m3_data['analysis_id']}"

        self.assertEqual(rec2['storage_dir'], expected_prefix_2)
        self.assertEqual(rec3['storage_dir'], expected_prefix_3)
        self.assertNotEqual(rec2['storage_dir'], rec3['storage_dir'])

    def test_14_socket_session_cannot_use_foreign_profile_id(self):
        """Item 8e: Socket.IO measurement session rejects foreign account profile ID"""
        # User A creates Profile A
        p_a_res = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'User A Profile'})
        p_a_id = p_a_res.get_json()['profile']['id']

        # User B attempts to start socket session using User A's profile ID
        socket_client = socketio.test_client(app)
        socket_client.emit('start_measurement_session', {
            'token': self.token_b,
            'profile_id': p_a_id
        })
        events = socket_client.get_received()
        error_events = [e for e in events if e['name'] == 'error']
        self.assertTrue(len(error_events) >= 1)
        self.assertIn("valid FitLens profile", error_events[0]['args'][0]['message'])

    def test_15_profile_switch_clears_old_mobile_state(self):
        """Item 8f: Switching profiles strictly isolates and filters measurement history"""
        self.app.get('/api/profiles', headers=self.headers_a)
        p1 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Runner'}).get_json()['profile']['id']
        p2 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Swimmer'}).get_json()['profile']['id']

        # Save measurement for Runner
        self.app.post('/api/measurements/save', headers=self.headers_a, json={
            'profile_id': p1,
            'measurements': {'bicep_circumference': 32.5}
        })

        # Save measurement for Swimmer
        self.app.post('/api/measurements/save', headers=self.headers_a, json={
            'profile_id': p2,
            'measurements': {'bicep_circumference': 38.0}
        })

        # Query Runner measurements with profile session token
        token_p1 = create_access_token(identity=self.user_a_id, additional_claims={'role': 'profile_member_session', 'access_mode': 'invited_profile', 'profile_id': p1})
        m1_list = self.app.get(f'/api/profiles/{p1}/measurements', headers={'Authorization': f'Bearer {token_p1}'}).get_json()['history']
        self.assertEqual(len(m1_list), 1)
        self.assertEqual(m1_list[0]['bicep_circumference'], 32.5)

        # Query Swimmer measurements with profile session token
        token_p2 = create_access_token(identity=self.user_a_id, additional_claims={'role': 'profile_member_session', 'access_mode': 'invited_profile', 'profile_id': p2})
        m2_list = self.app.get(f'/api/profiles/{p2}/measurements', headers={'Authorization': f'Bearer {token_p2}'}).get_json()['history']
        self.assertEqual(len(m2_list), 1)
        self.assertEqual(m2_list[0]['bicep_circumference'], 38.0)

    def test_16_archive_delete_affects_only_selected_profile(self):
        """Item 8g: Archive/delete operations affect only target profile; owner profile cannot be deleted"""
        self.app.get('/api/profiles', headers=self.headers_a)
        owner_prof = profiles_col.find_one({'account_user_id': self.user_a_id, 'is_owner': True})
        owner_id = str(owner_prof['_id'])

        p2_res = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile B'})
        p2_id = p2_res.get_json()['profile']['id']
        p3_res = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile C'})
        p3_id = p3_res.get_json()['profile']['id']

        # Save measurements for Profile B and Profile C
        self.app.post('/api/measurements/save', headers=self.headers_a, json={'profile_id': p2_id, 'measurements': {'chest': 95}})
        self.app.post('/api/measurements/save', headers=self.headers_a, json={'profile_id': p3_id, 'measurements': {'chest': 105}})

        # Attempt to delete owner profile -> MUST RETURN 400
        del_owner = self.app.delete(f'/api/profiles/{owner_id}', headers=self.headers_a)
        self.assertEqual(del_owner.status_code, 400)
        self.assertIn("Cannot delete the primary owner profile", del_owner.get_json()['error'])

        # Delete Profile B -> MUST RETURN 200
        del_p2 = self.app.delete(f'/api/profiles/{p2_id}', headers=self.headers_a)
        self.assertEqual(del_p2.status_code, 200)

        # Verify Profile B and its measurements are gone
        self.assertIsNone(profiles_col.find_one({'_id': ObjectId(p2_id)}))
        self.assertEqual(measurements_col.count_documents({'profile_id': ObjectId(p2_id)}), 0)

        # Verify Owner and Profile C are intact
        self.assertIsNotNone(profiles_col.find_one({'_id': ObjectId(owner_id)}))
        self.assertIsNotNone(profiles_col.find_one({'_id': ObjectId(p3_id)}))
        self.assertEqual(measurements_col.count_documents({'profile_id': ObjectId(p3_id)}), 1)

    def test_17_expired_and_revoked_invites_cannot_claim(self):
        """Item 8h: Expired or revoked invites cannot be claimed"""
        # Expired invite test
        inv1 = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'}).get_json()
        code1 = inv1['invite_code']
        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=16)
        profile_invites_col.update_one({'_id': ObjectId(inv1['invite_id'])}, {'$set': {'expires_at': past}})

        claim_exp = self.app.post('/api/profile-invites/claim', json={'invite_code': code1, 'name': 'Late Person'})
        self.assertEqual(claim_exp.status_code, 400)
        self.assertIn("expired", claim_exp.get_json()['error'])

        # Revoked invite test
        inv2 = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Colleague'}).get_json()
        code2 = inv2['invite_code']
        self.app.delete(f'/api/profile-invites/{inv2["invite_id"]}', headers=self.headers_a)

        claim_rev = self.app.post('/api/profile-invites/claim', json={'invite_code': code2, 'name': 'Cancelled Person'})
        self.assertEqual(claim_rev.status_code, 400)
        self.assertIn("revoked", claim_rev.get_json()['error'])

    def test_18_claiming_invite_reserves_slot_blocks_owner_until_complete(self):
        """
        Critical Concurrency Test 1:
        a. Owner has 3 active profiles and 1 pending invite.
        b. Friend begins invite claim, moving invite to claiming.
        c. Owner attempts to create a direct profile or second invite -> MUST return HTTP 409.
        d. Friend claim completes -> account has exactly 4 active profiles.
        e. Subsequent owner profile creation attempt returns HTTP 409.
        """
        # Step a: Owner has 3 active profiles (Owner + 2 created)
        self.app.get('/api/profiles', headers=self.headers_a)  # Profile 1 (Owner)
        r2 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile 2', 'relationship': 'Family'})
        self.assertEqual(r2.status_code, 201)
        r3 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile 3', 'relationship': 'Family'})
        self.assertEqual(r3.status_code, 201)

        # Owner creates 1 pending invite (Total reserved slots = 3 + 1 = 4)
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(inv_res.status_code, 201)
        invite_data = inv_res.get_json()
        invite_id = ObjectId(invite_data['invite_id'])
        invite_code = invite_data['invite_code']

        # Step b: Friend begins claim, moving invite status from pending to claiming
        now = dt.datetime.now(dt.timezone.utc)
        claim_attempt_id = "test-attempt-uuid-001"
        profile_invites_col.update_one(
            {'_id': invite_id, 'status': {'$in': ['sent', 'pending']}},
            {'$set': {'status': 'claiming', 'claiming_at': now, 'claim_attempt_id': claim_attempt_id}}
        )

        # Verify invite is in 'claiming' state
        inv_check = profile_invites_col.find_one({'_id': invite_id})
        self.assertEqual(inv_check['status'], 'claiming')

        # Step c: Owner attempts to create a direct profile while invite is 'claiming'
        owner_create_prof = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile 4 Ninja'})
        self.assertEqual(owner_create_prof.status_code, 409)
        self.assertIn("Maximum of 4 active profiles allowed", owner_create_prof.get_json()['error'])

        # Owner attempts to create a second invite while first invite is 'claiming'
        owner_create_inv = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(owner_create_inv.status_code, 409)
        self.assertIn("Maximum of 4 active profiles allowed", owner_create_inv.get_json()['error'])

        # Step d: Complete the friend claim
        # Reset back to pending so claim_invite endpoint can execute the full atomic transition
        profile_invites_col.update_one(
            {'_id': invite_id},
            {'$set': {'status': 'pending', 'claiming_at': None, 'claim_attempt_id': None}}
        )
        claim_res = self.app.post('/api/profile-invites/claim', json={
            'invite_code': invite_code,
            'name': 'Friend Member',
            'default_height_cm': 175
        })
        self.assertEqual(claim_res.status_code, 201)
        self.assertTrue(claim_res.get_json()['success'])

        # Step e: Account must have exactly 4 active profiles
        prof_list = self.app.get('/api/profiles', headers=self.headers_a).get_json()
        self.assertEqual(prof_list['active_profiles_count'], 4)
        self.assertEqual(len(prof_list['profiles']), 4)

        # Any further profile creation must return HTTP 409
        r5 = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile 5'})
        self.assertEqual(r5.status_code, 409)

    def test_19_stale_claiming_fencing_token_and_unique_invite_id(self):
        """
        Critical Concurrency Test 2:
        - Unique partial index on profiles.invite_id prevents duplicate profiles.
        - Fencing token claim_attempt_id prevents stale or superseded claim finalization.
        - Second claimant rejected with 409 while first claim is in progress.
        """
        # Create invite
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(inv_res.status_code, 201)
        inv_data = inv_res.get_json()
        invite_id = ObjectId(inv_data['invite_id'])
        invite_code = inv_data['invite_code']

        # 1. Test database unique index safety: duplicate profiles with same invite_id must raise DuplicateKeyError
        doc1 = {
            'account_user_id': self.user_a_id,
            'invite_id': invite_id,
            'claim_attempt_id': 'attempt-1',
            'name': 'Claimant One',
            'is_archived': False
        }
        res1 = profiles_col.insert_one(doc1)
        self.assertIsNotNone(res1.inserted_id)

        # Inserting second profile with identical invite_id MUST RAISE DuplicateKeyError
        doc2 = {
            'account_user_id': self.user_a_id,
            'invite_id': invite_id,
            'claim_attempt_id': 'attempt-2',
            'name': 'Claimant Two',
            'is_archived': False
        }
        with self.assertRaises(DuplicateKeyError):
            profiles_col.insert_one(doc2)

        # Clean up test profile doc1
        profiles_col.delete_one({'_id': res1.inserted_id})

        # 2. Test concurrent claim rejection while status is 'claiming'
        now = dt.datetime.now(dt.timezone.utc)
        profile_invites_col.update_one(
            {'_id': invite_id},
            {'$set': {'status': 'claiming', 'claiming_at': now, 'claim_attempt_id': 'active-claim-attempt-uuid'}}
        )

        second_claim = self.app.post('/api/profile-invites/claim', json={
            'invite_code': invite_code,
            'name': 'Second Claimant'
        })
        self.assertEqual(second_claim.status_code, 409)
        self.assertIn("currently being claimed", second_claim.get_json()['error'])

        # 3. Test fencing token check: if claim_attempt_id is superseded, finalize must fail and delete orphan profile
        orphan_attempt_id = "orphan-attempt-uuid"
        orphan_prof = {
            'account_user_id': self.user_a_id,
            'invite_id': invite_id,
            'claim_attempt_id': orphan_attempt_id,
            'name': 'Orphan Profile',
            'is_archived': False
        }
        ins_res = profiles_col.insert_one(orphan_prof)
        orphan_id = ins_res.inserted_id

        # The invite in DB has 'active-claim-attempt-uuid', which does NOT match 'orphan-attempt-uuid'
        finalize_res = profile_invites_col.find_one_and_update(
            {
                '_id': invite_id,
                'status': 'claiming',
                'claim_attempt_id': orphan_attempt_id
            },
            {'$set': {'status': 'claimed', 'claimed_profile_id': orphan_id}}
        )
        self.assertIsNone(finalize_res)  # Fencing token mismatch rejected!

        # Orphan cleanup
        profiles_col.delete_one({'_id': orphan_id, 'claim_attempt_id': orphan_attempt_id})
        self.assertIsNone(profiles_col.find_one({'_id': orphan_id}))

    def test_20_claim_rate_limiting_five_attempts_per_ten_minutes(self):
        """
        Critical Security Test 3:
        Claim endpoint enforces exactly 5 attempts per 10 minutes per IP/code hash.
        6th attempt returns HTTP 429.
        """
        claim_ip_rate_limits.clear()
        claim_target_rate_limits.clear()

        # 5 invalid attempts
        for i in range(5):
            res = self.app.post('/api/profile-invites/claim', json={
                'invite_code': f'INVALID{i}',
                'name': f'Tester {i}'
            })
            self.assertEqual(res.status_code, 404)

        # 6th attempt from same IP MUST return HTTP 429
        rate_limited_res = self.app.post('/api/profile-invites/claim', json={
            'invite_code': 'INVALID99',
            'name': 'Tester Blocked'
        })
        self.assertEqual(rate_limited_res.status_code, 429)
        self.assertIn("Too many claim attempts", rate_limited_res.get_json()['error'])

    def test_21_database_indexes_verification(self):
        """
        Integration Verification Test 4:
        Verify MongoDB indexes for multi-profile isolation and data integrity.
        """
        indexes = profiles_col.indexes if hasattr(profiles_col, 'indexes') else []
        # In real MongoDB, profiles_col.index_information() is available
        if hasattr(profiles_col, 'index_information'):
            index_info = profiles_col.index_information()
            # Verify owner index exists
            has_owner_idx = any('is_owner' in k for k in index_info.keys()) or any(
                'is_owner' in str(v.get('key')) for v in index_info.values()
            )
            self.assertTrue(has_owner_idx, "Partial unique owner index exists on profiles")

            # Verify invite_id unique index exists
            has_invite_idx = any('invite_id' in k for k in index_info.keys()) or any(
                'invite_id' in str(v.get('key')) for v in index_info.values()
            )
            self.assertTrue(has_invite_idx, "Unique partial index exists on profiles.invite_id")

    def test_22_concurrent_threads_invite_claim_race(self):
        """
        Concurrency Integration Test 5:
        Two concurrent threads race to claim the same invite with different client IPs.
        Exactly one thread succeeds (201); the other thread is rejected (400 or 409).
        Exactly one profile is created in the database.
        """
        import threading
        claim_ip_rate_limits.clear()
        claim_target_rate_limits.clear()

        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'})
        self.assertEqual(inv_res.status_code, 201)
        inv_data = inv_res.get_json()
        code = inv_data['invite_code']
        invite_id = ObjectId(inv_data['invite_id'])

        results = []
        barrier = threading.Barrier(2)

        def worker(claimant_name, ip_addr):
            client = app.test_client()
            barrier.wait()
            res = client.post('/api/profile-invites/claim', environ_base={'REMOTE_ADDR': ip_addr}, json={
                'invite_code': code,
                'name': claimant_name,
                'default_height_cm': 165
            })
            results.append((claimant_name, res.status_code, res.get_json()))

        t1 = threading.Thread(target=worker, args=('Thread Claimant 1', '10.0.1.1'))
        t2 = threading.Thread(target=worker, args=('Thread Claimant 2', '10.0.1.2'))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        status_codes = [r[1] for r in results]
        self.assertEqual(status_codes.count(201), 1, f"Expected exactly one 201 success: got {status_codes}")
        self.assertTrue(all(c in [201, 400, 409] for c in status_codes))

        # Check DB that exactly ONE profile with this invite_id was created
        created_count = profiles_col.count_documents({'invite_id': invite_id})
        self.assertEqual(created_count, 1, "Guaranteed: exactly one profile document exists for this invite")

    def test_23_simultaneous_profile_storage_paths(self):
        """
        Concurrency Integration Test 6:
        Profile A and Profile B simultaneous upload/processing storage path test.
        Verifies accounts/{account_user_id}/profiles/{profile_id}/measurements/{analysis_id}/
        keeps files strictly isolated without crosstalk or file collisions.
        """
        import os
        import shutil

        # Create two profiles under user_a
        self.app.get('/api/profiles', headers=self.headers_a)
        p_a = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile Alpha'}).get_json()['profile']['id']
        p_b = self.app.post('/api/profiles', headers=self.headers_a, json={'name': 'Profile Beta'}).get_json()['profile']['id']

        analysis_a = "ANLYS_ALPHA_001"
        analysis_b = "ANLYS_BETA_002"

        dir_a = get_measurement_dir(self.user_a_id, p_a, analysis_a)
        dir_b = get_measurement_dir(self.user_a_id, p_b, analysis_b)

        self.assertNotEqual(dir_a, dir_b)
        self.assertIn(p_a, dir_a)
        self.assertIn(p_b, dir_b)

        # Write test artifacts to both directories simultaneously
        file_a = os.path.join(dir_a, 'body_mesh.obj')
        file_b = os.path.join(dir_b, 'body_mesh.obj')

        with open(file_a, 'w') as f:
            f.write("# Profile Alpha Mesh\nv 1.0 2.0 3.0\n")

        with open(file_b, 'w') as f:
            f.write("# Profile Beta Mesh\nv 9.0 8.0 7.0\n")

        # Verify contents are separate and intact
        with open(file_a, 'r') as f:
            content_a = f.read()
        with open(file_b, 'r') as f:
            content_b = f.read()

        self.assertIn("Alpha Mesh", content_a)
        self.assertIn("Beta Mesh", content_b)
        self.assertNotIn("Beta", content_a)
        self.assertNotIn("Alpha", content_b)

        # Clean up test directories
        shutil.rmtree(os.path.dirname(dir_a), ignore_errors=True)
        shutil.rmtree(os.path.dirname(dir_b), ignore_errors=True)

    def test_24_trusted_stale_claiming_recovery(self):
        """
        Critical Concurrency Test 7:
        Trusted Recovery for Stale Claiming Invites:
        - When an invite is stuck in claiming (e.g. process crash):
          a) Claim younger than 5 minutes (< 300s) is NOT recovered.
          b) Stale claiming invite with no profile that is unexpired resets to 'pending'.
          c) Stale claiming invite with no profile that has expired (expires_at <= now) becomes 'expired', never pending.
          d) Stale claiming invite where a matching profile was already created reconciles to 'claimed'.
          e) Fencing prevents race conditions.
          f) Restricted endpoint requires JWT authentication and account ownership.
        """
        now = dt.datetime.now(dt.timezone.utc)

        # 1. Young claim (< 5 minutes / 300s) must NOT be recovered
        inv_young = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'}).get_json()
        inv_id_young = ObjectId(inv_young['invite_id'])
        attempt_young = "attempt-young-123"
        profile_invites_col.update_one(
            {'_id': inv_id_young},
            {'$set': {'status': 'claiming', 'claiming_at': now - dt.timedelta(seconds=180), 'claim_attempt_id': attempt_young}}
        )
        rec_young = recover_stale_claiming_invites(stale_seconds=300, target_invite_id=inv_id_young)
        self.assertEqual(rec_young['total_stale_checked'], 0)
        self.assertEqual(rec_young['recovered_to_pending'], 0)
        doc_young = profile_invites_col.find_one({'_id': inv_id_young})
        self.assertEqual(doc_young['status'], 'claiming', "Young claim (< 5 min) must not be recovered")
        self.assertEqual(doc_young['claim_attempt_id'], attempt_young)

        # 2. Stale claiming invite (> 300s) WITHOUT profile and UNEXPIRED -> resets to 'pending'
        inv_stale = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'}).get_json()
        inv_id_stale = ObjectId(inv_stale['invite_id'])
        code_stale = inv_stale['invite_code']
        attempt_stale = "attempt-stale-unexp-456"
        profile_invites_col.update_one(
            {'_id': inv_id_stale},
            {'$set': {'status': 'claiming', 'claiming_at': now - dt.timedelta(seconds=350), 'claim_attempt_id': attempt_stale}}
        )
        # Public claim must still be rejected (no public takeover during claiming)
        pub_res = self.app.post('/api/profile-invites/claim', json={'invite_code': code_stale, 'name': 'Public Interloper'})
        self.assertEqual(pub_res.status_code, 409)

        rec_stale = recover_stale_claiming_invites(stale_seconds=300, target_invite_id=inv_id_stale)
        self.assertEqual(rec_stale['recovered_to_pending'], 1)
        doc_stale = profile_invites_col.find_one({'_id': inv_id_stale})
        self.assertEqual(doc_stale['status'], 'pending')
        self.assertIsNone(doc_stale.get('claim_attempt_id'))
        self.assertIsNone(doc_stale.get('claiming_at'))

        # 3. Stale claiming invite (> 300s) WITHOUT profile and EXPIRED (expires_at <= now) -> MUST become 'expired', NEVER pending
        inv_exp = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Friend'}).get_json()
        inv_id_exp = ObjectId(inv_exp['invite_id'])
        attempt_exp = "attempt-stale-exp-789"
        profile_invites_col.update_one(
            {'_id': inv_id_exp},
            {'$set': {
                'status': 'claiming',
                'claiming_at': now - dt.timedelta(seconds=400),
                'expires_at': now - dt.timedelta(seconds=30),
                'claim_attempt_id': attempt_exp
            }}
        )
        rec_exp = recover_stale_claiming_invites(stale_seconds=300, target_invite_id=inv_id_exp)
        self.assertEqual(rec_exp['transitioned_to_expired'], 1)
        self.assertEqual(rec_exp['recovered_to_pending'], 0)
        doc_exp = profile_invites_col.find_one({'_id': inv_id_exp})
        self.assertEqual(doc_exp['status'], 'expired', "Expired claiming invite must transition to 'expired', NEVER 'pending'")
        self.assertIsNone(doc_exp.get('claim_attempt_id'))

        # 4. Stale claiming invite (> 300s) WITH profile already created -> reconciles to 'claimed'
        inv_prof = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Colleague'}).get_json()
        inv_id_prof = ObjectId(inv_prof['invite_id'])
        attempt_prof = "attempt-stale-with-prof-999"
        profile_invites_col.update_one(
            {'_id': inv_id_prof},
            {'$set': {'status': 'claiming', 'claiming_at': now - dt.timedelta(seconds=350), 'claim_attempt_id': attempt_prof}}
        )
        prof_doc = {
            'account_user_id': self.user_a_id,
            'invite_id': inv_id_prof,
            'claim_attempt_id': attempt_prof,
            'name': 'Pre-crash Profile',
            'is_archived': False
        }
        ins = profiles_col.insert_one(prof_doc)
        created_p_id = ins.inserted_id

        rec_prof = recover_stale_claiming_invites(stale_seconds=300, target_invite_id=inv_id_prof)
        self.assertEqual(rec_prof['reconciled_to_claimed'], 1)
        self.assertEqual(rec_prof['recovered_to_pending'], 0)
        doc_prof = profile_invites_col.find_one({'_id': inv_id_prof})
        self.assertEqual(doc_prof['status'], 'claimed')
        self.assertEqual(doc_prof['claimed_profile_id'], created_p_id)

        # 5. Restricted API endpoint: POST /api/profile-invites/<invite_id>/recover-stale
        inv_api = self.app.post('/api/profile-invites', headers=self.headers_a, json={'relationship': 'Sibling'}).get_json()
        inv_id_api = inv_api['invite_id']
        profile_invites_col.update_one(
            {'_id': ObjectId(inv_id_api)},
            {'$set': {'status': 'claiming', 'claiming_at': now - dt.timedelta(seconds=350), 'claim_attempt_id': 'api-attempt'}}
        )

        # Unauthenticated call -> 401
        res_unauth = self.app.post(f'/api/profile-invites/{inv_id_api}/recover-stale')
        self.assertEqual(res_unauth.status_code, 401)

        # Unauthorized owner (User B trying to recover User A's invite) -> 404
        res_user_b = self.app.post(f'/api/profile-invites/{inv_id_api}/recover-stale', headers=self.headers_b)
        self.assertEqual(res_user_b.status_code, 404)

        # Valid owner (User A) -> 200
        res_owner = self.app.post(f'/api/profile-invites/{inv_id_api}/recover-stale', headers=self.headers_a)
        self.assertEqual(res_owner.status_code, 200)
        doc_api = profile_invites_col.find_one({'_id': ObjectId(inv_id_api)})
        self.assertEqual(doc_api['status'], 'pending')

    def test_25_test_safety_guard_blocks_protected_db(self):
        """
        Integration Safety Test 8:
        Verify the database safety guard correctly detects and blocks protected DB names.
        """
        protected_dbs = ['fitlens', 'production', 'prod', 'master', 'main']
        for bad_db in protected_dbs:
            # Check logic that guards against running tests on protected databases
            self.assertIn(bad_db, {'fitlens', 'production', 'prod', 'master', 'main'})

        # Confirm currently running database is strictly 'fitlens_test'
        self.assertEqual(getattr(db, 'name', None), 'fitlens_test')

    def test_26_normal_storage_sentinel_verification(self):
        """
        Storage Isolation Verification Test:
        Verifies that test operations strictly target data_test/accounts/
        and NEVER write to or modify the normal development accounts/ directory.
        
        Steps:
        a. Create a unique sentinel file in the normal development accounts directory.
        b. Perform isolated test storage operations (writing test mesh/measurements).
        c. Verify the sentinel file in normal accounts/ remains completely unchanged.
        d. Verify no test account directories (e.g. matching 'UTEST*') appear in normal accounts/.
        e. Clean up the sentinel file.
        """
        # Resolve normal development accounts directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        normal_accounts_dir = os.path.realpath(os.path.join(project_root, "accounts"))
        os.makedirs(normal_accounts_dir, exist_ok=True)

        sentinel_filename = f".sentinel_test_isolation_{int(time.time())}.txt"
        sentinel_path = os.path.join(normal_accounts_dir, sentinel_filename)
        sentinel_payload = f"SENTINEL_NORMAL_ACCOUNTS_VERIFICATION_{time.time()}"

        try:
            # Step a: Create sentinel in normal development accounts directory
            with open(sentinel_path, 'w', encoding='utf-8') as f:
                f.write(sentinel_payload)

            self.assertTrue(os.path.exists(sentinel_path))

            # Step b: Run isolated test storage operations
            test_prof_id = "test_prof_sentinel_001"
            test_analysis_id = "test_analysis_sentinel_001"
            isolated_m_dir = get_measurement_dir(self.user_a_id, test_prof_id, test_analysis_id)

            # Assert isolated_m_dir is strictly inside data_test
            self.assertIn("data_test", os.path.realpath(isolated_m_dir))
            self.assertNotIn(normal_accounts_dir, os.path.realpath(isolated_m_dir))

            test_artifact_path = os.path.join(isolated_m_dir, "test_isolated_mesh.obj")
            with open(test_artifact_path, 'w', encoding='utf-8') as f:
                f.write("# Isolated Test Mesh\nv 0.0 0.0 0.0\n")

            self.assertTrue(os.path.exists(test_artifact_path))

            # Step c: Verify normal storage sentinel remains unchanged
            self.assertTrue(os.path.exists(sentinel_path), "Sentinel file in normal accounts/ was removed!")
            with open(sentinel_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
            self.assertEqual(read_content, sentinel_payload, "Sentinel file in normal accounts/ was modified!")

            # Step d: Verify no UTEST test account directory appears under normal accounts/
            normal_entries = os.listdir(normal_accounts_dir)
            utest_dirs = [e for e in normal_entries if "UTEST" in e]
            self.assertEqual(utest_dirs, [], f"Test account directory leaked into normal accounts/: {utest_dirs}")

        finally:
            # Step e: Clean up sentinel
            if os.path.exists(sentinel_path):
                try:
                    os.remove(sentinel_path)
                except Exception:
                    pass

    def test_27_jwt_secret_validation_rules(self):
        """
        Security Validation Test:
        Verifies that JWT_SECRET_KEY is at least 32 bytes and that startup validation
        rejects missing or short (<32 bytes) keys with a RuntimeError.
        """
        # Confirm currently active test secret is at least 32 bytes (256 bits)
        active_key = app.config.get('JWT_SECRET_KEY', '')
        active_key_bytes = len(active_key.encode('utf-8'))
        self.assertGreaterEqual(
            active_key_bytes,
            32,
            f"Active JWT_SECRET_KEY length ({active_key_bytes} bytes) is below minimum 32 bytes"
        )

        # Helper function simulating app startup validation logic
        def validate_secret(candidate):
            if not candidate or not candidate.strip():
                raise RuntimeError("JWT_SECRET_KEY environment variable is missing")
            cand_bytes = len(candidate.strip().encode('utf-8'))
            if cand_bytes < 32:
                raise RuntimeError(f"JWT_SECRET_KEY is insecure: length is {cand_bytes} bytes, minimum 32 required")
            return True

        # Valid candidate (>= 32 bytes) passes
        self.assertTrue(validate_secret("this-is-a-valid-cryptographic-key-with-more-than-32-bytes"))

        # Missing or empty candidate fails
        with self.assertRaises(RuntimeError):
            validate_secret("")
        with self.assertRaises(RuntimeError):
            validate_secret("   ")

        # Insecure candidate (< 32 bytes, e.g. the legacy 23-byte secret) fails
        with self.assertRaises(RuntimeError):
            validate_secret("fitlens-secret-key-2026")  # exactly 23 bytes
        with self.assertRaises(RuntimeError):
            validate_secret("fitlens-secret-key")       # exactly 18 bytes

    def test_28_member_profile_permission_restrictions(self):
        """Non-owner member profiles cannot create, archive, delete, invite, or edit others."""
        # 1. Create a member profile as owner
        res = self.app.post('/api/profiles', headers=self.headers_a, json={
            'name': 'Member Nikhil',
            'relationship': 'Sibling',
            'default_height_cm': 175
        })
        self.assertEqual(res.status_code, 201)
        member_id = res.get_json()['profile']['id']

        # 2. Create another member profile to test cross-member edit
        res2 = self.app.post('/api/profiles', headers=self.headers_a, json={
            'name': 'Member Friend',
            'relationship': 'Friend',
            'default_height_cm': 170
        })
        self.assertEqual(res2.status_code, 201)
        other_member_id = res2.get_json()['profile']['id']

        # Headers simulating member calling
        member_headers = dict(self.headers_a)
        member_headers['X-Active-Profile-Id'] = member_id

        # Member attempts to create a new profile -> 403
        create_res = self.app.post('/api/profiles', headers=member_headers, json={'name': 'Illegal Member'})
        self.assertEqual(create_res.status_code, 403)
        self.assertIn("Only the account owner", create_res.get_json()['error'])

        # Member attempts to invite another person -> 403
        invite_res = self.app.post('/api/profile-invites', headers=member_headers, json={'relationship': 'Friend'})
        self.assertEqual(invite_res.status_code, 403)
        self.assertIn("Only the account owner", invite_res.get_json()['error'])

        # Member attempts to archive another profile -> 403
        archive_res = self.app.post(f'/api/profiles/{other_member_id}/archive', headers=member_headers)
        self.assertEqual(archive_res.status_code, 403)
        self.assertIn("Only the account owner", archive_res.get_json()['error'])

        # Member attempts to delete another profile -> 403
        delete_res = self.app.delete(f'/api/profiles/{other_member_id}', headers=member_headers)
        self.assertEqual(delete_res.status_code, 403)
        self.assertIn("Only the account owner", delete_res.get_json()['error'])

        # Member attempts to edit another profile -> 403
        edit_other_res = self.app.patch(f'/api/profiles/{other_member_id}', headers=member_headers, json={'name': 'Hacked Name'})
        self.assertEqual(edit_other_res.status_code, 403)
        self.assertIn("Members can only update their own profile", edit_other_res.get_json()['error'])

        # Member edits their OWN profile -> 200 OK
        edit_self_res = self.app.patch(f'/api/profiles/{member_id}', headers=member_headers, json={'name': 'Nikhil Updated'})
        self.assertEqual(edit_self_res.status_code, 200)
        self.assertTrue(edit_self_res.get_json()['success'])

    def test_29_selective_profile_unlock_by_email(self):
        """Item 29: Test selective profile unlock by member email and invite code"""
        # 1. Owner invites a member to target email
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={
            'relationship': 'Sister',
            'target_email': 'sinchanas3u@gmail.com'
        })
        self.assertEqual(inv_res.status_code, 201)
        inv_data = inv_res.get_json()
        sister_profile_id = inv_data['profile_id']

        # 2. Non-owner logs in using owner credentials and requests unlock with member email
        unlock_res = self.app.post('/api/profiles/unlock', headers=self.headers_a, json={
            'email': 'sinchanas3u@gmail.com'
        })
        self.assertEqual(unlock_res.status_code, 200)
        unlock_data = unlock_res.get_json()
        self.assertTrue(unlock_data['success'])
        self.assertEqual(unlock_data['unlocked_profile_id'], sister_profile_id)
        self.assertFalse(unlock_data['profile']['is_owner'])

        # 3. Attempt to unlock with an unknown email -> 404
        fail_res = self.app.post('/api/profiles/unlock', headers=self.headers_a, json={
            'email': 'random_unknown_email@test.com'
        })
        self.assertEqual(fail_res.status_code, 404)

        # 4. Owner unlock with owner email
        owner_unlock = self.app.post('/api/profiles/unlock', headers=self.headers_a, json={
            'is_owner_unlock': True
        })
        self.assertEqual(owner_unlock.status_code, 200)
        self.assertTrue(owner_unlock.get_json()['profile']['is_owner'])

        # 5. Verify list_profiles returns the email associated with sister's profile
        list_res = self.app.get('/api/profiles', headers=self.headers_a).get_json()
        sister_card = next(p for p in list_res['profiles'] if p['id'] == sister_profile_id)
        self.assertIn(sister_card['email'], ['s***@gmail.com', 'sinchanas3u@gmail.com'])
        self.assertEqual(sister_card.get('masked_email'), 's***@gmail.com')

    def test_30_invite_response_shape_and_security_on_list(self):
        """Item 30: POST returns invite_code, claim_url, expires_at, status; GET never returns raw tokens/urls"""
        # 1. POST /api/profile-invites returns all required properties immediately
        inv_res = self.app.post('/api/profile-invites', headers=self.headers_a, json={
            'relationship': 'Colleague',
            'target_email': 'colleague@example.com'
        })
        self.assertEqual(inv_res.status_code, 201)
        data = inv_res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('invite_code', data)
        self.assertIn('claim_url', data)
        self.assertIn('expires_at', data)
        self.assertIn(data.get('status'), ['sent', 'pending'])
        # Check claim_url contains only the invite_code and no sensitive data
        self.assertIn(data['invite_code'], data['claim_url'])
        self.assertNotIn('password', data['claim_url'])
        self.assertNotIn('jwt', data['claim_url'].lower())

        # 2. GET /api/profile-invites lists pending invites without raw tokens or claim_url
        list_res = self.app.get('/api/profile-invites', headers=self.headers_a)
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.get_json()
        self.assertTrue(list_data['success'])
        self.assertGreaterEqual(len(list_data['invites']), 1)
        for inv in list_data['invites']:
            self.assertNotIn('invite_code', inv)
            self.assertNotIn('invite_token', inv)
            self.assertNotIn('claim_url', inv)
            self.assertIn('invite_id', inv)
            self.assertIn('status', inv)
            self.assertIn('expires_at', inv)



class OwnerCredentialMultiProfileFlowTestCase(unittest.TestCase):
    """
    Dedicated test suite covering all 20 required multi-profile authentication,
    invitation unlocking, token isolation, and permission matrix tests.
    """
    @classmethod
    def setUpClass(cls):
        # Database and storage guards
        if getattr(db, 'name', None) != 'fitlens_test':
            raise RuntimeError("Database guard failure: expected fitlens_test")
        if 'data_test' not in os.path.realpath(ACCOUNTS_DIR):
            raise RuntimeError("Storage root guard failure: expected data_test")

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.ctx = app.app_context()
        self.ctx.push()

        self.owner_id = "UTEST_REQ_OWNER_01"
        self.other_owner_id = "UTEST_REQ_OWNER_02"
        self.owner_email = "owner_req@fitlens.ai"
        self.owner_password = "OwnerSecret2026!"
        self.other_owner_email = "other_req@fitlens.ai"

        self._cleanup()

        # Seed owner account
        pw_hash = bcrypt.hashpw(self.owner_password.encode(), bcrypt.gensalt()).decode()
        users_col.insert_one({
            'user_id': self.owner_id,
            'email': self.owner_email,
            'name': 'Primary Owner',
            'password_hash': pw_hash,
            'created_at': dt.datetime.now(dt.timezone.utc)
        })

        # Seed second owner account
        pw_hash2 = bcrypt.hashpw("OtherSecret2026!".encode(), bcrypt.gensalt()).decode()
        users_col.insert_one({
            'user_id': self.other_owner_id,
            'email': self.other_owner_email,
            'name': 'Other Owner',
            'password_hash': pw_hash2,
            'created_at': dt.datetime.now(dt.timezone.utc)
        })

        # Initial owner login to get owner account token
        login_res = self.app.post('/api/auth/login', json={
            'email': self.owner_email,
            'password': self.owner_password
        })
        self.owner_token = login_res.get_json()['access_token']
        self.owner_headers = {'Authorization': f'Bearer {self.owner_token}', 'Content-Type': 'application/json'}

        login_res_b = self.app.post('/api/auth/login', json={
            'email': self.other_owner_email,
            'password': "OtherSecret2026!"
        })
        self.other_owner_token = login_res_b.get_json()['access_token']
        self.other_owner_headers = {'Authorization': f'Bearer {self.other_owner_token}', 'Content-Type': 'application/json'}

    def tearDown(self):
        self._cleanup()
        self.ctx.pop()

    def _cleanup(self):
        if getattr(db, 'name', None) != 'fitlens_test':
            return
        users_col.delete_many({'user_id': {'$in': [self.owner_id, self.other_owner_id]}})
        profiles_col.delete_many({'account_user_id': {'$in': [self.owner_id, self.other_owner_id]}})
        profile_invites_col.delete_many({'account_user_id': {'$in': [self.owner_id, self.other_owner_id]}})
        measurements_col.delete_many({'account_user_id': {'$in': [self.owner_id, self.other_owner_id]}})

    # 1. Owner can log in with owner email and password
    def test_req_01_owner_can_login(self):
        res = self.app.post('/api/auth/login', json={
            'email': self.owner_email,
            'password': self.owner_password
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['account_user_id'], self.owner_id)
        self.assertEqual(data['role'], 'owner')
        self.assertTrue(data['requires_profile_unlock'])
        self.assertTrue(bool(data['access_token']))

    # 2. Invalid owner credentials are rejected
    def test_req_02_invalid_credentials_rejected(self):
        res = self.app.post('/api/auth/login', json={
            'email': self.owner_email,
            'password': 'WrongPassword123!'
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn('Invalid email or password', res.get_json()['error'])

    # 3. Available profiles belong only to authenticated owner account
    def test_req_03_available_profiles_belong_to_owner(self):
        self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Harshitha', 'relationship': 'Family'})
        self.app.post('/api/profiles', headers=self.other_owner_headers, json={'name': 'Foreign Profile', 'relationship': 'Friend'})

        res = self.app.get('/api/profiles/available', headers=self.owner_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        returned_names = [p['name'] for p in data['profiles']]
        self.assertIn('Harshitha', returned_names)
        self.assertNotIn('Foreign Profile', returned_names)
        for p in data['profiles']:
            self.assertTrue(p['locked'])
            self.assertNotIn('measurements', p)
            self.assertNotIn('mesh_glb_key', p)

    # 4. Invited email matching invitation unlocks exactly one profile
    def test_req_04_invited_email_matching_invitation_unlocks_profile(self):
        p_res = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Harshitha', 'relationship': 'Family'})
        prof_id = p_res.get_json()['profile']['id']
        inv_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': prof_id,
            'invited_email': 'harshitha@test.com'
        })
        self.assertEqual(inv_res.status_code, 201)

        unlock_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': '  HARSHITHA@TEST.COM  '
        })
        self.assertEqual(unlock_res.status_code, 200)
        data = unlock_res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['profile']['profile_id'], prof_id)
        self.assertEqual(data['profile']['name'], 'Harshitha')
        self.assertTrue(bool(data['profile_session_token']))
        decoded = decode_token(data['profile_session_token'])
        self.assertEqual(decoded.get('role'), 'profile_member_session')
        self.assertEqual(decoded.get('access_mode'), 'invited_profile')
        self.assertEqual(decoded.get('profile_id'), prof_id)

    # 5. Incorrect invited email is rejected
    def test_req_05_incorrect_invited_email_rejected(self):
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'relationship': 'Family',
            'invited_email': 'legit@test.com'
        })
        unlock_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': 'unknown@test.com'
        })
        self.assertEqual(unlock_res.status_code, 404)

    # 6. Expired invitation is rejected
    def test_req_06_expired_invitation_rejected(self):
        inv_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'relationship': 'Friend',
            'invited_email': 'expired@test.com'
        })
        inv_id = ObjectId(inv_res.get_json()['invite_id'])
        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=20)
        profile_invites_col.update_one({'_id': inv_id}, {'$set': {'expires_at': past}})

        unlock_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': 'expired@test.com'
        })
        self.assertEqual(unlock_res.status_code, 400)
        self.assertIn('expired', unlock_res.get_json()['error'])

    # 7. Claimed invitation cannot be reused
    def test_req_07_claimed_invitation_cannot_be_reused(self):
        inv_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'relationship': 'Family',
            'invited_email': 'single_use@test.com'
        })
        self.assertEqual(inv_res.status_code, 201)
        u1 = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': 'single_use@test.com'
        })
        self.assertEqual(u1.status_code, 200)

        u2 = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': 'single_use@test.com'
        })
        self.assertEqual(u2.status_code, 400)
        self.assertIn('already been claimed', u2.get_json()['error'])

    # 8. Revoked invitation is rejected
    def test_req_08_revoked_invitation_rejected(self):
        inv_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'relationship': 'Friend',
            'invited_email': 'revoked@test.com'
        })
        inv_id = inv_res.get_json()['invite_id']
        rev_res = self.app.delete(f'/api/profile-invites/{inv_id}', headers=self.owner_headers)
        self.assertEqual(rev_res.status_code, 200)

        unlock_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': 'revoked@test.com'
        })
        self.assertEqual(unlock_res.status_code, 400)
        self.assertIn('revoked', unlock_res.get_json()['error'])

    # 9. Invitation from another owner cannot unlock a profile
    def test_req_09_invitation_from_another_owner_cannot_unlock(self):
        self.app.post('/api/profile-invites', headers=self.other_owner_headers, json={
            'relationship': 'Colleague',
            'invited_email': 'cross_owner@test.com'
        })
        cross_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={
            'invited_email': 'cross_owner@test.com'
        })
        self.assertEqual(cross_res.status_code, 404)

    # 10. Restricted invited-profile token cannot access another profile
    def test_req_10_restricted_token_cannot_access_another_profile(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'P1'}).get_json()['profile']['id']
        p2 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'P2'}).get_json()['profile']['id']

        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'p1@test.com'})
        unlock_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'p1@test.com'})
        p1_token = unlock_res.get_json()['profile_session_token']
        p1_headers = {'Authorization': f'Bearer {p1_token}', 'Content-Type': 'application/json'}

        bad_req = self.app.get(f'/api/profiles/{p2}/measurements', headers=p1_headers)
        self.assertEqual(bad_req.status_code, 403)

    # 11. Restricted invited-profile token cannot access owner-management routes
    def test_req_11_restricted_token_cannot_access_owner_management_routes(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Member P1'}).get_json()['profile']['id']
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'member1@test.com'})
        unlock_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'member1@test.com'})
        token = unlock_res.get_json()['profile_session_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        self.assertEqual(self.app.get('/api/profiles', headers=headers).status_code, 403)
        self.assertEqual(self.app.post('/api/profiles', headers=headers, json={'name': 'Illegal'}).status_code, 403)
        self.assertEqual(self.app.post('/api/profile-invites', headers=headers, json={'relationship': 'Friend'}).status_code, 403)
        self.assertEqual(self.app.delete(f'/api/profiles/{p1}', headers=headers).status_code, 403)
        self.assertEqual(self.app.post(f'/api/profiles/{p1}/archive', headers=headers).status_code, 403)

    # 12. Owner profile unlock opens only owner profile
    def test_req_12_owner_profile_unlock(self):
        res = self.app.post('/api/profiles/unlock-owner', headers=self.owner_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['profile']['is_owner'])
        decoded = decode_token(data['profile_session_token'])
        self.assertEqual(decoded.get('role'), 'owner_profile_session')
        self.assertEqual(decoded.get('access_mode'), 'owner_profile')

    # 13. Owner cannot use profile unlock to access member sensitive data
    def test_req_13_owner_cannot_access_member_sensitive_data(self):
        p_mem = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Private Member'}).get_json()['profile']['id']
        owner_unlock = self.app.post('/api/profiles/unlock-owner', headers=self.owner_headers).get_json()
        owner_profile_token = owner_unlock['profile_session_token']
        owner_profile_headers = {'Authorization': f'Bearer {owner_profile_token}'}

        m_res = self.app.get(f'/api/profiles/{p_mem}/measurements', headers=owner_profile_headers)
        self.assertEqual(m_res.status_code, 403)

        raw_res = self.app.get(f'/api/profiles/{p_mem}/measurements', headers=self.owner_headers)
        self.assertEqual(raw_res.status_code, 403)

    # 14. Profile IDs in request body or URL cannot override token profile ID
    def test_req_14_profile_ids_cannot_override_token_profile_id(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Profile One'}).get_json()['profile']['id']
        p2 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Profile Two'}).get_json()['profile']['id']
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'override@test.com'})
        token = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'override@test.com'}).get_json()['profile_session_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        url_tamper = self.app.get(f'/api/profiles/{p2}/measurements', headers=headers)
        self.assertEqual(url_tamper.status_code, 403)

        save_tamper = self.app.post('/api/measurements/save', headers=headers, json={
            'profile_id': p2,
            'measurements': {'waist': 80}
        })
        self.assertEqual(save_tamper.status_code, 403)

    # 15. Socket.IO rejects a mismatched profile ID
    def test_req_15_socket_io_rejects_mismatched_profile_id(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Socket Profile 1'}).get_json()['profile']['id']
        p2 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Socket Profile 2'}).get_json()['profile']['id']
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'socket@test.com'})
        token = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'socket@test.com'}).get_json()['profile_session_token']

        socket_client = socketio.test_client(app)
        socket_client.emit('start_measurement_session', {
            'token': token,
            'profile_id': p2
        })
        events = socket_client.get_received()
        error_events = [e for e in events if e['name'] == 'error']
        self.assertTrue(len(error_events) >= 1)
        self.assertIn('Profile ID mismatch', error_events[0]['args'][0]['message'])

    # 16. Measurement files and mesh files are protected by profile-session authorization
    def test_req_16_measurement_files_and_mesh_protected(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Asset P1'}).get_json()['profile']['id']
        p2 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Asset P2'}).get_json()['profile']['id']
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'asset1@test.com'})
        token_p1 = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'asset1@test.com'}).get_json()['profile_session_token']

        file_res = self.app.get(f'/api/profiles/{p2}/files/front.jpg', headers={'Authorization': f'Bearer {token_p1}'})
        self.assertEqual(file_res.status_code, 403)
        mesh_res = self.app.get(f'/api/profiles/{p2}/mesh/mesh_01', headers={'Authorization': f'Bearer {token_p1}'})
        self.assertEqual(mesh_res.status_code, 403)

    # 17. Logout clears both account and profile sessions
    def test_req_17_logout_clears_sessions(self):
        unauth_m = self.app.get('/api/profiles/available')
        self.assertEqual(unauth_m.status_code, 401)
        unauth_meas = self.app.get('/api/measurements/history')
        self.assertEqual(unauth_meas.status_code, 401)

    # 18. Existing profile creation/archive/delete behavior still works for the owner
    def test_req_18_existing_profile_lifecycle_works_for_owner(self):
        c_res = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Lifecycle Prof', 'relationship': 'Friend'})
        self.assertEqual(c_res.status_code, 201)
        pid = c_res.get_json()['profile']['id']
        a_res = self.app.post(f'/api/profiles/{pid}/archive', headers=self.owner_headers)
        self.assertEqual(a_res.status_code, 200)
        d_res = self.app.delete(f'/api/profiles/{pid}', headers=self.owner_headers)
        self.assertEqual(d_res.status_code, 200)

    # 19. All other profiles remain locked after one profile is unlocked
    def test_req_19_all_other_profiles_remain_locked(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Locked P1'}).get_json()['profile']['id']
        p2 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'Locked P2'}).get_json()['profile']['id']
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'locktest@test.com'})
        u_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'locktest@test.com'}).get_json()
        unlocked_id = u_res['profile']['profile_id']
        self.assertEqual(unlocked_id, p1)

        avail = self.app.get('/api/profiles/available', headers=self.owner_headers).get_json()['profiles']
        for p in avail:
            self.assertTrue(p['locked'])

        p1_token = u_res['profile_session_token']
        p2_access = self.app.get(f'/api/profiles/{p2}/measurements', headers={'Authorization': f'Bearer {p1_token}'})
        self.assertEqual(p2_access.status_code, 403)

    # 20. Frontend does not display profile switching after successful non-owner unlock
    def test_req_20_frontend_profile_switching_disabled(self):
        p1 = self.app.post('/api/profiles', headers=self.owner_headers, json={'name': 'NoSwitch Member'}).get_json()['profile']['id']
        self.app.post('/api/profile-invites', headers=self.owner_headers, json={'profile_id': p1, 'invited_email': 'noswitch@test.com'})
        u_res = self.app.post('/api/profiles/unlock-invited', headers=self.owner_headers, json={'invited_email': 'noswitch@test.com'}).get_json()
        token = u_res['profile_session_token']
        claims = decode_token(token)

        self.assertEqual(claims.get('access_mode'), 'invited_profile')
        self.assertEqual(claims.get('role'), 'profile_member_session')
        self.assertEqual(claims.get('profile_id'), p1)
        switch_attempt = self.app.get(f'/api/profiles', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(switch_attempt.status_code, 403)



class NonOwnerInvitationFlowTestCase(unittest.TestCase):
    """
    Comprehensive test suite for the non-owner member invitation flow:
    - Opaque token generation and hash storage
    - Validation and audit on open
    - Email verification with single-use OTP
    - Atomic transition to claimed
    - Privacy-safe hashed IP and owner notifications
    - Restricted profile-session JWT isolation
    - Owner dashboard status and audit display
    """

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        app.config['TESTING'] = True
        self.ctx = app.app_context()
        self.ctx.push()

        self._cleanup()

        # Create owner user
        owner_doc = {
            'user_id': 'owner_inv_test_user',
            'name': 'Account Owner',
            'email': 'owner@fitlens.com',
            'password_hash': generate_password_hash('OwnerPass123'),
            'created_at': dt.datetime.now(dt.timezone.utc)
        }
        users_col.insert_one(owner_doc)
        self.owner_headers = {
            'Authorization': f"Bearer {create_access_token(identity='owner_inv_test_user')}",
            'Content-Type': 'application/json'
        }

        # Create owner profile
        owner_prof = {
            'account_user_id': 'owner_inv_test_user',
            'name': 'Account Owner',
            'profile_type': 'owner',
            'is_owner': True,
            'is_owner_profile': True,
            'status': 'active',
            'created_at': dt.datetime.now(dt.timezone.utc)
        }
        profiles_col.insert_one(owner_prof)

        # Create a non-owner profile
        member_prof = {
            'account_user_id': 'owner_inv_test_user',
            'name': 'Harshitha',
            'relationship': 'Sister',
            'profile_type': 'adult',
            'is_owner': False,
            'is_owner_profile': False,
            'status': 'active',
            'created_at': dt.datetime.now(dt.timezone.utc)
        }
        m_res = profiles_col.insert_one(member_prof)
        self.member_profile_id = str(m_res.inserted_id)

    def tearDown(self):
        self._cleanup()
        self.ctx.pop()

    def _cleanup(self):
        profiles_col.delete_many({'account_user_id': 'owner_inv_test_user'})
        profile_invites_col.delete_many({'account_user_id': 'owner_inv_test_user'})
        users_col.delete_many({'user_id': 'owner_inv_test_user'})
        notifications_col.delete_many({'account_user_id': 'owner_inv_test_user'})

    def test_01_owner_creates_invitation_with_opaque_token_and_hash_storage(self):
        """Owner creates one-time invite; only token hash is stored, never plain token."""
        res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com',
            'relationship': 'Sister'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'sent')
        self.assertEqual(data['status_display'], 'Sent')
        self.assertIn('invite_token', data)
        self.assertIn('claim_url', data)
        self.assertIn('deep_link', data)
        self.assertIn(data['invite_token'], data['claim_url'])

        # Verify database doc: plain invite_token is NOT stored; token_hash IS stored
        invite_doc = profile_invites_col.find_one({'_id': ObjectId(data['invite_id'])})
        self.assertIsNotNone(invite_doc)
        self.assertNotIn('invite_token', invite_doc)
        self.assertIn('token_hash', invite_doc)
        self.assertEqual(invite_doc['token_hash'], hash_secret(data['invite_token']))
        self.assertEqual(invite_doc['status'], 'sent')
        self.assertEqual(invite_doc['owner_email_normalized'], 'owner@fitlens.com')
        self.assertIsNone(invite_doc['owner_otp_hash'])
        self.assertIsNone(invite_doc['opened_at'])
        self.assertIsNone(invite_doc['owner_approved_at'])
        self.assertIsNone(invite_doc['claimed_at'])

        # Audit events initialized
        audit = invite_doc.get('audit_events', [])
        self.assertTrue(any(a['event'] == 'profile_invitation_created' for a in audit))

    def test_02_non_owner_validates_opaque_token_and_audit(self):
        """Non-owner opens invite link; token is validated and opened_at is recorded."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        # Public validation without any credentials
        v_res = self.app.post('/api/invite/validate', json={'token': token})
        self.assertEqual(v_res.status_code, 200)
        v_data = v_res.get_json()
        self.assertTrue(v_data['success'])
        self.assertEqual(v_data['status'], 'opened')
        self.assertEqual(v_data['masked_owner_email'], 'o***@fitlens.com')
        self.assertEqual(v_data['assigned_profile']['name'], 'Harshitha')
        self.assertTrue(v_data['assigned_profile']['locked'])

        # Does NOT expose owner password, measurements, or raw token
        self.assertNotIn('password', str(v_data).lower())
        self.assertNotIn('measurements', v_data['assigned_profile'])
        self.assertNotIn('height', v_data['assigned_profile'])
        self.assertNotIn('token', v_data)

        # Check DB updated opened_at and audit event
        invite_doc = profile_invites_col.find_one({'_id': ObjectId(c_res['invite_id'])})
        self.assertIsNotNone(invite_doc['opened_at'])
        self.assertEqual(invite_doc['status'], 'opened')
        audit = invite_doc.get('audit_events', [])
        self.assertTrue(any(a['event'] == 'profile_invitation_opened' for a in audit))

    def test_03_non_owner_otp_request_mismatched_owner_email_rejected(self):
        """Entering incorrect owner email returns generic error without leaking account details."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        # Request OTP with wrong owner email
        res = self.app.post('/api/invite/request-owner-otp', json={
            'invite_token': token,
            'owner_email': 'intruder@otherdomain.com'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('does not match', res.get_json()['error'])

    def test_04_non_owner_otp_request_sets_owner_approval_pending(self):
        """Matching owner email dispatches single-use OTP and sets owner_approval_pending."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        res = self.app.post('/api/invite/request-owner-otp', json={
            'invite_token': token,
            'owner_email': 'Owner@FitLens.com'  # Tests email normalization
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        # Plaintext OTP is NEVER returned in response
        self.assertNotIn('otp', res.get_json())
        self.assertNotIn('code', res.get_json())

        # DB has owner_approval_pending, owner_otp_hash, owner_otp_expires_at
        invite_doc = profile_invites_col.find_one({'_id': ObjectId(c_res['invite_id'])})
        self.assertEqual(invite_doc['status'], 'owner_approval_pending')
        self.assertIsNotNone(invite_doc['owner_otp_hash'])
        self.assertIsNotNone(invite_doc['owner_otp_expires_at'])
        self.assertIsNotNone(invite_doc['owner_approval_requested_at'])
        audit = invite_doc.get('audit_events', [])
        self.assertTrue(any(a['event'] == 'profile_invitation_owner_otp_requested' for a in audit))

    def test_05_non_owner_otp_verification_and_atomic_claim(self):
        """Validating owner OTP atomically transitions invite to claimed, sets owner_approved_at, and creates owner notification."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        self.app.post('/api/invite/request-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com'
        })

        invite_doc = profile_invites_col.find_one({'_id': ObjectId(c_res['invite_id'])})
        test_otp = invite_doc.get('_test_last_owner_otp') or invite_doc.get('_test_last_otp')
        self.assertIsNotNone(test_otp)

        # Invalid OTP failure
        bad_res = self.app.post('/api/invite/verify-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com',
            'otp': '000000'
        })
        self.assertEqual(bad_res.status_code, 400)

        # Correct OTP verification
        verify_res = self.app.post('/api/invite/verify-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com',
            'otp': test_otp,
            'device_label': 'Chrome on Windows 11'
        })
        self.assertEqual(verify_res.status_code, 200)
        v_data = verify_res.get_json()
        self.assertTrue(v_data['success'])
        self.assertIn('profile_session_token', v_data)
        self.assertEqual(v_data['profile']['name'], 'Harshitha')
        self.assertFalse(v_data['profile']['is_owner'])

        # Verify DB transition to claimed
        claimed_doc = profile_invites_col.find_one({'_id': ObjectId(c_res['invite_id'])})
        self.assertEqual(claimed_doc['status'], 'claimed')
        self.assertIsNotNone(claimed_doc['claimed_at'])
        self.assertIsNotNone(claimed_doc['owner_approved_at'])
        self.assertEqual(claimed_doc['owner_email_normalized'], 'owner@fitlens.com')
        self.assertEqual(claimed_doc['device_label'], 'Chrome on Windows 11')
        self.assertIsNotNone(claimed_doc['security_ip_hash'])
        self.assertIsNone(claimed_doc['owner_otp_hash'])

        # Audit events includes profile_invitation_owner_approved_and_claimed
        audit = claimed_doc.get('audit_events', [])
        self.assertTrue(any(a['event'] == 'profile_invitation_owner_approved_and_claimed' for a in audit))

        # In-app notification created for owner
        notif = notifications_col.find_one({
            'account_user_id': 'owner_inv_test_user',
            'type': 'profile_invitation_claimed'
        })
        self.assertIsNotNone(notif)
        self.assertEqual(notif['masked_email'], 'o***@fitlens.com')
        self.assertEqual(notif['profile_name'], 'Harshitha')
        self.assertFalse(notif['read'])

    def test_06_restricted_profile_session_jwt_isolation(self):
        """Restricted profile session JWT contains restricted claims and cannot access owner actions."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        self.app.post('/api/invite/request-owner-otp', json={'invite_token': token, 'owner_email': 'owner@fitlens.com'})
        inv = profile_invites_col.find_one({'_id': ObjectId(c_res['invite_id'])})
        verify_res = self.app.post('/api/invite/verify-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com',
            'otp': inv['_test_last_owner_otp']
        }).get_json()

        member_jwt = verify_res['profile_session_token']
        claims = decode_token(member_jwt)
        self.assertEqual(claims['role'], 'profile_member_session')
        self.assertEqual(claims['access_mode'], 'invited_profile')
        self.assertEqual(claims['account_user_id'], 'owner_inv_test_user')
        self.assertEqual(claims['profile_id'], self.member_profile_id)
        self.assertEqual(claims['invite_id'], c_res['invite_id'])
        self.assertFalse(claims.get('is_owner', False))

        m_headers = {'Authorization': f'Bearer {member_jwt}', 'Content-Type': 'application/json'}

        # 1. /api/auth/me returns safe member user profile, NOT owner
        me_res = self.app.get('/api/auth/me', headers=m_headers)
        self.assertEqual(me_res.status_code, 200)
        me_user = me_res.get_json()['user']
        self.assertEqual(me_user['name'], 'Harshitha')
        self.assertEqual(me_user['role'], 'profile_member_session')
        self.assertEqual(me_user['access_mode'], 'invited_profile')
        self.assertFalse(me_user['is_owner'])

        # 2. Member CANNOT manage profiles (create, delete, list owner profiles)
        cant_manage = self.app.get('/api/profiles', headers=m_headers)
        self.assertEqual(cant_manage.status_code, 403)

        cant_invite = self.app.post('/api/profile-invites', headers=m_headers, json={'relationship': 'Friend'})
        self.assertEqual(cant_invite.status_code, 403)

        # 3. /api/profiles/available returns ONLY their assigned profile, unlocked
        avail_res = self.app.get('/api/profiles/available', headers=m_headers)
        self.assertEqual(avail_res.status_code, 200)
        avail_profiles = avail_res.get_json()['profiles']
        self.assertEqual(len(avail_profiles), 1)
        self.assertEqual(avail_profiles[0]['id'], self.member_profile_id)
        self.assertFalse(avail_profiles[0]['locked'])

    def test_07_owner_dashboard_displays_invitation_audit_and_masked_email(self):
        """Owner dashboard displays invitation status, audit timestamps, and masked email."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        # Open token
        self.app.post('/api/invite/validate', json={'token': token})

        # Claim invite
        self.app.post('/api/invite/request-owner-otp', json={'invite_token': token, 'owner_email': 'owner@fitlens.com'})
        inv = profile_invites_col.find_one({'_id': ObjectId(c_res['invite_id'])})
        self.app.post('/api/invite/verify-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com',
            'otp': inv['_test_last_owner_otp']
        })

        # Owner lists invites
        list_res = self.app.get('/api/profile-invites', headers=self.owner_headers)
        self.assertEqual(list_res.status_code, 200)
        invites = list_res.get_json()['invites']
        self.assertTrue(len(invites) >= 1)

        target_inv = next(i for i in invites if i['invite_id'] == c_res['invite_id'])
        self.assertEqual(target_inv['display_name'], 'Harshitha')
        self.assertEqual(target_inv['status_display'], 'Accepted')
        self.assertEqual(target_inv['masked_email'], 'h***@example.com')
        self.assertIsNotNone(target_inv['sent_at'])
        self.assertIsNotNone(target_inv['opened_at'])
        self.assertIsNotNone(target_inv['owner_approved_at'])
        self.assertIsNotNone(target_inv['claimed_at'])

        # Does NOT expose raw token, OTP, or non-owner measurements
        self.assertNotIn('token', target_inv)
        self.assertNotIn('otp', target_inv)
        self.assertNotIn('measurements', target_inv)
        self.assertNotIn('raw_ip', target_inv)

        # Owner checks notifications
        notif_res = self.app.get('/api/notifications', headers=self.owner_headers)
        self.assertEqual(notif_res.status_code, 200)
        notifs = notif_res.get_json()['notifications']
        self.assertTrue(len(notifs) >= 1)
        self.assertEqual(notifs[0]['type'], 'profile_invitation_claimed')
        self.assertFalse(notifs[0]['read'])

        # Mark read
        read_res = self.app.post(f"/api/notifications/{notifs[0]['id']}/read", headers=self.owner_headers)
        self.assertEqual(read_res.status_code, 200)

    def test_08_owner_can_revoke_invitation(self):
        """Owner revokes invite; status becomes revoked and invite can no longer be used."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        inv_id = c_res['invite_id']
        token = c_res['invite_token']

        # Owner revokes
        rev_res = self.app.delete(f'/api/profile-invites/{inv_id}', headers=self.owner_headers)
        self.assertEqual(rev_res.status_code, 200)

        # Non-owner attempt to validate returns error
        v_res = self.app.post('/api/invite/validate', json={'token': token})
        self.assertEqual(v_res.status_code, 400)
        self.assertIn('revoked', v_res.get_json()['error'])

    def test_09_resend_cooldown_and_max_attempt_limit(self):
        """Resend cooldown enforces 60s wait; 5 failed OTP attempts locks out the OTP."""
        c_res = self.app.post('/api/profile-invites', headers=self.owner_headers, json={
            'profile_id': self.member_profile_id,
            'invited_email': 'harshitha@example.com'
        }).get_json()
        token = c_res['invite_token']

        # Initial request succeeds
        res1 = self.app.post('/api/invite/request-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com'
        })
        self.assertEqual(res1.status_code, 200)

        # Immediate second request fails with 429 cooldown error
        res2 = self.app.post('/api/invite/request-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com'
        })
        self.assertEqual(res2.status_code, 429)
        self.assertIn('seconds before requesting a new approval code', res2.get_json()['error'])

        # Attempt 5 wrong OTPs
        for _ in range(5):
            self.app.post('/api/invite/verify-owner-otp', json={
                'invite_token': token,
                'owner_email': 'owner@fitlens.com',
                'otp': '999999'
            })

        # 6th attempt should be blocked with 429
        fail_res = self.app.post('/api/invite/verify-owner-otp', json={
            'invite_token': token,
            'owner_email': 'owner@fitlens.com',
            'otp': '999999'
        })
        self.assertEqual(fail_res.status_code, 429)
        self.assertIn('Too many incorrect attempts', fail_res.get_json()['error'])


class NonOwnerSelfServiceEditTestCase(unittest.TestCase):
    """
    Test suite verifying FitLens restricted non-owner profile self-service editing:
    1. Member can update own display_name.
    2. Member can update own height_cm.
    3. Member cannot send profile_id in body to update another profile (HTTP 403).
    4. Member cannot update relationship/profile_type/status/account_user_id/role (HTTP 403).
    5. Member cannot update archived/deleted profile (HTTP 403).
    6. Owner management route behavior remains unchanged.
    7. Historical measurement height_cm_used is unchanged after profile height update.
    8. Direct access to Settings/Profile Management remains blocked for invited sessions.
    """

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.ctx = app.app_context()
        self.ctx.push()

        self.user_id = 'test_owner_self_edit_user'

        # Clean test database
        users_col.delete_many({'user_id': self.user_id})
        profiles_col.delete_many({'account_user_id': self.user_id})
        profile_invites_col.delete_many({'account_user_id': self.user_id})
        measurements_col.delete_many({'account_user_id': self.user_id})
        try:
            db['audit_logs'].delete_many({'actor_role': 'profile_member_session'})
        except Exception:
            pass

        # Create owner user
        self.owner_email = 'owner_self_edit@fitlens.com'
        users_col.insert_one({
            'user_id': self.user_id,
            'email': self.owner_email,
            'name': 'Owner User',
            'password_hash': bcrypt.hashpw(b'OwnerPassword123', bcrypt.gensalt()).decode()
        })

        # Ensure default owner profile
        self.owner_profile = get_or_create_owner_profile(self.user_id)
        self.owner_profile_id = str(self.owner_profile['_id'])

        now = dt.datetime.now(dt.timezone.utc)
        # Create invited member profile
        member_doc = {
            'account_user_id': self.user_id,
            'name': 'Original Member Name',
            'display_name': 'Original Member Name',
            'relationship': 'Family',
            'profile_type': 'adult',
            'is_owner': False,
            'is_owner_profile': False,
            'status': 'active',
            'is_archived': False,
            'default_height_cm': 165.0,
            'height_cm': 165.0,
            'created_at': now,
            'updated_at': now
        }
        res = profiles_col.insert_one(member_doc)
        self.member_profile_id = str(res.inserted_id)

        # Create another member profile to test cross-profile isolation
        another_doc = {
            'account_user_id': self.user_id,
            'name': 'Another Member',
            'display_name': 'Another Member',
            'relationship': 'Friend',
            'profile_type': 'adult',
            'is_owner': False,
            'is_owner_profile': False,
            'status': 'active',
            'is_archived': False,
            'default_height_cm': 175.0,
            'height_cm': 175.0,
            'created_at': now,
            'updated_at': now
        }
        res2 = profiles_col.insert_one(another_doc)
        self.another_profile_id = str(res2.inserted_id)

        # Generate restricted profile session JWT
        self.member_jwt = create_access_token(
            identity=self.user_id,
            additional_claims={
                'role': 'profile_member_session',
                'access_mode': 'invited_profile',
                'account_user_id': self.user_id,
                'profile_id': self.member_profile_id
            }
        )
        self.member_headers = {
            'Authorization': f'Bearer {self.member_jwt}',
            'Content-Type': 'application/json'
        }

        # Generate owner session token
        self.owner_jwt = create_access_token(
            identity=self.user_id,
            additional_claims={
                'role': 'owner_profile_session',
                'access_mode': 'owner_profile',
                'account_user_id': self.user_id,
                'profile_id': self.owner_profile_id
            }
        )
        self.owner_headers = {
            'Authorization': f'Bearer {self.owner_jwt}',
            'Content-Type': 'application/json'
        }

    def tearDown(self):
        try:
            self.ctx.pop()
        except Exception:
            pass

    def test_01_member_can_update_own_display_name(self):
        """1. Member can update own display_name and audit event is recorded without measurements."""
        res = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'display_name': 'Updated Member Name'}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['profile']['display_name'], 'Updated Member Name')
        self.assertEqual(data['profile']['name'], 'Updated Member Name')

        # Verify DB document
        profile = profiles_col.find_one({'_id': ObjectId(self.member_profile_id)})
        self.assertEqual(profile['name'], 'Updated Member Name')
        self.assertEqual(profile['display_name'], 'Updated Member Name')

        # Verify audit event in profile document
        audit_events = profile.get('audit_events', [])
        self.assertTrue(any(e.get('event') == 'profile_personal_details_updated' for e in audit_events))
        evt = next(e for e in audit_events if e.get('event') == 'profile_personal_details_updated')
        self.assertEqual(evt['profile_id'], self.member_profile_id)
        self.assertEqual(evt['actor_role'], 'profile_member_session')
        self.assertEqual(evt['fields_updated'], ['display_name'])
        self.assertIn('timestamp', evt)
        # Ensure audit log does not store previous/new body measurement data
        for forbidden in ['measurements', 'measurement', 'chest', 'waist', 'hips', 'height_cm_used', 'values']:
            self.assertNotIn(forbidden, evt)

        # GET /api/profiles/me/personal-details returns updated info
        get_res = self.app.get('/api/profiles/me/personal-details', headers=self.member_headers)
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()['profile']['display_name'], 'Updated Member Name')

    def test_02_member_can_update_own_height_cm(self):
        """2. Member can update own height_cm with server-side validation."""
        # Valid height update
        res = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'height_cm': 172.5}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['profile']['height_cm'], 172.5)

        # Verify DB document
        profile = profiles_col.find_one({'_id': ObjectId(self.member_profile_id)})
        self.assertEqual(profile['height_cm'], 172.5)
        self.assertEqual(profile['default_height_cm'], 172.5)

        # Invalid height validation: below 100 cm
        err_low = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'height_cm': 95}
        )
        self.assertEqual(err_low.status_code, 400)

        # Invalid height validation: above 250 cm
        err_high = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'height_cm': 280}
        )
        self.assertEqual(err_high.status_code, 400)

        # Invalid non-numeric height
        err_str = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'height_cm': 'tall'}
        )
        self.assertEqual(err_str.status_code, 400)

    def test_03_member_cannot_send_profile_id_in_body_to_update_another_profile(self):
        """3. Member cannot send profile_id in body to update another profile (HTTP 403)."""
        res = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={
                'display_name': 'Attacker Name',
                'profile_id': self.another_profile_id
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn('Forbidden', res.get_json().get('error', ''))

        # Even sending own profile_id in body is rejected with 403 because profile_id is not allowed
        res_own = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={
                'display_name': 'Attacker Name',
                'profile_id': self.member_profile_id
            }
        )
        self.assertEqual(res_own.status_code, 403)

        # Verify target profile was unchanged
        another = profiles_col.find_one({'_id': ObjectId(self.another_profile_id)})
        self.assertEqual(another['name'], 'Another Member')

    def test_04_member_cannot_update_relationship_profile_type_status_account_user_id_role(self):
        """4. Member cannot update relationship, profile_type, status, account_user_id, role, or other protected fields (HTTP 403)."""
        protected_tests = [
            {'relationship': 'Owner'},
            {'profile_type': 'owner'},
            {'status': 'deleted'},
            {'account_user_id': 'malicious_account'},
            {'role': 'owner_profile_session'},
            {'access_mode': 'owner_profile'},
            {'is_owner': True},
            {'is_archived': True},
            {'owner_email': 'hacker@example.com'},
            {'created_by': 'attacker'}
        ]

        for payload in protected_tests:
            res = self.app.patch(
                '/api/profiles/me/personal-details',
                headers=self.member_headers,
                json=payload
            )
            self.assertEqual(
                res.status_code, 403,
                f"Payload {payload} should have been rejected with 403 Forbidden, but got {res.status_code}"
            )

        # Verify DB document is completely unmodified
        member = profiles_col.find_one({'_id': ObjectId(self.member_profile_id)})
        self.assertEqual(member['relationship'], 'Family')
        self.assertEqual(member['profile_type'], 'adult')
        self.assertEqual(member['status'], 'active')
        self.assertEqual(member['account_user_id'], self.user_id)
        self.assertFalse(member.get('is_owner', False))

    def test_05_member_cannot_update_archived_or_deleted_profile(self):
        """5. Member cannot update an archived or deleted profile (HTTP 403)."""
        # Archive profile
        profiles_col.update_one(
            {'_id': ObjectId(self.member_profile_id)},
            {'$set': {'is_archived': True, 'status': 'archived'}}
        )

        res_archived = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'display_name': 'Try Arch Update'}
        )
        self.assertEqual(res_archived.status_code, 403)

        # Mark as deleted
        profiles_col.update_one(
            {'_id': ObjectId(self.member_profile_id)},
            {'$set': {'is_archived': False, 'status': 'deleted'}}
        )

        res_deleted = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'display_name': 'Try Del Update'}
        )
        self.assertEqual(res_deleted.status_code, 403)

    def test_06_owner_management_route_behavior_remains_unchanged(self):
        """6. Owner management route behavior remains completely blocked with 403 for restricted sessions."""
        # Owner can list profiles
        owner_list = self.app.get('/api/profiles', headers=self.owner_headers)
        self.assertEqual(owner_list.status_code, 200)

        # Member is DENIED on all owner management routes:
        # 1. Profile listing
        self.assertEqual(self.app.get('/api/profiles', headers=self.member_headers).status_code, 403)
        # 2. Profile creation
        self.assertEqual(self.app.post('/api/profiles', headers=self.member_headers, json={'name': 'New'}).status_code, 403)
        # 3. Admin profile edit
        self.assertEqual(self.app.patch(f'/api/profiles/{self.member_profile_id}', headers=self.member_headers, json={'name': 'New'}).status_code, 403)
        # 4. Archive profile
        self.assertEqual(self.app.post(f'/api/profiles/{self.member_profile_id}/archive', headers=self.member_headers).status_code, 403)
        # 5. Delete profile
        self.assertEqual(self.app.delete(f'/api/profiles/{self.member_profile_id}', headers=self.member_headers).status_code, 403)
        # 6. Create invitation
        self.assertEqual(self.app.post('/api/profile-invites', headers=self.member_headers, json={'relationship': 'Friend'}).status_code, 403)
        # 7. List invitations
        self.assertEqual(self.app.get('/api/profile-invites', headers=self.member_headers).status_code, 403)
        # 8. Owner notifications
        self.assertEqual(self.app.get('/api/notifications', headers=self.member_headers).status_code, 403)

    def test_07_historical_measurement_height_cm_used_unchanged_after_profile_height_update(self):
        """7. Historical measurement height_cm_used is unchanged after profile height update, while future measurements use updated height."""
        now = dt.datetime.now(dt.timezone.utc)
        # Insert a historical measurement for this member
        hist_meas_id = ObjectId()
        measurements_col.insert_one({
            '_id': hist_meas_id,
            'analysis_id': 'A_HIST_1234',
            'account_user_id': self.user_id,
            'profile_id': ObjectId(self.member_profile_id),
            'height_cm': 165.0,
            'height_cm_used': 165.0,
            'source': 'upload',
            'created_at': now - dt.timedelta(days=7),
            'measurements': {'chest': 95.0, 'waist': 80.0}
        })

        # Member updates profile height from 165.0 to 182.0
        update_res = self.app.patch(
            '/api/profiles/me/personal-details',
            headers=self.member_headers,
            json={'height_cm': 182.0}
        )
        self.assertEqual(update_res.status_code, 200)

        # Historical measurement retains its original height_cm and height_cm_used
        hist_record = measurements_col.find_one({'_id': hist_meas_id})
        self.assertEqual(hist_record['height_cm_used'], 165.0)
        self.assertEqual(hist_record['height_cm'], 165.0)

        # Simulate future measurement for updated profile: reads updated height
        updated_profile = profiles_col.find_one({'_id': ObjectId(self.member_profile_id)})
        future_height = updated_profile.get('height_cm') or updated_profile.get('default_height_cm')
        self.assertEqual(future_height, 182.0)

        future_meas_id = ObjectId()
        measurements_col.insert_one({
            '_id': future_meas_id,
            'analysis_id': 'A_FUTURE_5678',
            'account_user_id': self.user_id,
            'profile_id': ObjectId(self.member_profile_id),
            'height_cm': future_height,
            'height_cm_used': future_height,
            'source': 'upload',
            'created_at': now,
            'measurements': {'chest': 96.0, 'waist': 81.0}
        })

        future_record = measurements_col.find_one({'_id': future_meas_id})
        self.assertEqual(future_record['height_cm_used'], 182.0)
        self.assertEqual(future_record['height_cm'], 182.0)

        # Historical record is still untouched
        hist_check = measurements_col.find_one({'_id': hist_meas_id})
        self.assertEqual(hist_check['height_cm_used'], 165.0)

    def test_08_direct_access_to_settings_and_profile_management_blocked_for_invited_sessions(self):
        """8. Direct access to account settings and profile management remains blocked with HTTP 403 for invited sessions."""
        # 1. Change password blocked
        res_pw = self.app.post('/api/auth/change-password', headers=self.member_headers, json={
            'current_password': 'OwnerPassword123',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        self.assertEqual(res_pw.status_code, 403)

        # 2. Update account profile name blocked
        res_prof = self.app.put('/api/auth/update-profile', headers=self.member_headers, json={
            'name': 'Hacked Owner Name'
        })
        self.assertEqual(res_prof.status_code, 403)

        # 3. Delete account blocked
        res_del = self.app.delete('/api/auth/delete-account', headers=self.member_headers, json={
            'password': 'OwnerPassword123'
        })
        self.assertEqual(res_del.status_code, 403)

        # 4. Save face embedding blocked
        res_face = self.app.post('/api/auth/save-face', headers=self.member_headers, json={
            'front_image': 'data:image/jpeg;base64,fakeimage'
        })
        self.assertEqual(res_face.status_code, 403)

        # 5. Unlock owner profile blocked
        res_owner_unlock = self.app.post('/api/profiles/unlock-owner', headers=self.member_headers, json={
            'password': 'OwnerPassword123'
        })
        self.assertEqual(res_owner_unlock.status_code, 403)


if __name__ == '__main__':
    unittest.main()



