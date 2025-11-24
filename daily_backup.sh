#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/autograder-system/backups"
mkdir -p $BACKUP_DIR

# PostgreSQL dump
docker exec autograder-system-db-1 pg_dump -U autograder_user autograder_db > $BACKUP_DIR/postgres_$DATE.sql

# Django dumpdata
docker exec autograder-system-backend-1 python manage.py dumpdata --indent=2 > $BACKUP_DIR/django_$DATE.json

# Keep only last 30 days
find $BACKUP_DIR -name 'postgres_*.sql' -mtime +30 -delete
find $BACKUP_DIR -name 'django_*.json' -mtime +30 -delete

echo "Backup completed: $DATE"
