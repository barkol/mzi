#!/usr/bin/env python3
"""
Remove '_converted' suffix from WAV filenames
"""

import os
import sys
import argparse
from pathlib import Path


def remove_converted_suffix(folder_path, dry_run=False, force=False):
    """Remove '_converted' from WAV filenames in the specified folder"""
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        return False
    
    # Find all WAV files with '_converted' in the name
    wav_files = []
    for pattern in ["*_converted*.wav", "*_converted*.WAV"]:
        wav_files.extend(folder.glob(pattern))
    
    # Remove duplicates (in case of case-insensitive filesystems)
    wav_files = list(set(wav_files))
    
    if not wav_files:
        print(f"No WAV files with '_converted' found in {folder_path}")
        return True
    
    print(f"Found {len(wav_files)} file(s) to rename:")
    if dry_run:
        print("(DRY RUN - no files will be changed)\n")
    else:
        print()
    
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    
    for wav_file in sorted(wav_files):
        old_name = wav_file.name
        # Remove '_converted' from the filename
        new_name = old_name.replace('_converted', '')
        
        # If nothing changed, skip
        if old_name == new_name:
            continue
        
        new_path = wav_file.parent / new_name
        
        # Check if target file already exists
        if new_path.exists() and not force:
            print(f"⚠️  SKIP: {old_name}")
            print(f"         Target already exists: {new_name}")
            skipped_count += 1
            continue
        
        # Perform rename (or simulate in dry run)
        try:
            if dry_run:
                print(f"✓ WOULD RENAME: {old_name}")
                print(f"            TO: {new_name}")
            else:
                if new_path.exists() and force:
                    print(f"⚠️  OVERWRITING: {new_name}")
                wav_file.rename(new_path)
                print(f"✓ RENAMED: {old_name}")
                print(f"       TO: {new_name}")
            renamed_count += 1
        except Exception as e:
            print(f"✗ ERROR: Could not rename {old_name}")
            print(f"         {str(e)}")
            error_count += 1
    
    # Summary
    print(f"\n{'DRY RUN ' if dry_run else ''}Summary:")
    print(f"  Files {'would be ' if dry_run else ''}renamed: {renamed_count}")
    if skipped_count > 0:
        print(f"  Files skipped: {skipped_count}")
    if error_count > 0:
        print(f"  Errors: {error_count}")
    
    return error_count == 0


def batch_remove_suffix(folder_path, pattern="_converted", dry_run=False, force=False, recursive=False):
    """More flexible version that can remove any suffix pattern"""
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        return False
    
    # Find all WAV files with the pattern
    if recursive:
        wav_files = []
        for ext in ["*.wav", "*.WAV"]:
            wav_files.extend(folder.rglob(ext))
    else:
        wav_files = list(folder.glob("*.wav")) + list(folder.glob("*.WAV"))
    
    # Filter files that contain the pattern
    matching_files = [f for f in wav_files if pattern in f.stem]
    
    if not matching_files:
        print(f"No WAV files with '{pattern}' found in {folder_path}")
        if recursive:
            print("(searched recursively)")
        return True
    
    print(f"Found {len(matching_files)} file(s) containing '{pattern}':")
    if dry_run:
        print("(DRY RUN - no files will be changed)\n")
    else:
        print()
    
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Group by directory for better output
    files_by_dir = {}
    for f in matching_files:
        if f.parent not in files_by_dir:
            files_by_dir[f.parent] = []
        files_by_dir[f.parent].append(f)
    
    for directory, files in sorted(files_by_dir.items()):
        if recursive and directory != folder:
            print(f"\nDirectory: {directory.relative_to(folder)}/")
        
        for wav_file in sorted(files):
            old_name = wav_file.name
            # Remove the pattern from the filename (only from stem, not extension)
            new_stem = wav_file.stem.replace(pattern, '')
            new_name = new_stem + wav_file.suffix
            
            # If nothing changed, skip
            if old_name == new_name:
                continue
            
            new_path = wav_file.parent / new_name
            
            # Check if target file already exists
            if new_path.exists() and not force:
                print(f"  ⚠️  SKIP: {old_name}")
                print(f"           Target exists: {new_name}")
                skipped_count += 1
                continue
            
            # Perform rename (or simulate in dry run)
            try:
                if dry_run:
                    print(f"  ✓ WOULD RENAME: {old_name} → {new_name}")
                else:
                    if new_path.exists() and force:
                        print(f"  ⚠️  OVERWRITING: {new_name}")
                    wav_file.rename(new_path)
                    print(f"  ✓ RENAMED: {old_name} → {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"  ✗ ERROR: Could not rename {old_name}")
                print(f"           {str(e)}")
                error_count += 1
    
    # Summary
    print(f"\n{'DRY RUN ' if dry_run else ''}Summary:")
    print(f"  Files {'would be ' if dry_run else ''}renamed: {renamed_count}")
    if skipped_count > 0:
        print(f"  Files skipped (already exist): {skipped_count}")
    if error_count > 0:
        print(f"  Errors: {error_count}")
    
    return error_count == 0


def main():
    parser = argparse.ArgumentParser(
        description="Remove '_converted' or other patterns from WAV filenames"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder containing WAV files (default: current directory)"
    )
    parser.add_argument(
        "-p", "--pattern",
        default="_converted",
        help="Pattern to remove from filenames (default: '_converted')"
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process subdirectories recursively"
    )
    
    args = parser.parse_args()
    
    # Warning for force mode
    if args.force and not args.dry_run:
        print(f"WARNING: Force mode enabled. This may overwrite existing files.")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
    
    # Use the more flexible function if custom pattern or recursive
    if args.pattern != "_converted" or args.recursive:
        success = batch_remove_suffix(
            args.folder, 
            args.pattern, 
            args.dry_run, 
            args.force,
            args.recursive
        )
    else:
        success = remove_converted_suffix(args.folder, args.dry_run, args.force)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
