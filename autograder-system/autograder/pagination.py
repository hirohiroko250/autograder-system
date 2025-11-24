from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    page_sizeクエリパラメータに対応したカスタムページネーション
    """
    page_size = 50  # デフォルトページサイズ
    page_size_query_param = 'page_size'  # page_sizeパラメータを有効化
    max_page_size = 10000  # 最大ページサイズ