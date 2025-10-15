from django.core.management.base import BaseCommand
from scores.models import CommentTemplate

class Command(BaseCommand):
    help = 'デフォルトコメントテンプレートを作成'

    def handle(self, *args, **options):
        # 国語のデフォルトコメント
        japanese_comments = [
            (0, 25, "国語の基礎をしっかりと身につけましょう。文章をじっくり読む習慣をつけることが大切です。"),
            (26, 50, "国語の理解が進んでいます。語彙力を増やして、より深い読解力を身につけましょう。"),
            (51, 75, "国語の力がついてきています。難しい文章にも挑戦して、表現力も磨いていきましょう。"),
            (76, 100, "国語の力が素晴らしいです。この調子で読書量を増やし、豊かな表現力を育てていきましょう。"),
        ]
        
        # 算数のデフォルトコメント
        math_comments = [
            (0, 25, "算数の基本計算をしっかりと練習しましょう。毎日少しずつでも計算問題に取り組むことが大切です。"),
            (26, 50, "算数の基礎は身についています。文章問題にも積極的に取り組んで、応用力を伸ばしましょう。"),
            (51, 75, "算数の力がついてきています。様々な問題パターンに慣れて、さらなる向上を目指しましょう。"),
            (76, 100, "算数の力が優秀です。この調子で難しい問題にも挑戦し、論理的思考力を磨いていきましょう。"),
        ]
        
        # 国語コメントを作成
        for min_score, max_score, text in japanese_comments:
            CommentTemplate.objects.get_or_create(
                school=None,
                subject='japanese',
                score_range_min=min_score,
                score_range_max=max_score,
                defaults={
                    'template_text': text,
                    'is_default': True,
                    'is_active': True,
                }
            )
        
        # 算数コメントを作成
        for min_score, max_score, text in math_comments:
            CommentTemplate.objects.get_or_create(
                school=None,
                subject='math',
                score_range_min=min_score,
                score_range_max=max_score,
                defaults={
                    'template_text': text,
                    'is_default': True,
                    'is_active': True,
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS('デフォルトコメントテンプレートが正常に作成されました。')
        )