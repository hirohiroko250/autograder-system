from django.core.management.base import BaseCommand
from scores.models import CommentTemplateV2

class Command(BaseCommand):
    help = 'コメントテンプレートの初期データを作成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='既存のテンプレートをすべて削除してから作成'
        )

    def handle(self, *args, **options):
        if options['clear']:
            CommentTemplateV2.objects.all().delete()
            self.stdout.write(self.style.WARNING('既存のテンプレートをすべて削除しました'))

        # 良い評価テンプレート
        positive_templates = [
            {
                'title': '素晴らしい成績',
                'category': 'positive',
                'template_text': '素晴らしい成績です！この調子で頑張ってください。',
                'applicable_scope': 'high_score',
                'score_range_min': 80,
                'score_range_max': 100,
            },
            {
                'title': '満点達成',
                'category': 'positive',
                'template_text': '満点達成おめでとうございます！完璧な理解を示しています。',
                'applicable_scope': 'high_score',
                'score_range_min': 100,
                'score_range_max': 100,
            },
            {
                'title': '前回から向上',
                'category': 'positive',
                'template_text': '前回よりも点数が向上しています。努力の成果が表れていますね。',
                'applicable_scope': 'improved',
            },
            {
                'title': '良い理解度',
                'category': 'positive',
                'template_text': 'よく理解できています。基礎がしっかり身についていますね。',
                'applicable_scope': 'average_score',
                'score_range_min': 70,
                'score_range_max': 85,
            },
        ]

        # 改善が必要なテンプレート
        improvement_templates = [
            {
                'title': '基礎の復習が必要',
                'category': 'needs_improvement',
                'template_text': '基礎から復習して、理解を深めましょう。',
                'applicable_scope': 'low_score',
                'score_range_min': 0,
                'score_range_max': 50,
            },
            {
                'title': '計算ミスに注意',
                'category': 'needs_improvement',
                'template_text': '計算ミスが目立ちます。見直しを心がけましょう。',
                'applicable_scope': 'any',
                'subject_filter': 'math',
            },
            {
                'title': '文章読解の練習',
                'category': 'needs_improvement',
                'template_text': '文章をしっかり読んで理解する練習をしましょう。',
                'applicable_scope': 'any',
                'subject_filter': 'japanese',
            },
            {
                'title': '前回より低下',
                'category': 'needs_improvement',
                'template_text': '前回より点数が下がっています。復習を重点的に行いましょう。',
                'applicable_scope': 'declined',
            },
        ]

        # 励ましテンプレート
        encouragement_templates = [
            {
                'title': '次回に向けて',
                'category': 'encouragement',
                'template_text': '今回は思うような結果が出ませんでしたが、次回に向けて一緒に頑張りましょう。',
                'applicable_scope': 'low_score',
                'score_range_min': 0,
                'score_range_max': 60,
            },
            {
                'title': '継続は力',
                'category': 'encouragement',
                'template_text': '継続は力です。毎日少しずつでも勉強を続けていきましょう。',
                'applicable_scope': 'any',
            },
            {
                'title': 'あと一歩',
                'category': 'encouragement',
                'template_text': 'あと少しで目標達成です。もう一踏ん張り頑張りましょう。',
                'applicable_scope': 'average_score',
                'score_range_min': 60,
                'score_range_max': 75,
            },
        ]

        # 宿題関連テンプレート
        homework_templates = [
            {
                'title': '宿題の見直し',
                'category': 'homework',
                'template_text': '宿題でしっかり復習してください。特に間違えた問題を重点的に。',
                'applicable_scope': 'any',
            },
            {
                'title': '追加練習が必要',
                'category': 'homework',
                'template_text': '追加で練習問題に取り組むことをお勧めします。',
                'applicable_scope': 'low_score',
                'score_range_min': 0,
                'score_range_max': 70,
            },
        ]

        # 学習態度関連テンプレート
        behavior_templates = [
            {
                'title': '集中して取り組めています',
                'category': 'behavior',
                'template_text': '授業中よく集中して取り組めています。この姿勢を続けてください。',
                'applicable_scope': 'any',
            },
            {
                'title': '質問を積極的に',
                'category': 'behavior',
                'template_text': 'わからないことは積極的に質問しましょう。理解が深まります。',
                'applicable_scope': 'any',
            },
        ]

        # 特定スキル関連テンプレート
        skill_templates = [
            {
                'title': '応用力が向上',
                'category': 'specific_skill',
                'template_text': '応用問題を解く力が向上しています。さらに難しい問題にも挑戦してみましょう。',
                'applicable_scope': 'high_score',
                'score_range_min': 85,
                'score_range_max': 100,
            },
            {
                'title': '計算力が安定',
                'category': 'specific_skill',
                'template_text': '計算力が安定してきました。正確性を保ちながらスピードアップを図りましょう。',
                'applicable_scope': 'any',
                'subject_filter': 'math',
            },
        ]

        # すべてのテンプレートを結合
        all_templates = (
            positive_templates + improvement_templates + encouragement_templates + 
            homework_templates + behavior_templates + skill_templates
        )

        created_count = 0
        for template_data in all_templates:
            template, created = CommentTemplateV2.objects.get_or_create(
                title=template_data['title'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'テンプレート作成: {template.title}')
            else:
                self.stdout.write(f'テンプレート既存: {template.title}')

        self.stdout.write(
            self.style.SUCCESS(f'コメントテンプレートの作成完了: {created_count}件作成')
        )