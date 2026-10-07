"""
FitLens Database Migration: Multi-Profile Support
================================================
Idempotent migration script that:
1. Discovers all existing owner accounts in MongoDB 'users'.
2. Creates a default owner profile ('Self', profile_type='owner') for accounts missing one.
3. Links all legacy unassigned measurements in 'measurements' to the account owner profile
   with account_user_id and profile_id.

Usage:
  Backup Prerequisite (MANDATORY before --apply):
    mongodump --db fitlens --out .\backups\fitlens-before-profile-migration

  Dry-Run (Simulate without writing):
    python backend/migrate_profiles.py --dry-run

  Live Migration:
    python backend/migrate_profiles.py --apply

  Verification:
    python backend/migrate_profiles.py --verify
"""

import sys
import os
import argparse
import datetime as dt
from pymongo import MongoClient
from bson import ObjectId

def run_migration(apply_changes: bool = False, verify_only: bool = False):
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/fitlens')
    print(f"Connecting to MongoDB at: {mongo_uri}")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    try:
        client.admin.command('ping')
        print("Connected to MongoDB successfully.")
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB: {e}")
        sys.exit(1)

    try:
        db = client.get_default_database()
    except Exception:
        db = client['fitlens']

    users_col = db['users']
    profiles_col = db['profiles']
    measurements_col = db['measurements']

    now = dt.datetime.now(dt.timezone.utc)

    total_users = users_col.count_documents({})
    total_profiles = profiles_col.count_documents({})
    total_measurements = measurements_col.count_documents({})

    print("\n" + "=" * 60)
    print("FITLENS DATABASE STATE")
    print(f"  Total Accounts (users):       {total_users}")
    print(f"  Total Profiles:               {total_profiles}")
    print(f"  Total Measurements:           {total_measurements}")
    print("=" * 60 + "\n")

    if verify_only:
        print("--- VERIFICATION REPORT ---")
        unmigrated_measurements = measurements_col.count_documents({
            '$or': [
                {'profile_id': {'$exists': False}},
                {'account_user_id': {'$exists': False}}
            ]
        })
        accounts_without_profile = 0
        for u in users_col.find({}):
            uid = u.get('user_id')
            p = profiles_col.find_one({'account_user_id': uid, 'profile_type': 'owner', 'is_archived': {'$ne': True}})
            if not p:
                accounts_without_profile += 1

        print(f"Accounts without default owner profile: {accounts_without_profile}")
        print(f"Measurements missing profile_id/account_user_id: {unmigrated_measurements}")
        if accounts_without_profile == 0 and unmigrated_measurements == 0:
            print("\nSTATUS: ALL ACCOUNTS AND MEASUREMENTS ARE FULLY MIGRATED.")
        else:
            print("\nSTATUS: Migration pending. Run with --apply to migrate.")
        return

    mode_label = "LIVE APPLY" if apply_changes else "DRY-RUN (SIMULATION ONLY)"
    print(f"Running migration mode: [{mode_label}]\n")

    profiles_to_create = []
    measurements_to_update = []

    # Step 1: Ensure each user account has a default owner profile and check for duplicates
    duplicate_owner_accounts = []
    all_user_ids = set()

    for user in users_col.find({}):
        user_id = user.get('user_id')
        if not user_id:
            print(f"WARNING: User document missing user_id: {user.get('_id')}")
            continue
        all_user_ids.add(user_id)

        # Check for multiple active owner profiles
        owner_profiles = list(profiles_col.find({
            'account_user_id': user_id,
            '$or': [{'is_owner': True}, {'profile_type': 'owner'}],
            'is_archived': {'$ne': True}
        }))

        if len(owner_profiles) > 1:
            duplicate_owner_accounts.append((user_id, [str(p['_id']) for p in owner_profiles]))
        elif len(owner_profiles) == 1:
            owner_profile_id = owner_profiles[0]['_id']
        else:
            new_profile_doc = {
                'account_user_id': user_id,
                'name': user.get('name') or 'My Profile',
                'avatar_url': None,
                'relationship': 'Self',
                'profile_type': 'owner',
                'is_owner': True,
                'privacy_mode': 'account_owner_access',
                'default_height_cm': 170.0,
                'is_archived': False,
                'created_by': 'owner',
                'created_at': user.get('created_at') or now,
                'updated_at': now,
                'last_used_at': now,
                'pin_enabled': False,
                'profile_pin_hash': None
            }
            profiles_to_create.append((user_id, new_profile_doc))

    # Step 2: Check for unmappable measurements and associate legacy measurements with the account owner profile
    unmappable_measurements = []
    for m in measurements_col.find({}):
        # Check if already migrated
        if m.get('profile_id') and m.get('account_user_id'):
            continue

        m_user_id = m.get('account_user_id') or m.get('user_id')
        if not m_user_id or m_user_id not in all_user_ids:
            unmappable_measurements.append((str(m['_id']), m_user_id, m.get('analysis_id')))
            continue

        measurements_to_update.append((m['_id'], m_user_id))

    print(f"MIGRATION PLAN SUMMARY:")
    print(f"  Owner profiles to create:                   {len(profiles_to_create)}")
    print(f"  Measurements to associate with owner:      {len(measurements_to_update)}")
    print(f"  Accounts with duplicate owner profiles:    {len(duplicate_owner_accounts)}")
    print(f"  Unmappable measurements (missing user):     {len(unmappable_measurements)}")

    if duplicate_owner_accounts:
        print("\n[WARNING] Duplicate owner profiles detected for accounts:")
        for uid, pids in duplicate_owner_accounts:
            print(f"  - Account {uid}: profile IDs {pids}")

    if unmappable_measurements:
        print("\n[WARNING] Unmappable measurements detected:")
        for mid, uid, aid in unmappable_measurements:
            print(f"  - Measurement {mid} (analysis_id={aid}, user_id={uid}): user not found in 'users'")

    if not apply_changes:
        print("\n[DRY RUN FINISHED] No database writes were performed.")
        print("\nSAFETY PRE-REQUISITE:")
        print("Before running live migration, you MUST back up the database:")
        print("  mongodump --db fitlens --out .\\backups\\fitlens-before-profile-migration\n")
        print("To execute this migration against your database after backup, run:")
        print("  python backend/migrate_profiles.py --apply\n")
        return

    # Execute LIVE updates
    print("\nExecuting live changes...")
    created_profiles_map = {}

    for uid, pdoc in profiles_to_create:
        res = profiles_col.insert_one(pdoc)
        inserted_id = getattr(res, 'inserted_id', pdoc.get('_id'))
        created_profiles_map[uid] = inserted_id
        print(f"  [+] Created default owner profile for account {uid} -> Profile ID: {inserted_id}")

    migrated_meas_count = 0
    for m_oid, uid in measurements_to_update:
        # Lookup owner profile
        owner_p = profiles_col.find_one({'account_user_id': uid, 'profile_type': 'owner', 'is_archived': {'$ne': True}})
        if not owner_p and uid in created_profiles_map:
            owner_p = {'_id': created_profiles_map[uid]}

        if not owner_p:
            print(f"  [!] Could not find owner profile for measurement {m_oid} (user {uid})")
            continue

        measurements_col.update_one(
            {'_id': m_oid},
            {
                '$set': {
                    'account_user_id': uid,
                    'profile_id': owner_p['_id'],
                    'updated_at': now
                }
            }
        )
        migrated_meas_count += 1

    print(f"\n[MIGRATION COMPLETE]")
    print(f"  Profiles created: {len(profiles_to_create)}")
    print(f"  Measurements updated: {migrated_meas_count}")
    print("\nRun verification check:")
    print("  python backend/migrate_profiles.py --verify\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FitLens Multi-Profile Migration Script")
    parser.add_argument('--dry-run', action='store_true', help="Simulate migration without modifying database")
    parser.add_argument('--apply', action='store_true', help="Execute migration against database")
    parser.add_argument('--verify', action='store_true', help="Verify migration status and data integrity")
    args = parser.parse_args()

    if args.verify:
        run_migration(verify_only=True)
    elif args.apply:
        run_migration(apply_changes=True)
    else:
        run_migration(apply_changes=False)
