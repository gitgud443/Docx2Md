import sys
import json
import re

def inject_code_blocks(md_path, json_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    with open(json_path, 'r', encoding='utf-8') as f:
        code_blocks = json.load(f)

    # For every block code, replace the occurences of the @@CODEBLOCK_n@@ marker
    # With the exact exctrated block code between backticks ```
    for i, code_text in enumerate(code_blocks, start=1):
        marker = f'@@CODEBLOCK_{i}@@'
        code_block_md = f"\n```\n{code_text}\n```\n"
        # Replace all the occurences of the marker in the markdown
        md_content = md_content.replace(marker, code_block_md)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"Finished injecting in {md_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python inject_code_blocks_single_marker.py <input_final.md> <codeblocks.json>")
        sys.exit(1)

    inject_code_blocks(sys.argv[1], sys.argv[2])
