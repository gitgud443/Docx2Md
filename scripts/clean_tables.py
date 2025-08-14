from bs4 import BeautifulSoup
import re
import sys

def clean_tables(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # First, handle HTML tables
    html_table_pattern = r'<table>.*?</table>'
    html_tables = re.findall(html_table_pattern, content, re.DOTALL)
    
    for table in html_tables:
        # Parse HTML table
        soup = BeautifulSoup(table, 'html.parser')
        
        # Check if this is a complex table with rowspan or colspan
        has_complex_structure = False
        for tag in soup.find_all(['td', 'th']):
            if tag.has_attr('rowspan') or tag.has_attr('colspan'):
                has_complex_structure = True
                break
        
        if has_complex_structure:
            # For complex tables, keep the HTML format but clean it up
            clean_html = str(soup.prettify())
            content = content.replace(table, clean_html)
            continue
        
        # For simple tables, convert to Markdown
        md_table = []
        
        # Process headers
        headers = []
        for th in soup.find_all('th'):
            headers.append(th.text.strip())
        
        if not headers and soup.find('tr'):
            # If no headers found, use first row as header
            for td in soup.find('tr').find_all('td'):
                headers.append(td.text.strip())
        
        if headers:
            md_table.append('| ' + ' | '.join(headers) + ' |')
            md_table.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
            # Process rows (skip header if we used first row as header)
            start_idx = 1 if soup.find('th') or not soup.find('tr') else 2
            for tr in soup.find_all('tr')[start_idx:]:
                row = []
                for td in tr.find_all('td'):
                    # Preserve line breaks within cells
                    cell_content = td.text.strip().replace('\n', '<br>')
                    row.append(cell_content)
                if row:  # Only add non-empty rows
                    md_table.append('| ' + ' | '.join(row) + ' |')
            
            # Replace HTML table with markdown table
            content = content.replace(table, '\n'.join(md_table))
    
    # Now, fix broken Markdown tables
    # First, find all potential table sections
    table_sections = re.findall(r'(\n\|[^\n]*\|[^\n]*\n\|[\s-]+\|[^\n]*\n(?:\|[^\n]*\|[^\n]*\n)+)', content, re.DOTALL)
    
    for section in table_sections:
        # Check if this is a broken table (header row spans multiple lines)
        lines = section.strip().split('\n')
        
        # Fix header row if it's broken across multiple lines
        if len(lines) >= 2:
            header_parts = []
            i = 0
            
            # Collect all parts of the header until we find the separator row
            while i < len(lines) and not re.match(r'\|\s*[-:]+\s*\|', lines[i]):
                if lines[i].startswith('|') and lines[i].endswith('|'):
                    header_parts.append(lines[i])
                i += 1
            
            if len(header_parts) > 1:
                # We have a multi-line header, let's fix it
                # First, determine the number of columns from the separator row
                if i < len(lines):
                    separator = lines[i]
                    column_count = separator.count('|') - 1
                    
                    # Create a new header row with the right number of columns
                    header_cells = []
                    for part in header_parts:
                        # Extract cells from this part
                        cells = part.strip('|').split('|')
                        header_cells.extend([cell.strip() for cell in cells])
                    
                    # Ensure we have exactly the right number of cells
                    if len(header_cells) >= column_count:
                        header_cells = header_cells[:column_count]
                    else:
                        # Pad with empty cells if needed
                        header_cells.extend([''] * (column_count - len(header_cells)))
                    
                    # Create the new header row
                    new_header = '| ' + ' | '.join(header_cells) + ' |'
                    
                    # Replace the original multi-line header with the new one
                    new_section = new_header + '\n' + '\n'.join(lines[i:])
                    content = content.replace(section, '\n' + new_section + '\n')
    
    # Fix cells with multiple lines
    # Find all Markdown tables again after the previous fixes
    md_table_pattern = r'\n\|[^\n]+\|\n\|[\s-]+\|\n(?:\|[^\n]+\|\n)+'
    md_tables = re.findall(md_table_pattern, content)
    
    for table in md_tables:
        # Split the table into rows
        rows = table.strip().split('\n')
        
        # Get the header and separator rows
        header_row = rows[0]
        separator_row = rows[1]
        
        # Count the number of columns
        column_count = header_row.count('|') - 1
        
        # Process the data rows
        processed_rows = [header_row, separator_row]
        current_row = []
        
        for i in range(2, len(rows)):
            row = rows[i]
            
            # Check if this is a new row or continuation of a cell
            if row.startswith('| ') and row.endswith(' |') and row.count('|') == column_count + 1:
                # This is a new row
                if current_row:
                    processed_rows.append('| ' + ' | '.join(current_row) + ' |')
                    current_row = []
                
                # Extract cell values
                cells = row.strip('| ').split(' | ')
                current_row = cells
            else:
                # This is a continuation of the last cell
                if current_row:
                    current_row[-1] += '<br>' + row.strip()
        
        # Add the last row if there's any
        if current_row:
            processed_rows.append('| ' + ' | '.join(current_row) + ' |')
        
        # Replace the original table with the processed one
        content = content.replace(table, '\n'.join(processed_rows) + '\n')
    
    # Fix checkmarks and special characters
    content = content.replace('|  |', '| ✓ |')
    content = content.replace('| ¹ |', '| ¹ |')
    
    # Fix empty cells in tables
    content = re.sub(r'\|\s+\|', '|  |', content)
    
    # Add proper spacing in table cells
    content = re.sub(r'\|(\S)', '| \1', content)
    content = re.sub(r'(\S)\|', '\1 |', content)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Tables cleaned: {input_file} → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clean_tables.py input_file output_file")
        sys.exit(1)
    
    clean_tables(sys.argv[1], sys.argv[2])
