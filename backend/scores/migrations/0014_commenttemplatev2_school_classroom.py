# Generated manually on 2025-11-13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0005_school_can_input_scores_school_can_register_students_and_more'),
        ('classrooms', '0008_auto_20250917_1256'),
        ('scores', '0013_alter_individualproblemscore_student_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='commenttemplatev2',
            name='school',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comment_templates_v2',
                to='schools.school',
                verbose_name='塾'
            ),
        ),
        migrations.AddField(
            model_name='commenttemplatev2',
            name='classroom',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comment_templates_v2',
                to='classrooms.classroom',
                verbose_name='教室'
            ),
        ),
    ]
