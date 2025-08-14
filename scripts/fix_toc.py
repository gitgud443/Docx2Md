#!/usr/bin/env python3

import re
import sys

DEBUG = False  # Set to True for debugging

def compile_patterns(patterns):
    return [re.compile(p, re.IGNORECASE) for p in patterns]

def find_toc_header(content, toc_patterns):
    for pattern in toc_patterns:
        match = pattern.search(content)
        if match:
            toc_start = match.start()
            toc_header = match.group(0).strip()
            if DEBUG:
                print(f"Found TOC header: '{toc_header}' at position {toc_start}")
            return toc_start, toc_header
    return -1, ""

def aggressive_toc_search(content):
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Remove formatting chars for matching
        clean_line = re.sub(r'[*_<>/]', '', line)
        if re.search(r'(?i)table\s+of\s+contents?|contents?', clean_line):
            toc_entries = 0
            for j in range(i+1, min(i+6, len(lines))):
                if re.search(r'\[.*\]\(#.*\)', lines[j]):
                    toc_entries += 1
            if toc_entries >= 2:
                toc_start = sum(len(l) + 1 for l in lines[:i])
                toc_header = line
                if DEBUG:
                    print(f"Found TOC header (aggressive): '{toc_header}' at position {toc_start}")
                return toc_start, toc_header
    return -1, ""

def find_toc_end(content, toc_start, toc_header):
    rest_of_content = content[toc_start:]

    # Clean TOC header text for comparison
    toc_header_text = re.sub(r'[#>*_\s]', '', toc_header).lower()

    # Find next top-level header (# Header) that is NOT the TOC header itself
    next_heading_match = None
    for match in re.finditer(r'\n#\s+(.+)', rest_of_content):
        header_text = match.group(1).strip().lower()
        header_text_clean = re.sub(r'[#>*_\s]', '', header_text)
        if header_text_clean != toc_header_text:
            next_heading_match = match
            if DEBUG:
                print(f"Next heading after TOC found: '{header_text}' at position {match.start()}")
            break

    table_start_match = re.search(r'<table', rest_of_content)

    if next_heading_match and (not table_start_match or next_heading_match.start() < table_start_match.start()):
        toc_end = toc_start + next_heading_match.start()
        if DEBUG:
            print(f"TOC end set at next heading position: {toc_end}")
        return toc_end
    elif table_start_match:
        content_before_table = rest_of_content[:table_start_match.start()]
        blank_line_before_table = re.search(r'\n\s*\n\s*$', content_before_table)
        if blank_line_before_table:
            toc_end = toc_start + blank_line_before_table.start() + 1
        else:
            toc_end = toc_start + table_start_match.start()
        if DEBUG:
            print(f"TOC end set at table start position: {toc_end}")
        return toc_end
    else:
        # Fallback approach
        lines = rest_of_content.split('\n')
        i = 1  # skip TOC header line
        toc_entries_found = 0
        consecutive_non_toc = 0
        max_consecutive_non_toc = 3
        min_toc_entries = 5
        section_headers = ["Table of figures", "List of tables", "References", "references", "Reference", "reference"]
        in_secondary_toc = False

        while i < len(lines):
            line = lines[i].strip()

            if any(header in line for header in section_headers):
                in_secondary_toc = True
                toc_entries_found = 0
                consecutive_non_toc = 0
                i += 1
                continue

            is_toc_entry = (
                re.match(r'^\[.*\]\(#.*\)$', line) or
                re.search(r'<span[^>]*>.*</span>.*\[.*\]\(#.*\)', line) or
                re.match(r'^\d+(?:\.\d+)*\.?\s+[^[]+\s+\[.*\]\(#.*\)', line) or
                re.match(r'^\d+(?:\.\d+)*\.?\s+.+?(?:\s+\d+)?$', line) or
                re.search(r'\[.*\]\(#.*\)', line) or
                re.match(r'^\s*\*\s+\[.*\]\(#.*\)', line) or
                line.startswith('>')
            )

            is_table_start = "<table" in line

            if is_table_start:
                if DEBUG:
                    print(f"TOC end found at table start line {i}")
                break

            if is_toc_entry or not line or (in_secondary_toc and line in section_headers):
                if is_toc_entry:
                    toc_entries_found += 1
                consecutive_non_toc = 0
            else:
                consecutive_non_toc += 1
                if toc_entries_found >= min_toc_entries and consecutive_non_toc >= max_consecutive_non_toc and not in_secondary_toc:
                    if DEBUG:
                        print(f"TOC end found at line {i} due to consecutive non-TOC lines")
                    break

            i += 1

        if toc_entries_found < min_toc_entries and not in_secondary_toc:
            if DEBUG:
                print(f"Warning: Not enough TOC entries found (found {toc_entries_found}, need {min_toc_entries})")
            return None

        if i < 10 and not is_table_start:
            if DEBUG:
                print(f"Warning: TOC appears very short, using fallback method")
            paragraph_break = re.search(r'\n\s*\n', rest_of_content[100:])
            if paragraph_break:
                toc_end = toc_start + 100 + paragraph_break.start() + 1
            else:
                toc_end = toc_start + int(len(rest_of_content) * 0.2)
        else:
            toc_end = toc_start + sum(len(line) + 1 for line in lines[:i])

        if DEBUG:
            print(f"TOC end determined at position {toc_end}")
        return toc_end

