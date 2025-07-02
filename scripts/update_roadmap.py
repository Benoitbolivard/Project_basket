import os
import re

ROADMAP_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ROADMAP.md')

def main():
    tags_env = os.getenv('COMPLETED_TAGS', '')
    if not tags_env:
        return
    tags = [t.strip() for t in tags_env.split(',') if t.strip()]
    if not tags:
        return

    with open(ROADMAP_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        updated = False
        for tag in tags:
            pattern = rf'^- \[ \] <!--TASK:{re.escape(tag)}-->(.*)$'
            m = re.match(pattern, line)
            if m:
                desc = m.group(1).strip()
                line = f"- [x] <!--TASK:{tag}-->~~{desc}~~\n"
                updated = True
                break
        updated_lines.append(line)

    with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

if __name__ == '__main__':
    main()
