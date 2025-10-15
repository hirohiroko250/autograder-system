#!/bin/bash
# Database backup script for autograder system
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/autograder-system/backups"
mkdir -p $BACKUP_DIR

# Backup production database
docker exec autograder-system-backend-1 python manage.py dumpdata --settings=autograder.settings_production --indent=2 > $BACKUP_DIR/backup_$DATE.json

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.json" -mtime +7 -delete

echo "Database backup completed: backup_$DATE.json"