def clean_strikethrough(line):
    return re.sub(r'~~|<span[^>]*>~~|~~</span>', '', line)

def parse_external_url(line, has_strikethrough):
    # Example: [1 [QFX5120 Juniper switch - Hardware agreement](https://kmlibraries...)](...)
    match = re.match(r'^\[(\d+(?:\.\d+)*\.?)\s+\[(.*?)\]\((https?://[^)]+)\)\]\(.*\)$', line)
    if not match:
        return None
    section_num = match.group(1).rstrip('.')
    title = match.group(2).strip()
    url = match.group(3)
    indent_level = section_num.count('.')
    indent = "  " * indent_level
    if has_strikethrough:
        return f"{indent}* [~~{section_num} {title}~~]({url})"
    else:
        return f"{indent}* [{section_num} {title}]({url})"

def parse_span_in_link(line, has_strikethrough):
    # Example: [<span class="mark">7. Preparation to the merge RBCI/RAEI</span> [40](#preparation-to-the-merge-rbciraei)](#preparation-to-the-merge-rbciraei)
    match = re.match(r'^\[\s*<span[^>]*>([^<]+)</span>\s*\[(\d+)\]\((#[^)]+)\)\s*\]\((#[^)]+)\)$', line)
    if not match:
        return None
    link_text = match.group(1).strip()
    anchor = match.group(4)
    if re.match(r'(?i)table\s+of\s+content|table\s+des\s+matières', link_text) or link_text.lower() in ["contents", "content"]:
        return None
    section_match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.+)$', link_text)
    if section_match:
        section_num = section_match.group(1).rstrip('.')
        title = section_match.group(2).strip()
        indent_level = section_num.count('.')
        indent = "  " * indent_level
        if has_strikethrough:
            return f"{indent}* [~~{section_num} {title}~~]({anchor})"
        else:
            return f"{indent}* [{section_num} {title}]({anchor})"
    else:
        if has_strikethrough:
            return f"* [~~{link_text}~~]({anchor})"
        else:
            return f"* [{link_text}]({anchor})"

def parse_figure_link(line, has_strikethrough):
    # Example: [Figure 1: Physical Architecture during migration [8](#_Toc105709552)](#_Toc105709552)
    match = re.match(r'^\[((?:Figure|Table|Fig\.|Tab\.)\s+\d+:?\s+[^[]+)\s+\[\d+\]\((#[^)]+)\)\]\((#[^)]+)\)$', line)
    if not match:
        return None
    figure_text = match.group(1).strip()
    anchor = match.group(2)
    if has_strikethrough:
        return f"* [~~{figure_text}~~]({anchor})"
    else:
        return f"* [{figure_text}]({anchor})"

