import re
import json

def parse_doc(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    lessons = {}
    current_date = None
    current_content = []

    # Regex to find lines starting with "@ MM-DD"
    date_pattern = re.compile(r'^@\s*(\d{1,2}-\d{1,2})')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = date_pattern.match(line)
        if match:
            # Save previous lesson if exists
            if current_date:
                month = current_date.split('-')[0]
                if month not in lessons:
                    lessons[month] = []
                lessons[month].append({
                    'date': current_date,
                    'content': '\n'.join(current_content).strip()
                })
            
            # Start new lesson
            current_date = match.group(1)
            current_content = []
        else:
            if current_date:
                current_content.append(line)

    # Save the last lessen
    if current_date:
        month = current_date.split('-')[0]
        if month not in lessons:
            lessons[month] = []
        lessons[month].append({
            'date': current_date,
            'content': '\n'.join(current_content).strip()
        })

    return lessons

if __name__ == '__main__':
    result = parse_doc('doc_export.txt')
    print(json.dumps(result, indent=2, ensure_ascii=False))
