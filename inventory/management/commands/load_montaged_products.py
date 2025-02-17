from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from inventory.models import Product, InventoryCategory
from erp_core.models import Customer

class Command(BaseCommand):
    help = 'Loads montaged products data into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading montaged products data...')

        try:
            with transaction.atomic():
                # Get or create the MAMUL category
                mamul_category, _ = InventoryCategory.objects.get_or_create(
                    name='MAMUL',
                    defaults={'description': 'Finished and Single Products'}
                )

                # Get or create customers
                kk_customer, _ = Customer.objects.get_or_create(
                    code='KKCO',
                    defaults={'name': 'KK Customer'}
                )
                ss_customer, _ = Customer.objects.get_or_create(
                    code='SSCO',
                    defaults={'name': 'SS Customer'}
                )

                # Montaged products data
                products_data = [
                    {
                        'product_code': '02.PİM.SPİ.Ø02.50x14.00',
                        'product_name': 'DIN 7343 Ø2.5x14mm St Spiral Pim',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.0.13.0001.01.00.00',
                        'product_name': 'Alt Mekanizma Gövdesi_Rev.1',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.0.13.0002.01.00.00',
                        'product_name': 'Piston Mili_Rev.1',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.01.0000.00.00.00',
                        'product_name': 'MPT 76-GEZ KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.02.0000.00.00.00',
                        'product_name': 'MPT 76-ARPACIK KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.03.0000.00.00.00',
                        'product_name': 'KCR556 11"-14,5"  GEZ KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.04.0000.00.00.00',
                        'product_name': 'KCR556-11"-14,5" ARPACIK KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.05.0000.00.00.00',
                        'product_name': 'KCR556-7,5" GEZ KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.06.0000.00.00.00',
                        'product_name': 'KCR556-7,5" ARPACIK KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.07.0000.00.00.00',
                        'product_name': 'KGL 40 - NİŞANGAH KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.08.0000.00.00.00',
                        'product_name': 'KMG5 16" MEKANİZMA GRUBU KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.09.0000.00.00.00',
                        'product_name': 'KMG5 16" ALT MEKANİZMA ALT KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.10.0000.00.00.00',
                        'product_name': 'KMG5 16" ÜST MEKANİZMA ALT KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.11.0000.00.00.00',
                        'product_name': 'KMG5 16" MEKANİZMA BAŞI KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.12.0000.00.00.00',
                        'product_name': 'KMG5 16" BESLEME GRUBU KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.13.0000.04.00.00',
                        'product_name': 'KMG5 16" AMPMK_Rev.4',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': 'KMG5-P404_ALT_MEKANIZMA_GOVDESI_R9 olduğu için revize edildi.'
                    },
                    {
                        'product_code': '03.1.14.0000.00.00.00',
                        'product_name': 'KMG5 16" A11 GEZ KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.15.0000.00.00.00',
                        'product_name': 'KMG5 16" A27 ARPACIK KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.16.0000.00.00.00',
                        'product_name': 'GEZ KOMPLESI SAR56 JND',
                        'customer': ss_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.17.0000.00.00.00',
                        'product_name': 'ARPACIK KOMPLESI SAR56 JND',
                        'customer': ss_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.18.0000.00.00.00',
                        'product_name': 'A6-513 TASIMA KOLU KOMPLESI',
                        'customer': ss_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.19.0000.00.00.00',
                        'product_name': 'KCR556 11"-14,5"  GEZ KOMPLESİ (L-R)',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': 'Gez yan tambura L-R yazılıyor.'
                    },
                    {
                        'product_code': '03.1.20.0000.00.00.00',
                        'product_name': '556 20S ARPACIK KOMPLESI',
                        'customer': ss_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.21.0000.00.00.00',
                        'product_name': '556 42S Gez Komplesi / 556 HMT GK',
                        'customer': ss_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.22.0000.00.00.00',
                        'product_name': 'KMG5 - ALT MEKANİZMA PİSTON MİLİ KOMPLESİ',
                        'customer': None,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.22.0000.01.00.00',
                        'product_name': 'AMPMK - Gövdesi PDK lı ürün_Rev.1',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': '• Ø 3 lük delik kaldırıldı,\n• Loctite 290 yerine 270 kullanılacak,\n• Notlar kısmına (7.2) montaj sonrası torkladıktan sonra yüzeylerin örtüşmesi beklenmektedir,'
                    },
                    {
                        'product_code': '03.1.23.0000.00.00.00',
                        'product_name': 'KCR739 11"-14,5" GEZ KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': 'Gez kamlı tamburu farklı'
                    },
                    {
                        'product_code': '03.1.24.0000.00.00.00',
                        'product_name': '556 HMT – ARPACIK KOMPLESİ',
                        'customer': ss_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.25.0000.00.00.00',
                        'product_name': 'KCR556-7,5" GEZ KOMPLESİ (L-R)',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    },
                    {
                        'product_code': '03.1.26.0000.00.00.00',
                        'product_name': 'KMG762 GEZ KOMPLESİ',
                        'customer': kk_customer,
                        'current_stock': 100,
                        'description': None
                    }
                ]

                # Create products
                created_count = 0
                skipped_count = 0
                for product_data in products_data:
                    defaults = {
                        'product_name': product_data['product_name'],
                        'product_type': 'MONTAGED',
                        'description': product_data['description'],
                        'current_stock': product_data['current_stock'],
                        'customer': product_data['customer'],
                        'inventory_category': mamul_category,
                    }
                    
                    _, created = Product.objects.get_or_create(
                        product_code=product_data['product_code'],
                        defaults=defaults
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(f"Created product: {product_data['product_code']}")
                    else:
                        skipped_count += 1
                        self.stdout.write(f"Skipped existing product: {product_data['product_code']}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded montaged products data. '
                        f'Created: {created_count}, Skipped: {skipped_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading montaged products data: {str(e)}')
            )
            raise 