#!/usr/bin/env python3

import re
import sys
import os

def debug_toc(input_file):
    print(f"Debugging TOC in file: {input_file}")
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} does not exist")
        return
    
    # Read the file content
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(input_file, 'r', encoding='latin-1') as file:
            content = file.read()
    
    print(f"File size: {len(content)} characters")
    
    # Find the "Contents" section
    contents_match = re.search(r'(?:^|\n)Contents\s*(?:\n|$)', content)
    
    if not contents_match:
        print("Error: No 'Contents' section found")
        return
    
    toc_start = contents_match.start()
    print(f"TOC starts at position: {toc_start}")
    
    # Find the end of the TOC by looking for the copyright notice
    copyright_match = re.search(r'Copyright © Orange Business Services', content[toc_start:])
    
    if copyright_match:
        toc_end = toc_start + copyright_match.start()
        print(f"TOC ends at position: {toc_end} (found copyright notice)")
    else:
        print("Warning: No copyright notice found to mark end of TOC")
        # If no copyright notice, look for other potential end markers
        
        # Look for a line that doesn't match TOC patterns after a reasonable number of lines
        lines = content[toc_start:].split('\n')
        end_idx = 0
        
        for i, line in enumerate(lines):
            if i > 5:  # Skip the header and first few lines
                line = line.strip()
                if line and not re.match(r'^\d+(\.\d+)*\s+\S+', line) and not line.startswith('ANNEX'):
                    end_idx = i
                    print(f"Potential TOC end at line {i}: '{line}'")
                    break
        
        if end_idx == 0:
            end_idx = 100  # Limit to 100 lines if no clear end is found
            print("No clear end of TOC found, using first 100 lines")
        
        toc_end = toc_start + sum(len(line) + 1 for line in lines[:end_idx])
        print(f"TOC ends at position: {toc_end}")
    
    # Extract the TOC content
    toc_text = content[toc_start:toc_end]
    
    # Save the raw TOC to a file for inspection
    with open("raw_toc.txt", "w", encoding="utf-8") as f:
        f.write(toc_text)
    print("Raw TOC saved to 'raw_toc.txt'")
    
    # Print the TOC content with line numbers and character codes
    print("\nTOC Content with line numbers and character codes:")
    lines = toc_text.split('\n')
    for i, line in enumerate(lines):
        print(f"Line {i}: '{line}'")
        if line:
            print(f"  Char codes: {[ord(c) for c in line[:20]]}{' ...' if len(line) > 20 else ''}")
    
    # Try to process each line
    print("\nTrying to process each line:")
    for i, line in enumerate(lines[1:], 1):  # Skip the "Contents" header
        line = line.strip()
        if not line:
            print(f"Line {i}: [Empty line]")
            continue
        
        print(f"\nLine {i}: '{line}'")
        
        # For ANNEX entries
        if line.startswith('ANNEX'):
            print(f"  Detected as ANNEX entry")
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                annex_num = parts[0]
                rest = parts[1]
                print(f"  ANNEX number: '{annex_num}'")
                print(f"  Rest: '{rest}'")
                
                # Extract page number if present
                rest_parts = rest.rsplit(' ', 1)
                if len(rest_parts) == 2 and rest_parts[1].isdigit():
                    title = rest_parts[0]
                    page = rest_parts[1]
                    print(f"  Title: '{title}'")
                    print(f"  Page: {page}")
                else:
                    print(f"  Could not extract page number")
            else:
                print(f"  Could not split ANNEX entry by ' - '")
            continue
        
        # For regular entries
        # Try different patterns
        
        # Pattern 1: section number + title + page number
        match1 = re.match(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)$', line)
        if match1:
            section_num = match1.group(1)
            title = match1.group(2)
            page = match1.group(3)
            print(f"  Pattern 1 match:")
            print(f"    Section: '{section_num}'")
            print(f"    Title: '{title}'")
            print(f"    Page: {page}")
            
            # Create anchor
            anchor = title.lower().replace(' ', '-').replace('–', '-')
            anchor = re.sub(r'[^\w\-]', '', anchor)
            print(f"    Anchor: #{anchor}")
            
            # Calculate indentation
            indent_level = section_num.count('.')
            print(f"    Indent level: {indent_level}")
            
            # Create Markdown link
            markdown_link = f"{'  ' * indent_level}* [{section_num} {title}](#{anchor})"
            print(f"    Markdown link: {markdown_link}")
            continue
        
        # Pattern 2: section number + title (no page number)
        match2 = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line)
        if match2:
            section_num = match2.group(1)
            rest = match2.group(2)
            print(f"  Pattern 2 match:")
            print(f"    Section: '{section_num}'")
            print(f"    Rest: '{rest}'")
            
            # Try to extract page number from the end
            rest_parts = rest.rsplit(' ', 1)
            if len(rest_parts) == 2 and rest_parts[1].isdigit():
                title = rest_parts[0]
                page = rest_parts[1]
                print(f"    Title: '{title}'")
                print(f"    Page: {page}")
            else:
                print(f"    Could not extract page number, using entire rest as title")
                title = rest
            
            # Create anchor
            anchor = title.lower().replace(' ', '-').replace('–', '-')
            anchor = re.sub(r'[^\w\-]', '', anchor)
            print(f"    Anchor: #{anchor}")
            
            # Calculate indentation
            indent_level = section_num.count('.')
            print(f"    Indent level: {indent_level}")
            
            # Create Markdown link
            markdown_link = f"{'  ' * indent_level}* [{section_num} {title}](#{anchor})"
            print(f"    Markdown link: {markdown_link}")
            continue
        
        print("  No pattern match!")
        
        # Try to extract any numbers at the beginning
        num_match = re.match(r'^(\d+)', line)
        if num_match:
            print(f"  Found number at beginning: {num_match.group(1)}")
        
        # Check for special characters
        special_chars = [c for c in line if ord(c) > 127]
        if special_chars:
            print(f"  Contains special characters: {special_chars}")
        
        # Check for invisible characters
        invisible_chars = [c for c in line if ord(c) < 32 and c != '\t']
        if invisible_chars:
            print(f"  Contains invisible characters: {[ord(c) for c in invisible_chars]}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_toc.py input_file")
        sys.exit(1)
    
    debug_toc(sys.argv[1])
