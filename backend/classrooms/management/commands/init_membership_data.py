from django.core.management.base import BaseCommand
from classrooms.models import MembershipType


class Command(BaseCommand):
    help = '会員種別・料金設定の初期データを作成'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('会員種別・料金設定データの初期化を開始します...'))
        
        # 料金設定データ
        membership_data = [
            {
                'type_code': 'culture_kids',
                'name': 'カルチャーキッズ導入塾',
                'description': 'カルチャーキッズ会員システムを導入している塾',
                'price_per_student': 100,
            },
            {
                'type_code': 'eduplus',
                'name': 'eduplus導入塾',
                'description': 'eduplus学習管理システムを導入している塾',
                'price_per_student': 300,
            },
            {
                'type_code': 'general',
                'name': '一般塾',
                'description': '特別なシステムを導入していない一般的な塾',
                'price_per_student': 500,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in membership_data:
            membership_type, created = MembershipType.objects.get_or_create(
                type_code=data['type_code'],
                defaults=data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'作成: {membership_type.name} - {membership_type.price_per_student}円')
                )
            else:
                # 既存のレコードの料金を更新
                if membership_type.price_per_student != data['price_per_student']:
                    old_price = membership_type.price_per_student
                    membership_type.price_per_student = data['price_per_student']
                    membership_type.name = data['name']
                    membership_type.description = data['description']
                    membership_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'更新: {membership_type.name} - {old_price}円 → {membership_type.price_per_student}円')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'既存: {membership_type.name} - {membership_type.price_per_student}円')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n完了: 作成 {created_count}件, 更新 {updated_count}件'
            )
        )
        
        # 料金一覧表示
        self.stdout.write(self.style.SUCCESS('\n=== 現在の料金設定 ==='))
        for membership_type in MembershipType.objects.filter(is_active=True).order_by('price_per_student'):
            self.stdout.write(f'  {membership_type.name}: {membership_type.price_per_student}円/名')