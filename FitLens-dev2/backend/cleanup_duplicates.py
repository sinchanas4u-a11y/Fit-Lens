import os
import json
import hashlib
import shutil
from datetime import datetime

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "measurement_images")
METADATA_PATH = os.path.join(IMAGES_DIR, "metadata.jsonl")
BACKUP_PATH = os.path.join(IMAGES_DIR, f"metadata_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")

def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return None

def cleanup():
    print("--- Starting Historical Duplicate Cleanup ---")
    
    if not os.path.exists(METADATA_PATH):
        print("Metadata file not found. Nothing to cleanup.")
        return

    # 1. Create a backup
    print(f"Creating backup of metadata at {BACKUP_PATH}...")
    shutil.copy2(METADATA_PATH, BACKUP_PATH)

    # 2. Read all metadata entries
    all_entries = []
    with open(METADATA_PATH, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    all_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"Read {len(all_entries)} metadata entries.")

    # 3. Scan files and ensure we have hashes for everyone
    # We use a dictionary to group entries by their image content hash
    # unique_images = { hash: [entry1, entry2, ...] }
    unique_images = {}
    
    # Also track files that actually exist on disk
    files_on_disk = set(os.listdir(IMAGES_DIR))
    
    print("Processing and hashing images...")
    processed_count = 0
    for entry in all_entries:
        filename = entry.get('filename')
        if not filename or filename not in files_on_disk:
            continue
            
        filepath = os.path.join(IMAGES_DIR, filename)
        
        # Use existing hash if available, otherwise calculate it
        img_hash = entry.get('hash') or get_file_hash(filepath)
        
        if img_hash:
            entry['hash'] = img_hash # Update entry with hash if missing
            if img_hash not in unique_images:
                unique_images[img_hash] = []
            unique_images[img_hash].append(entry)
            processed_count += 1

    print(f"Processed {processed_count} files. Found {len(unique_images)} unique images.")

    # 4. Identify and remove duplicates
    new_metadata_entries = []
    files_deleted = 0
    
    for img_hash, entries in unique_images.items():
        # Sort entries by timestamp/filename to find the oldest one
        # Entries typically look like: 20251218_105527_618836_upload_front.png
        # They naturally sort chronologically
        entries.sort(key=lambda x: x['filename'])
        
        # Keep the oldest one
        keep_entry = entries[0]
        new_metadata_entries.append(keep_entry)
        
        # Remove the rest
        if len(entries) > 1:
            for duplicate in entries[1:]:
                dup_filename = duplicate['filename']
                dup_path = os.path.join(IMAGES_DIR, dup_filename)
                
                # Double check we are not deleting the file we want to keep
                if dup_filename != keep_entry['filename']:
                    try:
                        if os.path.exists(dup_path):
                            os.remove(dup_path)
                            files_deleted += 1
                    except Exception as e:
                        print(f"Error deleting {dup_filename}: {e}")

    # 5. Write back the deduplicated metadata
    print(f"Writing {len(new_metadata_entries)} unique entries back to metadata.jsonl...")
    with open(METADATA_PATH, 'w') as f:
        for entry in new_metadata_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"\nCleanup Complete!")
    print(f"- Unique images preserved: {len(new_metadata_entries)}")
    print(f"- Duplicate files removed from disk: {files_deleted}")
    print(f"- Metadata entries preserved: {len(new_metadata_entries)}")

if __name__ == "__main__":
    cleanup()
