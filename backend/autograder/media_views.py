from django.http import Http404, HttpResponse
from django.shortcuts import render
import os
from django.conf import settings


def secure_media_serve(request, path):
    """
    メディアファイルのセキュアな配信
    ファイルが存在しない場合の適切なエラーハンドリング
    """
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # ファイルが存在しない場合の処理
    if not os.path.exists(file_path):
        context = {
            'error_message': 'リクエストされたファイルが見つかりません。',
            'file_path': path,
            'suggestions': [
                'ファイルが正しく生成されているか確認してください。',
                'レポートを再生成してください。', 
                'ファイルパスが正しいか確認してください。'
            ]
        }
        return render(request, 'errors/file_not_found.html', context, status=404)
    
    # ファイルが存在する場合は通常通り配信
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # MIMEタイプの決定
        content_type = 'application/octet-stream'
        if path.endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif path.endswith('.xlsx'):
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif path.endswith('.pdf'):
            content_type = 'application/pdf'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        
        response = HttpResponse(file_data, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
        return response
        
    except Exception as e:
        context = {
            'error_message': f'ファイルの読み込み中にエラーが発生しました: {str(e)}',
            'file_path': path,
        }
        return render(request, 'errors/file_error.html', context, status=500)