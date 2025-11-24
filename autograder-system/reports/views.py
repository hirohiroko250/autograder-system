from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
import logging

from tests.models import TestSchedule, TestDefinition
from .utils import TestReportGenerator, create_excel_response, create_pdf_response

logger = logging.getLogger(__name__)


@login_required
def test_report_generator_view(request):
    """テスト結果帳票生成画面"""
    
    # 利用可能なテストスケジュールを取得
    test_schedules = TestSchedule.objects.filter(is_active=True).order_by('-year', 'period')
    
    # 年度と期間の選択肢を生成
    years = sorted(list(set([schedule.year for schedule in test_schedules])), reverse=True)
    periods = TestSchedule.PERIODS
    subjects = TestDefinition.SUBJECTS
    grade_levels = TestDefinition.GRADE_LEVELS
    
    context = {
        'title': 'テスト結果帳票生成',
        'years': years,
        'periods': periods,
        'subjects': subjects,
        'grade_levels': grade_levels,
    }
    
    if request.method == 'POST':
        try:
            # フォームデータを取得
            year = request.POST.get('year')
            period = request.POST.get('period')
            subject = request.POST.get('subject')
            grade_level = request.POST.get('grade_level')
            school_id = request.POST.get('school_id')
            classroom_id = request.POST.get('classroom_id')
            output_format = request.POST.get('format')
            
            # 必須項目チェック
            if not year or not period:
                messages.error(request, '年度と期間は必須です')
                return render(request, 'reports/test_report_generator.html', context)
            
            # レポート生成器を作成
            generator = TestReportGenerator(
                year=int(year),
                period=period,
                subject=subject if subject else None,
                grade_level=grade_level if grade_level else None
            )
            
            # フォーマットに応じてレポートを生成
            if output_format == 'excel':
                content, error = generator.generate_excel_report(
                    school_id=school_id if school_id else None,
                    classroom_id=classroom_id if classroom_id else None
                )
                
                if error:
                    messages.error(request, error)
                    return render(request, 'reports/test_report_generator.html', context)
                
                # ファイル名を生成
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"test_report_{year}_{period}"
                if subject:
                    filename += f"_{subject}"
                if grade_level:
                    filename += f"_{grade_level}"
                filename += f"_{timestamp}.xlsx"
                
                return create_excel_response(content.getvalue(), filename)
                
            elif output_format == 'pdf':
                content, error = generator.generate_pdf_report(
                    school_id=school_id if school_id else None,
                    classroom_id=classroom_id if classroom_id else None
                )
                
                if error:
                    messages.error(request, error)
                    return render(request, 'reports/test_report_generator.html', context)
                
                # ファイル名を生成
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"test_report_{year}_{period}"
                if subject:
                    filename += f"_{subject}"
                if grade_level:
                    filename += f"_{grade_level}"
                filename += f"_{timestamp}.pdf"
                
                return create_pdf_response(content.getvalue(), filename)
            
            else:
                messages.error(request, '出力形式を選択してください')
                
        except Exception as e:
            logger.error(f"レポート生成エラー: {str(e)}")
            messages.error(request, f'レポート生成中にエラーが発生しました: {str(e)}')
    
    return render(request, 'reports/test_report_generator.html', context)


@login_required 
def preview_report_data(request):
    """レポートデータのプレビューAPI"""
    
    try:
        year = request.GET.get('year')
        period = request.GET.get('period')
        subject = request.GET.get('subject')
        grade_level = request.GET.get('grade_level')
        school_id = request.GET.get('school_id')
        classroom_id = request.GET.get('classroom_id')
        
        if not year or not period:
            return JsonResponse({'error': '年度と期間は必須です'}, status=400)
        
        generator = TestReportGenerator(
            year=int(year),
            period=period,
            subject=subject if subject else None,
            grade_level=grade_level if grade_level else None
        )
        
        test_results = generator.get_test_results_data(
            school_id=school_id if school_id else None,
            classroom_id=classroom_id if classroom_id else None
        )
        
        # プレビュー用のデータを準備
        preview_data = {
            'total_count': test_results.count(),
            'schools': list(test_results.values_list(
                'student__classroom__school__name', flat=True
            ).distinct()),
            'subjects': list(test_results.values_list(
                'test__subject', flat=True
            ).distinct()),
            'grade_levels': list(test_results.values_list(
                'test__grade_level', flat=True
            ).distinct()),
        }
        
        # 最初の10件のサンプルデータ
        sample_data = []
        for result in test_results[:10]:
            sample_data.append({
                'school_name': result.student.classroom.school.name,
                'student_id': result.student.student_id,
                'student_name': result.student.name,
                'total_score': result.total_score,
                'correct_rate': f"{result.correct_rate:.1f}%",
                'school_rank': f"{result.school_rank}/{result.school_total_students}" if result.school_rank else "未算出",
                'national_rank': f"{result.national_rank}/{result.national_total_students}" if result.national_rank else "未算出",
            })
        
        preview_data['sample'] = sample_data
        
        return JsonResponse(preview_data)
        
    except Exception as e:
        logger.error(f"プレビューデータ取得エラー: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def bulk_report_generation_view(request):
    """一括帳票生成画面"""
    
    context = {
        'title': '一括帳票生成',
    }
    
    if request.method == 'POST':
        try:
            year = request.POST.get('year')
            period = request.POST.get('period')
            output_format = request.POST.get('format')
            generate_by_school = request.POST.get('generate_by_school') == 'on'
            
            if not year or not period:
                messages.error(request, '年度と期間は必須です')
                return render(request, 'reports/bulk_report_generation.html', context)
            
            # 一括生成処理を実行
            result = generate_bulk_reports(
                year=int(year),
                period=period,
                output_format=output_format,
                generate_by_school=generate_by_school
            )
            
            if result['success']:
                messages.success(request, 
                    f"一括生成が完了しました。生成ファイル数: {result['count']}")
            else:
                messages.error(request, f"一括生成中にエラーが発生しました: {result['error']}")
                
        except Exception as e:
            logger.error(f"一括生成エラー: {str(e)}")
            messages.error(request, f'一括生成中にエラーが発生しました: {str(e)}')
    
    return render(request, 'reports/bulk_report_generation.html', context)


def generate_bulk_reports(year, period, output_format, generate_by_school=False):
    """一括レポート生成処理"""
    
    try:
        count = 0
        
        if generate_by_school:
            # 塾別に生成
            from schools.models import School
            schools = School.objects.filter(is_active=True)
            
            for school in schools:
                generator = TestReportGenerator(year=year, period=period)
                
                if output_format == 'excel':
                    content, error = generator.generate_excel_report(school_id=school.school_id)
                else:
                    content, error = generator.generate_pdf_report(school_id=school.school_id)
                
                if not error and content:
                    # ファイルを保存（実際の実装では適切なストレージに保存）
                    count += 1
        else:
            # 全体で一つのレポートを生成
            generator = TestReportGenerator(year=year, period=period)
            
            if output_format == 'excel':
                content, error = generator.generate_excel_report()
            else:
                content, error = generator.generate_pdf_report()
            
            if not error and content:
                count = 1
        
        return {'success': True, 'count': count}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
