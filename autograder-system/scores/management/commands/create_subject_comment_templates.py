from django.core.management.base import BaseCommand
from scores.models import CommentTemplateV2

class Command(BaseCommand):
    help = '教科ごとの総評用デフォルトコメントテンプレートを作成'

    def handle(self, *args, **kwargs):
        templates_data = [
            # 国語
            {
                'subject': 'japanese',
                'score_range': '0-20',
                'title': '国語 0-20点',
                'comment': '基礎的な内容の理解に課題が見られます。まずは教科書の音読を毎日続けることで、文章に慣れることから始めましょう。漢字の読み書きも繰り返し練習することで、確実に力がついていきます。焦らず一歩ずつ進んでいきましょう。'
            },
            {
                'subject': 'japanese',
                'score_range': '21-40',
                'title': '国語 21-40点',
                'comment': '基礎的な問題は理解できていますが、応用問題で苦戦しています。読解力を高めるため、様々なジャンルの文章を読む習慣をつけましょう。漢字や語句の知識を増やすことで、文章理解も深まります。少しずつ着実に力をつけていきましょう。'
            },
            {
                'subject': 'japanese',
                'score_range': '41-60',
                'title': '国語 41-60点',
                'comment': '基本的な読解力は身についています。さらに得点を伸ばすには、文章の細部まで注意深く読む習慣が大切です。記述問題では、答えの根拠を本文から探す練習を重ねましょう。継続的な努力で確実に力がついていきます。'
            },
            {
                'subject': 'japanese',
                'score_range': '61-80',
                'title': '国語 61-80点',
                'comment': '読解力が着実に身についており、よく頑張っています。さらに高得点を目指すには、記述問題での表現力を磨くことが重要です。制限時間内で正確に答えをまとめる練習を積み重ねましょう。この調子で学習を続けてください。'
            },
            {
                'subject': 'japanese',
                'score_range': '81-100',
                'title': '国語 81-100点',
                'comment': '高い読解力と表現力が身についており、大変よくできています。この力を維持しながら、さらに多様な文章に触れることで、より深い理解力を養いましょう。難易度の高い問題にも積極的にチャレンジし、更なる成長を目指してください。'
            },

            # 算数
            {
                'subject': 'math',
                'score_range': '0-20',
                'title': '算数 0-20点',
                'comment': '基本的な計算や概念の理解に課題があります。まずは基礎計算を繰り返し練習し、確実に解けるようにしましょう。わからない問題は先生に質問し、理解を深めることが大切です。一つ一つ丁寧に学習を進めていきましょう。'
            },
            {
                'subject': 'math',
                'score_range': '21-40',
                'title': '算数 21-40点',
                'comment': '基本問題は解けていますが、応用力に課題があります。計算ミスを減らすため、見直しの習慣をつけましょう。文章題では、図や表を使って考える練習が効果的です。コツコツと努力を続けることで、必ず力がついていきます。'
            },
            {
                'subject': 'math',
                'score_range': '41-60',
                'title': '算数 41-60点',
                'comment': '基礎的な力は身についています。さらに得点を伸ばすには、応用問題への取り組みを増やすことが大切です。間違えた問題は必ず復習し、解き方を理解しましょう。計算の正確性も意識して、ケアレスミスを減らす努力を続けてください。'
            },
            {
                'subject': 'math',
                'score_range': '61-80',
                'title': '算数 61-80点',
                'comment': '着実に力をつけており、よく頑張っています。さらに高得点を目指すには、難易度の高い問題にチャレンジすることが重要です。時間配分を意識しながら、確実に解ける問題から取り組む戦略を身につけましょう。この調子で学習を継続してください。'
            },
            {
                'subject': 'math',
                'score_range': '81-100',
                'title': '算数 81-100点',
                'comment': '高い計算力と思考力が身についており、大変よくできています。この力を維持しながら、さらに発展的な問題にも取り組み、数学的な考え方を深めましょう。様々なパターンの問題を解くことで、更なる成長が期待できます。'
            },
        ]

        created_count = 0
        for data in templates_data:
            template, created = CommentTemplateV2.objects.get_or_create(
                category=f"{data['subject']}_{data['score_range']}",
                defaults={
                    'title': data['title'],
                    'template_text': data['comment'],
                    'applicable_scope': 'specific_subject',
                    'subject_filter': data['subject']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ {data['title']} のテンプレートを作成しました"))
            else:
                self.stdout.write(f"  {data['title']} は既に存在します")

        self.stdout.write(self.style.SUCCESS(f"\n合計 {created_count} 件のテンプレートを作成しました"))
