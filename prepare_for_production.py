#!/usr/bin/env python3

import re
import sys
import os
import shutil
import glob
import argparse

def prepare_for_production(input_file, production_dir):
    """
    Prepare a final markdown file for production by:
    1. Changing image paths to point to a local media folder
    2. Copying the file and its images to the production directory
    """
    # Get the base name of the document (without path and extension)
    base_name = os.path.basename(input_file)
    if base_name.endswith('_final.md'):
        clean_name = base_name[:-9]  # Remove '_final.md'
    elif base_name.endswith('.md'):
        clean_name = base_name[:-3]  # Remove '.md'
    
    print(f"Processing document: {clean_name}")
    
    # Create production directory structure
    doc_prod_dir = os.path.join(production_dir, clean_name)
    media_prod_dir = os.path.join(doc_prod_dir, "media")
    
    os.makedirs(doc_prod_dir, exist_ok=True)
    os.makedirs(media_prod_dir, exist_ok=True)
    
    # Read the content of the markdown file
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find the source media directory
    source_media_dir = os.path.join("images", clean_name, "media")
    if not os.path.exists(source_media_dir):
        print(f"WARNING: Source media directory not found: {source_media_dir}")
        # Try to find it by searching for any reference in the markdown
        media_refs = re.findall(r'!\[.*?\]\((\.\.\/)?images\/([^\/]+)\/media\/', content)
        if media_refs:
            alt_name = media_refs[0][1]
            alt_media_dir = os.path.join("images", alt_name, "media")
            if os.path.exists(alt_media_dir):
                print(f"Found alternative media directory: {alt_media_dir}")
                source_media_dir = alt_media_dir
                clean_name = alt_name  # Update clean_name to match the directory
    
    # Count occurrences of different image formats for debugging
    md_format1 = len(re.findall(r'!\[.*?\]\((\.\.\/)?images\/[^\/]+\/media\/([^)]+)\)', content))
    md_format2 = len(re.findall(r'!\[.*?\]\(\.?/?images\/[^\/]+\/media\/([^)]+)\)', content))
    html_format = len(re.findall(r'<img src="(\.\.\/)?images\/[^\/]+\/media\/([^"]+)"', content))
    
    print(f"Found image references: Markdown: {md_format1 + md_format2}, HTML: {html_format}")
    
    # Fix Markdown image references
    # From: ![image](../images/doc_name/media/image1.png)
    # To:   ![image](media/image1.png)
    content = re.sub(
        r'!\[(.*?)\]\((\.\.\/)?images\/[^\/]+\/media\/([^)]+)\)',
        r'![\1](media/\3)',
        content
    )
    
    # Fix HTML image references
    # From: <img src="../images/doc_name/media/image2.png" ... />
    # To:   <img src="media/image2.png" ... />
    content = re.sub(
        r'<img src="(\.\.\/)?images\/[^\/]+\/media\/([^"]+)"',
        r'<img src="media/\2"',
        content
    )
    
    # Count fixed references for verification
    fixed_md = len(re.findall(r'!\[.*?\]\(media\/[^)]+\)', content))
    fixed_html = len(re.findall(r'<img src="media\/[^"]+"', content))
    
    print(f"Fixed image references: Markdown: {fixed_md}, HTML: {fixed_html}")
    
    # Write the updated content to the production file
    prod_md_file = os.path.join(doc_prod_dir, f"{clean_name}.md")
    with open(prod_md_file, 'w', encoding='utf-8') as file:
        file.write(content)
    
    # Copy all media files to the production media directory
    if os.path.exists(source_media_dir):
        print(f"Source media directory: {source_media_dir}")
        
        # Instead of using glob, use os.listdir() which handles special characters better
        try:
            media_files = [os.path.join(source_media_dir, f) for f in os.listdir(source_media_dir) 
                          if os.path.isfile(os.path.join(source_media_dir, f))]
            
            print(f"Found {len(media_files)} files in media directory")
            
            # Copy each file
            for media_file in media_files:
                dest_file = os.path.join(media_prod_dir, os.path.basename(media_file))
                print(f"Copying: {media_file} -> {dest_file}")
                shutil.copy2(media_file, dest_file)
            
            print(f"Copied {len(media_files)} media files to {media_prod_dir}")
        except Exception as e:
            print(f"Error copying media files: {str(e)}")
    else:
        print(f"ERROR: Media directory not found: {source_media_dir}")
    
    print(f"Production file created: {prod_md_file}")
    return True

def process_directory(input_dir, production_dir):
    """Process all final markdown files in a directory."""
    success_count = 0
    failure_count = 0
    
    # Find all final markdown files
    final_files = glob.glob(os.path.join(input_dir, "*_final.md"))
    
    if not final_files:
        print(f"No final markdown files found in {input_dir}")
        return 0, 0
    
    print(f"Found {len(final_files)} final markdown files to process")
    
    for final_file in final_files:
        try:
            if prepare_for_production(final_file, production_dir):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            print(f"Error processing {final_file}: {str(e)}")
            failure_count += 1
    
    print(f"Processed {success_count + failure_count} files")
    print(f"Success: {success_count}, Failures: {failure_count}")
    
    return success_count, failure_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare markdown files for production.')
    parser.add_argument('--input', '-i', default='output', help='Input directory containing final markdown files')
    parser.add_argument('--output', '-o', default='production', help='Output production directory')
    parser.add_argument('--file', '-f', help='Process a single file instead of a directory')
    
    args = parser.parse_args()
    
    # Create production directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    if args.file:
        if os.path.isfile(args.file) and args.file.endswith('.md'):
            prepare_for_production(args.file, args.output)
        else:
            print(f"Invalid file: {args.file}")
            sys.exit(1)
    else:
        process_directory(args.input, args.output)
