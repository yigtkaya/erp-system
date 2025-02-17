from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Product, InventoryCategory
from erp_core.models import Customer

class Command(BaseCommand):
    help = 'Loads single parts data into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading single parts data...')

        try:
            with transaction.atomic():
                # Get or create the MAMUL category
                mamul_category, _ = InventoryCategory.objects.get_or_create(
                    name='MAMUL',
                    defaults={'description': 'Finished and Single Products'}
                )

                # Single parts data from SQL
                products_data = [
                    {
                        'product_code': '03.0.00.0001.00.00.00',
                        'product_name': 'MPT NAMLU BAĞLAMA SOMUNU',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0002.00.00.00',
                        'product_name': 'KCR NAMLU BAĞLAMA SOMUNU',
                        'customer': None,
                        'current_stock': 100,
                                'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category    
                    },
                    {
                        'product_code': '03.0.00.0003.00.00.00',
                        'product_name': 'KCR DİPÇİK TÜPÜ BAĞLAMA SOMUNU',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0004.00.00.00',
                        'product_name': 'KGL GÖVDE',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0004.14.00.00',
                        'product_name': 'KGL GÖVDE',
                        'customer': None,
                        'current_stock': 100,
                            'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0005.00.00.00',
                        'product_name': 'OBA Tetik Tertibatı Hamili',
                        'customer': None,
                        'current_stock': 100,
                            'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0005.0B.00.00',
                        'product_name': 'OBA TETİK TERTİBATI HAMİLİ YERLİ',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0006.00.00.00',
                        'product_name': 'KCR556 QD KİLİT DİLİ',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0007.00.00.00',
                        'product_name': 'KCR556 QD KİLİT',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0008.00.00.00',
                        'product_name': 'KCR556 BASTIRICI KAPAK',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0010.00.00.00',
                        'product_name': 'PASLANMAZ ÖZEL VİDA İMALATI',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0011.00.00.00',
                        'product_name': 'RULMAN DAYAMASI',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0012.00.00.00',
                        'product_name': 'DIS_BAGLAMA_PIMI_r0',
                        'customer': None,
                        'current_stock': 100,
                            'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0013.00.00.00',
                        'product_name': 'IC_MANDAL_PIMI_r0',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0014.00.00.00',
                        'product_name': 'UZUN_ARA_PIM_r0',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0015.00.00.00',
                        'product_name': 'KISA_ARA_PIM_r0',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0016.00.00.00',
                        'product_name': 'BAGLANTI_SILINDIRI_r0',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0017.00.00.00',
                        'product_name': 'KGL 38 GÖVDE',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0017.01.00.00',
                        'product_name': 'KGL 38 GÖVDE V2',
                        'customer': None,
                        'current_stock': 100,
                            'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0018.00.00.00',
                        'product_name': 'KGL 38 Bağlantı Bacağı',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0019.00.00.00',
                        'product_name': 'CAR816 El Kundağı Alt',
                        'customer': None,
                        'current_stock': 1440,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0019.01.00.00',
                        'product_name': 'CAR816 El Kundağı Alt',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0020.00.00.00',
                        'product_name': 'CAR816 El Kundağı Üst',
                        'customer': None,
                        'current_stock': 1854,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0020.01.00.00',
                        'product_name': 'CAR816 El Kundağı Üst',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0021.00.00.00',
                        'product_name': 'CAR816 GAZ PİSTON HAMİLİ',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0021.01.00.00',
                        'product_name': 'CAR816 GAZ PİSTON HAMİLİ',
                            'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0022.00.00.00',
                        'product_name': 'OBA Tetik Tertibatı Hamili',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0023.00.00.00',
                        'product_name': 'OBA Sandık Tertibatı Tetik Tutucu',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0024.00.00.00',
                        'product_name': 'OBA Kilit Levhası Gövdesi',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0025.00.00.00',
                        'product_name': 'OBA  Dış Kızak',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0026.00.00.00',
                        'product_name': 'OBA Yay Hamili',
                        'customer': None,
                        'current_stock': 100,
                        'description': 'MKI ve teknik resim yok',
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0027.00.00.00',
                        'product_name': 'OBA Kızak',
                        'customer': None,
                        'current_stock': 100,
                        'description': '',
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0028.00.00.00',
                        'product_name': 'OBA Mühimmat Besleme Yatağı',
                        'customer':None,
                        'current_stock': 100,
                        'description': '',
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0029.00.00.00',
                        'product_name': 'OBA Mekanizma (A2)',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0030.00.00.00',
                        'product_name': 'OBA Sandık Üst Kapağı Gövdesi',
                        'customer': None,   
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0031.00.00.00',
                        'product_name': 'M7_209060_10050002 GEZ ',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0032.00.00.00',
                        'product_name': 'OBA Ateşleme İğnesi Kilit Mandalı',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0033.00.00.00',
                        'product_name': 'OBA Tırnak Sağ',
                        'customer': None,
                        'current_stock': 100,
                                'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0034.00.00.00',
                        'product_name': 'OBA Tırnak Sol',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0035.00.00.00',
                        'product_name': 'KCR556 739 GEZ KAMLI TAMBUR',
                        'customer': None,
                        'current_stock': 100,
                        'description': 'Isıl işlem için KK a gönderilecektir.',
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.00.0036.00.00.00',
                        'product_name': 'Piston Prob',
                        'customer': None,
                        'current_stock': 100,
                            'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.10.0001.00.00.00',
                        'product_name': 'KMG5-P405 - UST_MEKANIZMA_GOVDESI',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.10.0001.01.00.00',
                        'product_name': 'KMG5 MK - P405 Üst Mekanizma Gövdesi',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.12.0001.00.00.00',
                        'product_name': 'KMG5 P301 Üst Kapak',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.12.0004.00.00.00',
                        'product_name': 'KMG5 P304 Kapak Kilidi',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.12.0020.00.00.00',
                        'product_name': 'KMG5 BK - P320 Besleme Manivelası',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    },
                    {
                        'product_code': '03.0.13.0001.00.00.00',
                        'product_name': 'KMG5 P404 Alt Mekanizma Gövdesi',
                        'customer': None,
                        'current_stock': 100,
                        'description': None,
                        'product_type': 'SINGLE',
                        'inventory_category': mamul_category
                    }
                ]

                # Create products
                created_count = 0
                skipped_count = 0
                for product_data in products_data:
                    # Get or create customer if customer code exists
                    customer = None
                    if product_data.get('customer_code') and product_data['customer_code'].strip():
                        customer, _ = Customer.objects.get_or_create(
                            code=product_data['customer_code'],
                            defaults={'name': f"Customer {product_data['customer_code']}"}
                        )

                    defaults = {
                        'product_name': product_data['product_name'],
                        'product_type': 'SINGLE',
                        'description': product_data['description'],
                        'current_stock': product_data['current_stock'],
                        'customer': customer,
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
                        f'Successfully loaded single parts data. '
                        f'Created: {created_count}, Skipped: {skipped_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading single parts data: {str(e)}')
            )
            raise 