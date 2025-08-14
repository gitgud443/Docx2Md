#!/usr/bin/env python3

import re
import sys
import os

def fix_image_paths(input_file, output_file):
    # Get the base name of the document (without path and extension)
    base_name = os.path.basename(input_file)
    if base_name.endswith('_sections_fixed.md'):
        base_name = base_name[:-18]  # Remove '_sections_fixed.md'
    elif base_name.endswith('.md'):
        base_name = base_name[:-3]  # Remove '.md'
    
    print(f"Base name for image paths: {base_name}")
    
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Count occurrences of different image formats for debugging
    md_format1 = len(re.findall(r'!\[(.*?)\]\((\.\.)?/images/[^/]+/(.+?)\)', content))
    md_format2 = len(re.findall(r'!\[(.*?)\]\(\.?/?images/[^/]+/(.+?)\)', content))
    html_format = len(re.findall(r'<img src="\.?/?images/[^/]+/(.+?)"', content))
    
    print(f"Found image references: Markdown format 1: {md_format1}, Markdown format 2: {md_format2}, HTML: {html_format}")
    
    # Fix Markdown image references with ../images path
    # Example: ![alt text](../images/doc_name/media/image1.png)
    content = re.sub(
        r'!\[(.*?)\]\((\.\.)?/images/[^/]+/(.+?)\)',
        r'![image](../images/' + base_name + r'/\3)',
        content
    )
    
    # Fix Markdown image references with ./images or images path
    # Example: ![](./images/RAEI-IMN_VPN_interco_v2025.1/media/image3.png)
    content = re.sub(
        r'!\[(.*?)\]\(\.?/?images/[^/]+/(.+?)\)',
        r'![image](../images/' + base_name + r'/\2)',
        content
    )
    
    # Fix HTML image references
    # Example: <img src="./images/doc_name/media/image2.png" ... />
    content = re.sub(
        r'<img src="\.?/?images/[^/]+/(.+?)"([^>]*)>',
        r'<img src="../images/' + base_name + r'/\1"\2>',
        content
    )
    
    # Fix any remaining image paths with output/ prefix
    content = re.sub(
        r'(!\[.*?\]|<img src=")output/images/',
        r'\1../images/',
        content
    )
    
    # Fix any image paths that use &amp; in the directory name
    content = re.sub(
        r'(!\[.*?\]|<img src=")\.\.\/images\/(.+?)&amp;(.+?)\/(.+?)"',
        r'\1../images/\2&\3/\4"',
        content
    )
    
    # Count fixed references for verification
    fixed_refs = len(re.findall(r'!\[.*?\]\(\.\.\/images\/' + re.escape(base_name) + r'\/.*?\)', content))
    fixed_html = len(re.findall(r'<img src="\.\.\/images\/' + re.escape(base_name) + r'\/.*?"', content))
    
    print(f"Fixed image references: Markdown: {fixed_refs}, HTML: {fixed_html}")
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Image paths fixed: {input_file} → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_image_paths.py input_file output_file")
        sys.exit(1)
    
    fix_image_paths(sys.argv[1], sys.argv[2])
