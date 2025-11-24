import json
import sys

print('Loading export file...')
with open('full_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Loaded {len(data)} records')

# Count changes
changes = {
    'schools.classroom -> classrooms.classroom': 0,
    'schools.student -> students.student': 0,
}

# Fix model references
for record in data:
    if record['model'] == 'schools.classroom':
        record['model'] = 'classrooms.classroom'
        changes['schools.classroom -> classrooms.classroom'] += 1
    elif record['model'] == 'schools.student':
        record['model'] = 'students.student'
        changes['schools.student -> students.student'] += 1

print('\nChanges made:')
for change, count in changes.items():
    print(f'  {change}: {count} records')

# Write fixed data
print('\nWriting fixed export...')
with open('full_export_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done! Created full_export_fixed.json')
