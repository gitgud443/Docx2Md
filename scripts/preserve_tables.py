#!/usr/bin/env python3

import re
import sys
from bs4 import BeautifulSoup

def preserve_tables(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find HTML tables in the content
    html_table_pattern = r'<table>.*?</table>'
    html_tables = re.findall(html_table_pattern, content, re.DOTALL)
    
    # We'll keep track of tables we've processed to avoid duplicates
    processed_tables = set()
    
    for table in html_tables:
        if table in processed_tables:
            continue
        
        # Keep the table exactly as is, just ensure it has proper spacing
        content = content.replace(table, '\n\n' + table + '\n\n')
        processed_tables.add(table)
    
    # Convert Markdown tables to HTML
    md_table_pattern = r'(\n\|[^\n]+\|\n\|[\s-]+\|\n(?:\|[^\n]+\|\n)+)'
    md_tables = re.findall(md_table_pattern, content)
    
    for table in md_tables:
        if table in processed_tables:
            continue
        
        # Convert to HTML table
        rows = table.strip().split('\n')
        
        html_table = ['<table>', '<thead>', '<tr>']
        
        # Process header
        header_cells = rows[0].strip('|').split('|')
        for cell in header_cells:
            html_table.append(f'<th>{cell.strip()}</th>')
        
        html_table.append('</tr>')
        html_table.append('</thead>')
        html_table.append('<tbody>')
        
        # Process data rows
        for i, row in enumerate(rows[2:]):  # Skip header and separator
            # Alternate row classes for zebra striping
            row_class = 'odd' if i % 2 == 0 else 'even'
            html_table.append(f'<tr class="{row_class}">')
            
            cells = row.strip('|').split('|')
            for cell in cells:
                # Keep cell content as is, just strip whitespace
                cell_content = cell.strip()
                
                # Handle line breaks in cells
                cell_content = cell_content.replace('<br>', '<br/>')
                
                html_table.append(f'<td>{cell_content}</td>')
            html_table.append('</tr>')
        
        html_table.append('</tbody>')
        html_table.append('</table>')
        
        # Replace the Markdown table with HTML
        content = content.replace(table, '\n\n' + '\n'.join(html_table) + '\n\n')
        processed_tables.add(table)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Tables preserved as HTML: {input_file} → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python preserve_tables.py input_file output_file")
        sys.exit(1)
    
    preserve_tables(sys.argv[1], sys.argv[2])
