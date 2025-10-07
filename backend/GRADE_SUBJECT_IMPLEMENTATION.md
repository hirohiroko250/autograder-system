# Grade-Based Subject Selection Implementation

## Overview
Successfully implemented grade-based subject selection to support both elementary (小学生) and middle school (中学生) students with their respective subjects.

## Subject Distribution
- **小学生 (Elementary)**: 国語 (Japanese) and 算数 (Math)
- **中学生 (Middle School)**: 英語 (English) and 数学 (Mathematics)

## Changes Made

### 1. Model Updates (`tests/models.py`)
- Added `grade_level` field to `TestDefinition` model
- Defined subject constants for each grade level:
  - `ELEMENTARY_SUBJECTS`: Japanese (国語), Math (算数)
  - `MIDDLE_SCHOOL_SUBJECTS`: English (英語), Mathematics (数学)
- Added `GRADE_LEVELS` choices: Elementary (小学生), Middle School (中学生)
- Updated unique constraint to include `grade_level`
- Added validation in `clean()` method to ensure valid grade-subject combinations
- Added `get_subjects_for_grade()` class method for dynamic subject filtering

### 2. Admin Interface Enhancements (`autograder/admin.py`)
- Created `TestDefinitionForm` with dynamic subject filtering based on grade selection
- Updated admin list display to show grade level
- Added grade_level to list filters and fieldsets
- Enhanced fieldset descriptions to guide users

### 3. JavaScript Enhancements (`static/admin/js/test_definition.js`)
- Added `addGradeBasedSubjectSelection()` function
- Dynamic subject dropdown filtering based on grade level selection
- Real-time UI updates when grade level changes
- Maintains selected subject when appropriate

### 4. API Updates (`tests/views.py`)
- Updated `TestDefinitionViewSet` to include `grade_level` filtering
- Added `grade_level` and `grade_level_display` to API responses
- Removed hardcoded subject filtering to support all grade levels
- Added `subjects_for_grade` endpoint for dynamic subject retrieval
- Updated serializers to include grade level information

### 5. Utility Functions (`scores/utils.py`)
- Updated all functions to support optional `grade_level` parameter:
  - `get_test_template_structure()`
  - `generate_score_template()`
  - `import_scores_from_excel()`
  - `calculate_and_save_test_summary()`
  - `get_test_summary()`
- Enhanced subject display mapping to include English and Mathematics
- Updated error messages to include grade level information

### 6. Database Migration
- Created migration `0008_remove_testdefinition_test_defini_schedul_ad7b2d_idx_and_more.py`
- Added `grade_level` field with default value 'elementary'
- Updated unique constraints and indexes

## Validation Logic
The system enforces strict validation rules:
- Elementary students can only select Japanese (国語) or Math (算数)
- Middle school students can only select English (英語) or Mathematics (数学)
- Cross-grade subject selection is prevented with clear error messages

## API Endpoints
### New Endpoint
- `GET /api/tests/subjects_for_grade/?grade_level=elementary`
  - Returns available subjects for specified grade level
  - Response includes grade level display name and subject options

### Updated Endpoints
- All existing endpoints now support `grade_level` filtering
- API responses include grade level information

## Frontend Integration
The system is fully prepared for frontend integration:
- Dynamic subject filtering based on grade selection
- Comprehensive API endpoints for all grade-subject combinations
- Proper validation and error handling
- Japanese localization throughout

## Testing
Comprehensive test suite confirms:
- ✅ Grade-subject mapping works correctly
- ✅ Validation logic prevents invalid combinations
- ✅ Model choices are properly defined
- ✅ String representation includes grade level
- ✅ All API endpoints function correctly

## Usage Examples

### Creating Tests
```python
# Elementary Japanese test
test = TestDefinition.objects.create(
    schedule=schedule,
    grade_level='elementary',
    subject='japanese',
    name='小学生国語テスト',
    max_score=100
)

# Middle school English test
test = TestDefinition.objects.create(
    schedule=schedule,
    grade_level='middle_school', 
    subject='english',
    name='中学生英語テスト',
    max_score=100
)
```

### API Usage
```javascript
// Get subjects for elementary students
GET /api/tests/subjects_for_grade/?grade_level=elementary
// Returns: [{'value': 'japanese', 'label': '国語'}, {'value': 'math', 'label': '算数'}]

// Get subjects for middle school students  
GET /api/tests/subjects_for_grade/?grade_level=middle_school
// Returns: [{'value': 'english', 'label': '英語'}, {'value': 'mathematics', 'label': '数学'}]
```

## Implementation Status
All tasks completed successfully:
- ✅ Model updates with grade-based subject selection
- ✅ Validation logic implementation
- ✅ Admin interface enhancements
- ✅ Frontend API updates
- ✅ Comprehensive testing

The system now fully supports both elementary and middle school students with their appropriate subjects, maintaining data integrity through validation and providing a user-friendly interface for administrators.