from django.conf import settings

def media_url(request):
    """
    メディアURLを正しいドメインで提供するコンテキストプロセッサ
    """
    # 開発環境では正しいIPアドレスを使用
    if settings.DEBUG:
        host = request.get_host()
        if host.startswith('162.43.55.80') or host.startswith('0.0.0.0'):
            media_url = 'http://162.43.55.80:8000/media/'
        else:
            media_url = settings.MEDIA_URL
    else:
        media_url = settings.MEDIA_URL
    
    return {
        'MEDIA_URL': media_url,
        'FULL_MEDIA_URL': media_url if media_url.startswith('http') else f"http://{request.get_host()}{media_url}"
    }