from django.contrib import admin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils import timezone
from .models import IndividualProblem, IndividualProblemScore, Score, TestResult
from .utils import bulk_calculate_test_results
from tests.models import TestDefinition

class ZeroScoreFilter(admin.SimpleListFilter):
    title = '合計点フィルター'
    parameter_name = 'total_score_filter'
    
    def lookups(self, request, model_admin):
        return (
            ('zero', '0点のみ（欠席者）'),
            ('non_zero', '1点以上'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'zero':
            return queryset.filter(total_score=0)
        elif self.value() == 'non_zero':
            return queryset.filter(total_score__gt=0)
        return queryset

@admin.register(IndividualProblem)
class IndividualProblemAdmin(admin.ModelAdmin):
    list_display = ['test', 'problem_number', 'max_score', 'description']
    list_filter = ['test', 'max_score']
    search_fields = ['test__name', 'description']
    ordering = ['test', 'problem_number']
    
@admin.register(IndividualProblemScore)
class IndividualProblemScoreAdmin(admin.ModelAdmin):
    list_display = ['student', 'test', 'problem_number_display', 'score', 'max_score_display', 'created_at']
    list_filter = ['test', 'problem__problem_number', 'created_at']
    search_fields = ['student__name', 'student__student_id']
    ordering = ['test', 'student', 'problem__problem_number']
    
    def problem_number_display(self, obj):
        return f"問題{obj.problem.problem_number}"
    problem_number_display.short_description = '問題番号'
    
    def max_score_display(self, obj):
        return f"{obj.problem.max_score}点"
    max_score_display.short_description = '満点'

class ScoreAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'test_display', 'question_group_display', 'score', 'attendance', 'created_at']
    list_filter = ['test', 'question_group', 'attendance', 'created_at']
    search_fields = ['student__name', 'student__student_id', 'test__subject']
    ordering = ['test', 'student', 'question_group__group_number']
    readonly_fields = ['created_at', 'updated_at']
    
    
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = '生徒名'
    
    def test_display(self, obj):
        return f"{obj.test.schedule.year}年度{obj.test.schedule.get_period_display()} {obj.test.get_subject_display()}"
    test_display.short_description = 'テスト'
    
    def question_group_display(self, obj):
        return f"大問{obj.question_group.group_number}"
    question_group_display.short_description = '大問'
    

class TestResultAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_id_display', 'grade_display', 'school_display', 'test_display', 'total_score_display', 'deviation_score_display', 'grade_rank_display', 'school_rank_display', 'question_scores_display', 'updated_at']
    list_filter = ['test__schedule__year', 'test__schedule__period', 'test', 'is_rank_finalized', 'created_at', 'student__grade', 'student__classroom__school', ZeroScoreFilter]
    search_fields = ['student__name', 'student__student_id', 'test__subject', 'student__classroom__school__name']
    ordering = ['test', '-total_score']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['generate_test_results_from_scores', 'calculate_school_ranks', 'remove_absent_students', 'delete_zero_score_results']
    list_per_page = 50
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'テスト結果管理'
        return super().changelist_view(request, extra_context)
    
    
    # Japanese field labels
    fields = [
        'student', 'test', 'total_score', 'correct_rate',
        ('grade_rank', 'grade_total', 'grade_deviation_score'),
        ('school_category_rank', 'school_category_total'),
        ('national_rank', 'national_total'),
        ('school_rank_final', 'school_total_final'),
        'is_rank_finalized', 'comment',
        ('created_at', 'updated_at')
    ]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Override field labels to Japanese
        if 'grade_rank' in form.base_fields:
            form.base_fields['grade_rank'].label = '学年内順位'
        if 'grade_total' in form.base_fields:
            form.base_fields['grade_total'].label = '学年内受験者数'
        if 'grade_deviation_score' in form.base_fields:
            form.base_fields['grade_deviation_score'].label = '学年内偏差値'
        if 'school_category_rank' in form.base_fields:
            form.base_fields['school_category_rank'].label = '小中区分内順位'
        if 'school_category_total' in form.base_fields:
            form.base_fields['school_category_total'].label = '小中区分内受験者数'
        if 'national_rank' in form.base_fields:
            form.base_fields['national_rank'].label = '全国順位'
        if 'national_total' in form.base_fields:
            form.base_fields['national_total'].label = '全国受験者数'
        if 'school_rank_final' in form.base_fields:
            form.base_fields['school_rank_final'].label = '塾内順位'
        if 'school_total_final' in form.base_fields:
            form.base_fields['school_total_final'].label = '塾内受験者数'
        if 'total_score' in form.base_fields:
            form.base_fields['total_score'].label = '合計点'
        if 'correct_rate' in form.base_fields:
            form.base_fields['correct_rate'].label = '正答率（%）'
        if 'is_rank_finalized' in form.base_fields:
            form.base_fields['is_rank_finalized'].label = '順位確定済み'
        if 'comment' in form.base_fields:
            form.base_fields['comment'].label = 'コメント'
        return form
    
    def student_name(self, obj):
        return obj.student.name
    student_name.short_description = '生徒名'
    
    def test_display(self, obj):
        return f"{obj.test.schedule.year}年度{obj.test.schedule.get_period_display()} {obj.test.get_subject_display()}"
    test_display.short_description = 'テスト'
    
    def national_rank_display(self, obj):
        if obj.is_rank_finalized and obj.national_rank_final:
            return f"{obj.national_rank_final}位/{obj.national_total_final}名"
        elif obj.national_rank_temporary:
            return f"{obj.national_rank_temporary}位/{obj.national_total_temporary}名 (暫定)"
        return "-"
    national_rank_display.short_description = '全国順位'
    
    def school_rank_display(self, obj):
        # 学年別塾内順位を計算して表示
        school_id = obj.student.classroom.school.id if obj.student.classroom else None
        grade = obj.student.grade
        
        if school_id and grade:
            # 同じ塾・同じ学年で成績が上の生徒の数を数える
            better_results = TestResult.objects.filter(
                test=obj.test,
                student__classroom__school_id=school_id,
                student__grade=grade,
                total_score__gt=obj.total_score
            ).count()
            
            # 同じ塾・同じ学年の総生徒数
            total_students = TestResult.objects.filter(
                test=obj.test,
                student__classroom__school_id=school_id,
                student__grade=grade
            ).count()
            
            rank = better_results + 1
            return f"{rank}位/{total_students}名"
        return "-"
    school_rank_display.short_description = '塾内順位（学年別）'
    
    def student_id_display(self, obj):
        return obj.student.student_id
    student_id_display.short_description = '生徒ID'
    
    def grade_display(self, obj):
        grade = obj.student.grade
        if grade:
            try:
                grade_num = int(grade)
                if 1 <= grade_num <= 6:
                    return f"小学{grade_num}年生"
                elif grade_num == 7:
                    return "中学1年生"
                elif grade_num == 8:
                    return "中学2年生"
                elif grade_num == 9:
                    return "中学3年生"
                else:
                    return f"{grade}年生"
            except (ValueError, TypeError):
                return f"{grade}年生"
        return "-"
    grade_display.short_description = '学年'
    
    def school_display(self, obj):
        return obj.student.classroom.school.name if obj.student.classroom else "-"
    school_display.short_description = '塾名'
    
    def question_scores_display(self, obj):
        """大問ごとの得点を表示（全て表示）"""
        from django.db.models import Q
        from .models import Score
        from django.utils.html import format_html
        
        # 同じテストの大問別得点を取得
        scores = Score.objects.filter(
            student=obj.student,
            test=obj.test,
            attendance=True
        ).order_by('question_group__group_number')
        
        if scores.exists():
            score_list = []
            for score in scores:
                # スコアに応じて色分け表示
                if score.score == 0:
                    score_list.append(f'<span style="color: #dc3545;">大問{score.question_group.group_number}:{score.score}点</span>')
                elif score.score >= score.question_group.max_score * 0.8:  # 8割以上
                    score_list.append(f'<span style="color: #198754;">大問{score.question_group.group_number}:{score.score}点</span>')
                else:
                    score_list.append(f'大問{score.question_group.group_number}:{score.score}点')
            
            # HTMLとして安全に表示
            return format_html(" | ".join(score_list))
        return "-"
    question_scores_display.short_description = '大問別得点（全問表示）'
    
    def deviation_score_display(self, obj):
        """偏差値を表示"""
        if obj.grade_deviation_score:
            return f"{obj.grade_deviation_score:.1f}"
        return "-"
    deviation_score_display.short_description = '偏差値'
    
    def grade_rank_display(self, obj):
        """学年別順位を表示"""
        if obj.grade_rank and obj.grade_total:
            return f"{obj.grade_rank}位/{obj.grade_total}名"
        return "-"
    grade_rank_display.short_description = '学年内順位'
    
    def total_score_display(self, obj):
        """合計点を表示（0点の場合はハイライト）"""
        if obj.total_score == 0:
            return format_html(
                '<span style="color: red; background-color: #ffe6e6; padding: 2px 4px; border-radius: 3px; font-weight: bold;">{} 点（欠席？）</span>',
                obj.total_score
            )
        else:
            return f"{obj.total_score} 点"
    total_score_display.short_description = 'TOTAL SCORE'
    
    
    
    
    def generate_test_results_from_scores(self, request, queryset):
        """
        【STEP 1】ScoreからTestResultを生成
        得点入力済みのScoreデータから、TestResultレコードを自動生成します。
        新規データの作成や既存データの更新に使用してください。
        """
        from django.db.models import Sum, Count
        from .models import Score, TestResult
        from tests.models import TestDefinition
        
        generated_count = 0
        
        # 全てのテストについてTestResultを生成（出席者のみ）
        tests = TestDefinition.objects.all()
        
        for test in tests:
            # 各生徒の合計点を計算（出席者のみ、かつ有効な得点があるもの）
            student_totals = Score.objects.filter(
                test=test,
                attendance=True,  # 出席者のみ
                score__gte=0  # 0点以上（負の値を除外）
            ).values('student').annotate(
                total_score=Sum('score'),
                question_count=Count('question_group')  # 回答した大問数もカウント
            ).filter(
                question_count__gt=0  # 最低1つは大問に回答している
            )
            
            for student_total in student_totals:
                student_id = student_total['student']
                total_score = student_total['total_score']
                
                # 正答率を計算（仮に100点満点とする）
                correct_rate = (total_score / 100.0) * 100 if total_score else 0
                
                # TestResultを取得または作成
                test_result, created = TestResult.objects.get_or_create(
                    student_id=student_id,
                    test=test,
                    defaults={
                        'total_score': total_score,
                        'correct_rate': correct_rate,
                        'is_rank_finalized': False
                    }
                )
                
                if created:
                    generated_count += 1
                elif test_result.total_score != total_score:
                    # 既存データを更新
                    test_result.total_score = total_score
                    test_result.correct_rate = correct_rate
                    test_result.save()
                    generated_count += 1
        
        self.message_user(request, f"TestResultを{generated_count}件生成/更新しました。", messages.SUCCESS)
    generate_test_results_from_scores.short_description = "🔄 【STEP1】テスト結果を生成・更新（推奨）"
    
    
    def remove_absent_students(self, request, queryset):
        """
        【メンテナンス】欠席者のTestResultを削除
        欠席者の不要なデータを削除します。通常は使用不要。
        """
        from .models import Score
        
        removed_count = 0
        
        # 全てのTestResultについて、対応するScoreが欠席または存在しない場合は削除
        for test_result in TestResult.objects.all():
            # 該当する出席スコアがあるかチェック
            has_attendance_score = Score.objects.filter(
                student=test_result.student,
                test=test_result.test,
                attendance=True
            ).exists()
            
            if not has_attendance_score:
                test_result.delete()
                removed_count += 1
        
        self.message_user(
            request,
            f"欠席者のTestResultを{removed_count}件削除しました。",
            messages.SUCCESS
        )
    remove_absent_students.short_description = "🗑️ 【メンテナンス】欠席者データを削除"
    
    def delete_zero_score_results(self, request, queryset):
        """
        【欠席者削除】0点のテスト結果を削除
        合計点が0点のテスト結果を欠席者とみなして削除します。
        """
        deleted_count = 0
        
        # クエリセットが選択されている場合は選択されたもののみ、そうでなければ全体から0点を削除
        if queryset.exists():
            # 選択されたテスト結果の中で0点のものを削除
            zero_score_results = queryset.filter(total_score=0)
        else:
            # 全てのテスト結果の中で0点のものを削除
            zero_score_results = TestResult.objects.filter(total_score=0)
        
        deleted_items = []
        for result in zero_score_results:
            deleted_items.append({
                'student': result.student.name,
                'student_id': result.student.student_id,
                'test': str(result.test),
                'total_score': result.total_score
            })
            result.delete()
            deleted_count += 1
        
        if deleted_count > 0:
            # 削除された結果の詳細をメッセージに含める（最初の10件まで）
            details = []
            for item in deleted_items[:10]:
                details.append(f"{item['student']}({item['student_id']}) - {item['test']}")
            
            detail_message = "削除された結果: " + ", ".join(details)
            if len(deleted_items) > 10:
                detail_message += f" ...他{len(deleted_items) - 10}件"
            
            self.message_user(
                request,
                f"0点のテスト結果を{deleted_count}件削除しました。{detail_message}",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "削除対象の0点テスト結果はありませんでした。",
                messages.INFO
            )
    
    delete_zero_score_results.short_description = "❌ 【欠席者削除】0点の結果を削除"
    
    def calculate_school_ranks(self, request, queryset):
        """
        【STEP 2】順位・偏差値を一括計算
        TestResult作成後に実行し、学年別順位・小中区分別順位・偏差値を計算します。
        選択されたテスト結果に関連するテストのみを処理します。
        """
        from django.db.models import Avg, StdDev
        import math
        
        updated_count = 0
        tests_processed = set()
        
        # 選択されたテスト結果から関連するテストを取得（パフォーマンス改善）
        selected_tests = set(result.test_id for result in queryset)
        
        for test_id in selected_tests:
            test_results = TestResult.objects.filter(test_id=test_id)
            
            # 1. 学年別の順位・偏差値計算
            grades = test_results.values_list('student__grade', flat=True).distinct()
            
            for grade in grades:
                if not grade:
                    continue
                    
                grade_results = test_results.filter(student__grade=grade).order_by('-total_score')
                total_students = grade_results.count()
                
                if total_students == 0:
                    continue
                
                # 学年平均点と標準偏差を計算
                stats = grade_results.aggregate(
                    avg_score=Avg('total_score'),
                    std_dev=StdDev('total_score')
                )
                avg_score = stats['avg_score'] or 0
                std_dev = stats['std_dev'] or 1  # 0で割ることを防ぐ
                
                # 順位と偏差値を更新
                rank = 1
                prev_score = None
                actual_rank = 1
                
                for result in grade_results:
                    # 順位計算
                    if prev_score is not None and result.total_score < prev_score:
                        rank = actual_rank
                    
                    # 偏差値計算 (平均50, 標準偏差10)
                    if std_dev > 0:
                        deviation_score = 50 + (result.total_score - avg_score) / std_dev * 10
                        deviation_score = max(0, min(100, deviation_score))  # 0-100の範囲に制限
                    else:
                        deviation_score = 50
                    
                    # 学年別順位・偏差値を保存
                    result.grade_rank = rank
                    result.grade_total = total_students
                    result.grade_deviation_score = round(deviation_score, 2)
                    
                    # 学年別塾内順位を保存（確定として）
                    school_id = result.student.classroom.school.id if result.student.classroom else None
                    if school_id:
                        # 同じ塾・同じ学年でフィルタリング
                        school_grade_results = test_results.filter(
                            student__classroom__school_id=school_id,
                            student__grade=grade
                        )
                        better_school_results = school_grade_results.filter(total_score__gt=result.total_score).count()
                        school_total = school_grade_results.count()
                        result.school_rank_final = better_school_results + 1
                        result.school_total_final = school_total
                    
                    result.is_rank_finalized = True
                    result.rank_finalized_at = timezone.now()
                    result.save(update_fields=[
                        'grade_rank', 'grade_total', 'grade_deviation_score',
                        'school_rank_final', 'school_total_final',
                        'is_rank_finalized', 'rank_finalized_at'
                    ])
                    
                    prev_score = result.total_score
                    actual_rank += 1
                    updated_count += 1
            
            # 2. 全国順位は削除（学年別が基本方針）
                
                tests_processed.add(test_id)
        
        self.message_user(
            request, 
            f"順位・偏差値を計算しました。{len(tests_processed)}テスト・{updated_count}件の結果を更新。", 
            messages.SUCCESS
        )
    calculate_school_ranks.short_description = "📊 【STEP2】順位・偏差値を計算"

# テスト定義からの一括計算用のAdmin拡張は上記のEnhancedTestDefinitionAdminで実装

# Scoreモデルの登録
try:
    admin.site.unregister(Score)
except admin.sites.NotRegistered:
    pass
admin.site.register(Score, ScoreAdmin)

# TestResultモデルの登録  
try:
    admin.site.unregister(TestResult)
except admin.sites.NotRegistered:
    pass
admin.site.register(TestResult, TestResultAdmin)

# TestDefinitionモデルの登録 - autograderアプリの完全なAdminクラスを使用
try:
    admin.site.unregister(TestDefinition)
except admin.sites.NotRegistered:
    pass

# autograderのTestDefinitionAdminを拡張して、scores機能を追加
from autograder.admin import TestDefinitionAdmin as BaseTestDefinitionAdmin

class EnhancedTestDefinitionAdmin(BaseTestDefinitionAdmin):
    """autograderのTestDefinitionAdminにscores機能を追加"""
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        # scores機能のアクションを追加
        actions['calculate_all_results'] = (self.calculate_all_results, 'calculate_all_results', '選択されたテストの全結果を計算')
        actions['force_calculate_all_results'] = (self.force_calculate_all_results, 'force_calculate_all_results', '選択されたテストの全結果を強制再計算')
        return actions
    
    def calculate_all_results(self, request, queryset):
        """選択されたテスト定義の全結果を計算"""
        calculated_count = 0
        for test_def in queryset:
            try:
                results = bulk_calculate_test_results(test_def)
                calculated_count += len(results)
                self.message_user(request, f"テスト '{test_def}' の結果を計算しました ({len(results)}件)", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"テスト '{test_def}' の計算中にエラーが発生しました: {str(e)}", messages.ERROR)
        
        if calculated_count > 0:
            self.message_user(request, f"合計 {calculated_count} 件の結果を計算しました。", messages.SUCCESS)
    
    calculate_all_results.short_description = "選択されたテストの全結果を計算"
    
    def force_calculate_all_results(self, request, queryset):
        """選択されたテスト定義の全結果を強制再計算"""
        calculated_count = 0
        for test_def in queryset:
            try:
                results = bulk_calculate_test_results(test_def, force_recalculate=True)
                calculated_count += len(results)
                self.message_user(request, f"テスト '{test_def}' の結果を強制再計算しました ({len(results)}件)", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"テスト '{test_def}' の強制再計算中にエラーが発生しました: {str(e)}", messages.ERROR)
        
        if calculated_count > 0:
            self.message_user(request, f"合計 {calculated_count} 件の結果を強制再計算しました。", messages.SUCCESS)
    
    force_calculate_all_results.short_description = "選択されたテストの全結果を強制再計算"

admin.site.register(TestDefinition, EnhancedTestDefinitionAdmin)