def parse_simple_markdown_link(line, has_strikethrough):
    # Example: [1 References [6](#references)](#references)
    match = re.match(r'^\[(.*)\]\((#.*)\)$', line)
    if not match:
        return None
    link_text = match.group(1)
    anchor = match.group(2)
    if re.match(r'(?i)table\s+of\s+content', link_text) or link_text.lower() in ["contents", "content"]:
        return None
    clean_link_text = re.sub(r'\s*\[\d+\]\(#[^)]+\)', '', link_text)
    span_match = re.search(r'<span[^>]*>(\d+(?:\.\d+)*\.?)</span>\s+<span[^>]*>([^<]+)</span>', clean_link_text)
    if span_match:
        section_num = span_match.group(1).rstrip('.')
        title = span_match.group(2).strip()
        indent_level = section_num.count('.')
        indent = "  " * indent_level
        if has_strikethrough:
            return f"{indent}* [~~{section_num} {title}~~]({anchor})"
        else:
            return f"{indent}* [{section_num} {title}]({anchor})"
    section_match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.*?)$', clean_link_text)
    if section_match:
        section_num = section_match.group(1).rstrip('.')
        title = section_match.group(2).strip()
        indent_level = section_num.count('.')
        indent = "  " * indent_level
        if has_strikethrough:
            return f"{indent}* [~~{section_num} {title}~~]({anchor})"
        else:
            return f"{indent}* [{section_num} {title}]({anchor})"
    clean_link_text = re.sub(r'<span[^>]*>|</span>', '', clean_link_text)
    if has_strikethrough:
        return f"* [~~{clean_link_text}~~]({anchor})"
    else:
        return f"* [{clean_link_text}]({anchor})"

def parse_span_link(line, has_strikethrough):
    # Example: <span class="mark">2</span> <span class="mark">Introduction</span> [7](#introduction)
    match = re.match(r'<span[^>]*>(\d+(?:\.\d+)*\.?)</span>\s+<span[^>]*>([^<]+)</span>\s+\[(\d+)\]\((#[^)]+)\)', line)
    if not match:
        return None
    section_num = match.group(1).rstrip('.')
    title = match.group(2).strip()
    anchor = match.group(4)
    indent_level = section_num.count('.')
    indent = "  " * indent_level
    if has_strikethrough:
        return f"{indent}* [~~{section_num} {title}~~]({anchor})"
    else:
        return f"{indent}* [{section_num} {title}]({anchor})"

