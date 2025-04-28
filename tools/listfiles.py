#!/usr/bin/env python3
import os
import argparse

def list_files(start_dir, included_exts, onlyfilenames=False, onlyexcludedfilenames=False):
    """Walk directory tree and print files based on processing rules"""
    start_dir = os.path.abspath(start_dir)  # Normalize the path

    for root, dirs, files in os.walk(start_dir, topdown=True):
        # Skip hidden directories and special folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'.git', '.vscode'}]

        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, start_dir)  # Path relative to start_dir

            # Check if file is hidden
            is_hidden = filename.startswith('.')

            # Split filename and extension
            _, ext = os.path.splitext(filename)
            ext = ext.lstrip('.')  # Remove leading dot from extension

            # Determine if file would be included in normal processing
            is_included = not is_hidden and (ext in included_exts or (ext == '' and '' in included_exts))

            # Handle excluded filenames mode
            if onlyexcludedfilenames:
                if not is_included:
                    print(rel_path)
                continue

            # Handle normal filename-only mode
            if onlyfilenames:
                if is_included:
                    print(rel_path)
                continue

            # Skip files that wouldn't be included in normal processing
            if not is_included:
                continue

            # Original content processing
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"{rel_path}")
                    print("=" * 23)
                    lines = content.splitlines()
                    for line in lines:
                        print(line)                    
                    print("=" * 23)
                    print()  # Add empty line between files
            except UnicodeDecodeError:
                content = "[Binary content omitted]"
            except Exception as e:
                content = f"[Error reading file: {str(e)}]"




def valid_directory(path):
    """Argparse validator for directory paths"""
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid directory")
    return path

def main():
    parser = argparse.ArgumentParser(
        description="List files with their content in a structured format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-int', '--include', required=True,
                       help='Comma-separated list of extensions to include (use empty for no extension)')
    parser.add_argument('--dir', type=valid_directory, default='.',
                       help='Base directory to search from')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--onlyfilenames', action='store_true',
                      help='Output only included filenames without content')
    group.add_argument('--onlyexcludedfilenames', action='store_true',
                      help='Output only excluded filenames that would not be processed')

    args = parser.parse_args()
    included_exts = args.include.split(',')

    list_files(args.dir, included_exts, args.onlyfilenames, args.onlyexcludedfilenames)

if __name__ == '__main__':
    main()
