import re
import sys

def fix_section_numbering(input_file, output_file):
    with open(input_file, 'r') as file:
        content = file.read()
    
    # Find section headings with numbers
    pattern = r'^(\d+\.\d+(?:\.\d+)*)\s+(.*)$'
    
    # Format them consistently
    def format_heading(match):
        number = match.group(1)
        title = match.group(2)
        return f"## {number} {title}"
    
    content = re.sub(pattern, format_heading, content, flags=re.MULTILINE)
    
    with open(output_file, 'w') as file:
        file.write(content)
    
    print(f"Section numbering fixed: {input_file} → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_section_numbering.py input_file output_file")
        sys.exit(1)
    
    fix_section_numbering(sys.argv[1], sys.argv[2])