def parse_plain_link(line, has_strikethrough):
    # Example: 7 IP Addressing [40](#ip-addressing)
    match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+([^[]+)\s+\[(\d+)\]\((#[^)]+)\)$', line)
    if not match:
        return None
    section_num = match.group(1).rstrip('.')
    title = match.group(2).strip()
    anchor = match.group(4)
    indent_level = section_num.count('.')
    indent = "  " * indent_level
    if has_strikethrough:
        return f"{indent}* [~~{section_num} {title}~~]({anchor})"
    else:
        return f"{indent}* [{section_num} {title}]({anchor})"

def parse_plain_text(line, has_strikethrough):
    # Example: 1 References 6
    match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.+?)(?:\s+(\d+))?$', line)
    if not match:
        return None
    section_num = match.group(1).rstrip('.')
    title = match.group(2).strip()
    if title.lower() in ["contents", "content"]:
        return None
    anchor = title.lower().replace(' ', '-').replace('[', '').replace(']', '')
    anchor = re.sub(r'[^\w\-]', '', anchor)
    indent_level = section_num.count('.')
    indent = "  " * indent_level
    if has_strikethrough:
        return f"{indent}* [~~{section_num} {title}~~](#{anchor})"
    else:
        return f"{indent}* [{section_num} {title}](#{anchor})"

def parse_link_in_text(line, has_strikethrough):
    match = re.search(r'\[([^\]]+)\]\((#[^)]+)\)', line)
    if not match:
        return None
    link_text = match.group(1)
    anchor = match.group(2)
    if re.match(r'(?i)table\s+of\s+content', link_text) or link_text.lower() in ["contents", "content"]:
        return None
    clean_link_text = re.sub(r'\s*\[\d+\]\(#[^)]+\)', '', link_text)
    clean_link_text = re.sub(r'<span[^>]*>|</span>', '', clean_link_text)
    section_match = re.match(r'^(?:<span[^>]*>)?(\d+(?:\.\d+)*\.?)(?:</span>)?(?:\s+|$)', line)
    if not section_match:
        section_match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+', clean_link_text)
    if section_match:
        section_num = section_match.group(1).rstrip('.')
        title_match = re.match(r'^\d+(?:\.\d+)*\.?\s+(.+)$', clean_link_text)
        title = title_match.group(1) if title_match else clean_link_text
        indent_level = section_num.count('.')
        indent = "  " * indent_level
        if has_strikethrough:
            return f"{indent}* [~~{section_num} {title}~~]({anchor})"
        else:
            return f"{indent}* [{section_num} {title}]({anchor})"
    else:
        if has_strikethrough:
            return f"* [~~{clean_link_text}~~]({anchor})"
        else:
            return f"* [{clean_link_text}]({anchor})"

def fix_toc(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    toc_patterns = [
        # Standard headers
        r'(?:^|\n)#+\s*[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?\s*(?:\n|$)',
        r'(?:^|\n)#+\s*[Cc]ontent(?:s)?\s*(?:\n|$)',
        r'(?:^|\n)#+\s*[Tt]able\s*[Dd]es\s*[Mm]atière(?:s)?\s*(?:\n|$)',
        r'(?:^|\n)[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?\s*(?:\n|$)',
        r'(?:^|\n)[Cc]ontent(?:s)?\s*(?:\n|$)',
        r'(?:^|\n)[Tt]able\s*[Dd]es\s*[Mm]atière(?:s)?\s*(?:\n|$)',

        # Quote format
        r'(?:^|\n)>\s*[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?\s*(?:\n|$)',
        r'(?:^|\n)>\s*[Cc]ontent(?:s)?\s*(?:\n|$)',

        # Bold format
        r'(?:^|\n)\*\*[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?\*\*\s*(?:\n|$)',
        r'(?:^|\n)\*\*[Cc]ontent(?:s)?\*\*\s*(?:\n|$)',
        r'(?:^|\n)__[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?__\s*(?:\n|$)',
        r'(?:^|\n)__[Cc]ontent(?:s)?__\s*(?:\n|$)',

        # Italic format
        r'(?:^|\n)\*[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?\*\s*(?:\n|$)',
        r'(?:^|\n)\*[Cc]ontent(?:s)?\*\s*(?:\n|$)',
        r'(?:^|\n)_[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?_\s*(?:\n|$)',
        r'(?:^|\n)_[Cc]ontent(?:s)?_\s*(?:\n|$)',

        # Bold and italic
        r'(?:^|\n)\*\*\*[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?\*\*\*\s*(?:\n|$)',
        r'(?:^|\n)\*\*\*[Cc]ontent(?:s)?\*\*\*\s*(?:\n|$)',
        r'(?:^|\n)___[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?___\s*(?:\n|$)',
        r'(?:^|\n)___[Cc]ontent(?:s)?___\s*(?:\n|$)',

        # HTML formats
        r'(?:^|\n)<strong>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</strong>\s*(?:\n|$)',
        r'(?:^|\n)<strong>[Cc]ontent(?:s)?</strong>\s*(?:\n|$)',
        r'(?:^|\n)<b>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</b>\s*(?:\n|$)',
        r'(?:^|\n)<b>[Cc]ontent(?:s)?</b>\s*(?:\n|$)',
        r'(?:^|\n)<em>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</em>\s*(?:\n|$)',
        r'(?:^|\n)<em>[Cc]ontent(?:s)?</em>\s*(?:\n|$)',
        r'(?:^|\n)<i>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</i>\s*(?:\n|$)',
        r'(?:^|\n)<i>[Cc]ontent(?:s)?</i>\s*(?:\n|$)',
        r'(?:^|\n)<u>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</u>\s*(?:\n|$)',
        r'(?:^|\n)<u>[Cc]ontent(?:s)?</u>\s*(?:\n|$)',

        # Combinations of HTML formats
        r'(?:^|\n)<strong><em>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</em></strong>\s*(?:\n|$)',
        r'(?:^|\n)<strong><em>[Cc]ontent(?:s)?</em></strong>\s*(?:\n|$)',
        r'(?:^|\n)<em><strong>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</strong></em>\s*(?:\n|$)',
        r'(?:^|\n)<em><strong>[Cc]ontent(?:s)?</strong></em>\s*(?:\n|$)',
        r'(?:^|\n)<b><i>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</i></b>\s*(?:\n|$)',
        r'(?:^|\n)<b><i>[Cc]ontent(?:s)?</i></b>\s*(?:\n|$)',
        r'(?:^|\n)<i><b>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</b></i>\s*(?:\n|$)',
        r'(?:^|\n)<i><b>[Cc]ontent(?:s)?</b></i>\s*(?:\n|$)',

        # Underlined combinations
        r'(?:^|\n)<u><strong>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</strong></u>\s*(?:\n|$)',
        r'(?:^|\n)<u><strong>[Cc]ontent(?:s)?</strong></u>\s*(?:\n|$)',
        r'(?:^|\n)<u><em>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</em></u>\s*(?:\n|$)',
        r'(?:^|\n)<u><em>[Cc]ontent(?:s)?</em></u>\s*(?:\n|$)',
        r'(?:^|\n)<u><strong><em>[Tt]able\s*[Oo]f\s*[Cc]ontent(?:s)?</em></strong></u>\s*(?:\n|$)',
        r'(?:^|\n)<u><strong><em>[Cc]ontent(?:s)?</em></strong></u>\s*(?:\n|$)',
    ]

    toc_patterns_compiled = compile_patterns(toc_patterns)

    toc_start, toc_header = find_toc_header(content, toc_patterns_compiled)

    if toc_start == -1:
        toc_start, toc_header = aggressive_toc_search(content)

    if toc_start == -1:
        print(f"TOC ERROR : No table of contents found in {input_file}")
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        return

    toc_end = find_toc_end(content, toc_start, toc_header)
    if toc_end is None:
        # Not enough TOC entries found or other issue
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        return

    toc_content = content[toc_start:toc_end]

    if DEBUG:
        print(f"Extracted TOC content ({toc_end - toc_start} chars):")
        print(toc_content[:200] + "..." if len(toc_content) > 200 else toc_content)

    new_toc = ["## Table of Contents", ""]

    lines = toc_content.split('\n')

    # Skip header and empty lines or quote lines
    start_idx = 1
    while start_idx < len(lines) and (
        not lines[start_idx].strip() or
        re.search(r'(?i)table\s+of\s+content', re.sub(r'[*_<>/]', '', lines[start_idx].strip())) or
        re.sub(r'[*_<>/]', '', lines[start_idx].strip()).lower() in ["contents", "content"] or
        lines[start_idx].strip().startswith('>')
    ):
        start_idx += 1

    for i in range(start_idx, len(lines)):
        line = lines[i].strip()

        if line.startswith('>'):
            line = line[1:].strip()

        if not line:
            continue

        if re.search(r'(?i)\[(?:table\s+of\s+content|content)\s+\[\d+\]', line):
            continue

        if re.match(r'^#+\s+\d+(?:\.\d+)*\.?\s+', line):
            continue

        has_strikethrough = "~~" in line or '<span class="mark">~~' in line
        clean_line = clean_strikethrough(line)

        # Try each parser in order
        parsed_line = (
            parse_external_url(clean_line, has_strikethrough) or
            parse_span_in_link(clean_line, has_strikethrough) or
            parse_figure_link(clean_line, has_strikethrough) or
            parse_simple_markdown_link(clean_line, has_strikethrough) or
            parse_span_link(clean_line, has_strikethrough) or
            parse_plain_link(clean_line, has_strikethrough) or
            parse_plain_text(clean_line, has_strikethrough) or
            parse_link_in_text(clean_line, has_strikethrough)
        )

        if parsed_line:
            new_toc.append(parsed_line)

    if len(new_toc) <= 2:
        print(f"Warning: No TOC entries found in {input_file}")
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        return

    new_toc_text = '\n'.join(new_toc) + "\n\n"

    new_content = content[:toc_start] + new_toc_text + content[toc_end:]

    # Fix multiple TOC headers
    new_content = re.sub(r'(?i)## Table of Contents\s*\n\s*#\s*Contents?', '## Table of Contents', new_content)
    new_content = re.sub(r'(?i)## Table of Contents\s*\n\s*#\s*Table of Contents?', '## Table of Contents', new_content)

    # Clean up messy links
    new_content = re.sub(r'\[((?:Figure|Table|Fig\.|Tab\.)\s+\d+:?\s+[^[]+)\s+\[\d+\]\((#[^)]+)\)\]\((#[^)]+)\)', r'[\1](\2)', new_content)
    new_content = re.sub(r'\[(\d+(?:\.\d+)*\.?)\s+\[(.*?)\]\((https?://[^)]+)\)\]\(.*\)', r'[\1 \2](\3)', new_content)
    new_content = re.sub(r'\[(.*?)\s+\[\d+\]\((#[^)]+)\)\]\((#[^)]+)\)', r'[\1](\3)', new_content)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(new_content)

    print(f"Table of contents fixed: {input_file} → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_toc.py input_file output_file")
        sys.exit(1)

    fix_toc(sys.argv[1], sys.argv[2])
