import json

print('Loading fixed export file...')
with open('full_export_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Original records: {len(data)}')

# Exclude notification models to avoid conflicts with signal-generated notifications
excluded_models = ['notifications.notification', 'notifications.usernotification']
clean_data = [record for record in data if record['model'] not in excluded_models]

print(f'After excluding notifications: {len(clean_data)}')
print(f'Removed: {len(data) - len(clean_data)} notification records')

# Write clean export
print('Writing clean export...')
with open('full_export_clean.json', 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, ensure_ascii=False, indent=2)

print('Done! Created full_export_clean.json')
