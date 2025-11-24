from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.contrib import messages
from django.core.files.storage import default_storage
from .utils import import_schools_from_excel
import tempfile
import os

class SchoolImportForm:
    """塾データインポート用フォーム"""
    
    def __init__(self, request):
        self.request = request
    
    def process_import(self, excel_file):
        """Excelファイルからの塾データインポート処理"""
        try:
            # ファイル名と拡張子をチェック
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(self.request, "Excelファイル（.xlsx または .xls）をアップロードしてください。")
                return False
            
            # ファイルサイズをチェック（10MB以下）
            if excel_file.size > 10 * 1024 * 1024:
                messages.error(self.request, "ファイルサイズが大きすぎます（10MB以下にしてください）。")
                return False
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # インポート実行
            result = import_schools_from_excel(tmp_file_path)
            
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
            
            if result['success']:
                success_msg = f"塾データのインポートが完了しました。作成された塾: {result['created_schools']}件"
                messages.success(self.request, success_msg)
                
                # 作成されたユーザー認証情報を表示
                if result['user_credentials']:
                    cred_msg = "作成されたユーザー認証情報:\n"
                    for cred in result['user_credentials']:
                        cred_msg += f"塾: {cred['school_name']}, ID: {cred['username']}, PW: {cred['password']}\n"
                    messages.info(self.request, cred_msg)
                
                # エラーがあった場合は警告表示
                if result['errors']:
                    error_msg = "以下のエラーがありました:\n" + "\n".join(result['errors'])
                    messages.warning(self.request, error_msg)
                    
                return True
            else:
                messages.error(self.request, f"インポートに失敗しました: {result['error']}")
                return False
                
        except Exception as e:
            messages.error(self.request, f"ファイル処理中にエラーが発生しました: {str(e)}")
            return False

def school_import_action(modeladmin, request, queryset):
    """塾データ一括インポートアクション"""
    if request.method == 'POST' and 'excel_file' in request.FILES:
        form = SchoolImportForm(request)
        if form.process_import(request.FILES['excel_file']):
            return HttpResponseRedirect(request.get_full_path())
    
    # インポートフォームを表示
    context = {
        'title': '塾データ一括インポート',
        'action': 'school_import_action',
        'queryset': queryset,
        'opts': modeladmin.model._meta,
    }
    
    return render(request, 'admin/school_import.html', context)

school_import_action.short_description = "塾データを一括インポート"