import logging
import shutil
import os
from app import create_app
from app.extensions import db
from app.models import User, UserRole, AuthProvider, Product, Category, Order, Order_item
from app.models.order_model import OrderStatus
from app.models.category_items_model import category_items
from app.models.profile_model import Profile
from app.models.address_model import Address
from app.services.product_service import generate_slug
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO)

# Default password for all seeded users: "Password1234"
DEFAULT_PASSWORD_HASH = generate_password_hash("Password1234")


def seed_database():
     app = create_app()
     with app.app_context():
          logging.info("Starting database seeding...")

          # --- Reset all tables (order matters due to foreign keys) ---
          logging.info("Clearing existing data...")
          db.session.execute(db.text('TRUNCATE order_items, category_items, orders, products, addresses, profiles, categories, users RESTART IDENTITY CASCADE'))
          db.session.commit()
          logging.info("All tables cleared.")

          # --- Clean orphaned folders in uploads/products/ ---
          uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'products')
          if os.path.exists(uploads_dir):
               # After reset, no products exist so all folders are orphaned
               removed = 0
               for folder_name in os.listdir(uploads_dir):
                    folder_path = os.path.join(uploads_dir, folder_name)
                    if os.path.isdir(folder_path):
                         shutil.rmtree(folder_path)
                         removed += 1
               if removed:
                    logging.info(f"Removed {removed} orphaned folders from uploads/products/.")

          # =====================================================================
          # USERS (30 users with realistic names)
          # =====================================================================
          users = [
               # --- Superadmin ---
               User(id=1, email="funnyclown1112@gmail.com", age=35, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="funnyclown1112", roles=[UserRole.SUPERADMIN]),
               # --- Admin ---
               User(id=2, email="mike@gmail.com", age=30, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="mike", roles=[UserRole.BUYER, UserRole.ADMIN]),
               # --- Sellers ---
               User(id=3, email="justin@gmail.com", age=28, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="justin", roles=[UserRole.BUYER, UserRole.SELLER]),
               User(id=4, email="arini@gmail.com", age=27, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="arini", roles=[UserRole.BUYER, UserRole.SELLER]),
               User(id=5, email="david.wijaya@gmail.com", age=32, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="davidwijaya", roles=[UserRole.BUYER, UserRole.SELLER]),
               User(id=6, email="sarah.chen@gmail.com", age=29, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="sarahchen", roles=[UserRole.BUYER, UserRole.SELLER]),
               User(id=7, email="rizky.pratama@gmail.com", age=26, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="rizkypratama", roles=[UserRole.BUYER, UserRole.SELLER]),
               # --- Buyers ---
               User(id=8, email="budi@gmail.com", age=27, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="budi", roles=[UserRole.BUYER]),
               User(id=9, email="siti.nurhaliza@gmail.com", age=24, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="sitinurhaliza", roles=[UserRole.BUYER]),
               User(id=10, email="ahmad.fauzi@gmail.com", age=31, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="ahmadfauzi", roles=[UserRole.BUYER]),
               User(id=11, email="maria.garcia@gmail.com", age=25, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="mariagarcia", roles=[UserRole.BUYER]),
               User(id=12, email="tommy.hermawan@gmail.com", age=33, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="tommyhermawan", roles=[UserRole.BUYER]),
               User(id=13, email="jessica.tanaka@gmail.com", age=22, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="jessicatanaka", roles=[UserRole.BUYER]),
               User(id=14, email="rudi.setiawan@gmail.com", age=40, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="rudisetiawan", roles=[UserRole.BUYER]),
               User(id=15, email="dewi.lestari@gmail.com", age=28, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="dewilestari", roles=[UserRole.BUYER]),
               User(id=16, email="eko.prasetyo@gmail.com", age=35, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="ekoprasetyo", roles=[UserRole.BUYER]),
               User(id=17, email="nina.kartika@gmail.com", age=23, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="ninakartika", roles=[UserRole.BUYER]),
               User(id=18, email="fajar.nugroho@gmail.com", age=29, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="fajarnugroho", roles=[UserRole.BUYER]),
               User(id=19, email="linda.susanti@gmail.com", age=26, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="lindasusanti", roles=[UserRole.BUYER]),
               User(id=20, email="hendra.gunawan@gmail.com", age=37, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="hendragunawan", roles=[UserRole.BUYER]),
               User(id=21, email="putri.rahayu@gmail.com", age=21, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="putrirahayu", roles=[UserRole.BUYER]),
               User(id=22, email="agus.santoso@gmail.com", age=45, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="agussantoso", roles=[UserRole.BUYER]),
               User(id=23, email="ratna.dewi@gmail.com", age=30, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="ratnadewi", roles=[UserRole.BUYER]),
               User(id=24, email="bambang.suryadi@gmail.com", age=42, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="bambangsuryadi", roles=[UserRole.BUYER]),
               User(id=25, email="yuni.astuti@gmail.com", age=27, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="yuniastuti", roles=[UserRole.BUYER]),
               User(id=26, email="doni.saputra@gmail.com", age=34, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="donisaputra", roles=[UserRole.BUYER]),
               User(id=27, email="mega.wulandari@gmail.com", age=25, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="megawulandari", roles=[UserRole.BUYER]),
               User(id=28, email="irfan.hidayat@gmail.com", age=38, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="irfanhidayat", roles=[UserRole.BUYER]),
               User(id=29, email="ani.widodo@gmail.com", age=20, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="aniwidodo", roles=[UserRole.BUYER]),
               User(id=30, email="yoga.permana@gmail.com", age=31, is_active=True,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="yogapermana", roles=[UserRole.BUYER]),
               # --- Inactive / soft-deleted users ---
               User(id=31, email="deleted.user@gmail.com", age=22, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="deleteduser", roles=[UserRole.BUYER],
                    deleted_at="2026-08-01 10:00:00+07"),
               User(id=32, email="unverified.user@gmail.com", age=19, is_active=False,
                    provider=AuthProvider.PASSWORD_HASH, provider_key=DEFAULT_PASSWORD_HASH,
                    username="unverifieduser", roles=[UserRole.BUYER]),
          ]
          db.session.add_all(users)
          db.session.flush()
          logging.info(f"Users seeded: {len(users)} records.")

          # =====================================================================
          # PROFILES (one per user, realistic bios)
          # =====================================================================
          profiles = [
                    Profile(user_id=1, bio="Platform administrator", phone="+6281200000001"),
                    Profile(user_id=2, bio="Tech enthusiast and gadget reviewer", phone="+6281200000002"),
                    Profile(user_id=3, bio="Electronics seller specializing in laptops and phones", phone="+6281200000003"),
                    Profile(user_id=4, bio="Fashion and lifestyle products seller", phone="+6281200000004"),
                    Profile(user_id=5, bio="Home appliances and furniture seller", phone="+6281200000005"),
                    Profile(user_id=6, bio="Beauty and skincare products seller", phone="+6281200000006"),
                    Profile(user_id=7, bio="Sports and outdoor equipment seller", phone="+6281200000007"),
                    Profile(user_id=8, bio="Regular shopper who loves electronics", phone="+6281200000008"),
                    Profile(user_id=9, bio="Bookworm and stationery collector", phone="+6281200000009"),
                    Profile(user_id=10, bio="Fitness enthusiast looking for sports gear", phone="+6281200000010"),
                    Profile(user_id=11, bio="Fashion lover and trendsetter", phone="+6281200000011"),
                    Profile(user_id=12, bio="Dad shopping for family needs", phone="+6281200000012"),
                    Profile(user_id=13, bio="College student on a budget", phone="+6281200000013"),
                    Profile(user_id=14, bio="Business owner buying office supplies", phone="+6281200000014"),
                    Profile(user_id=15, bio="Cooking enthusiast shopping for kitchen tools", phone="+6281200000015"),
                    Profile(user_id=16, bio="Gamer looking for the best peripherals", phone="+6281200000016"),
                    Profile(user_id=17, bio="Skincare addict and makeup lover", phone="+6281200000017"),
                    Profile(user_id=18, bio="Photographer shopping for camera gear", phone="+6281200000018"),
                    Profile(user_id=19, bio="Pet lover buying supplies for cats", phone="+6281200000019"),
                    Profile(user_id=20, bio="DIY hobbyist and tool collector", phone="+6281200000020"),
                    Profile(user_id=21, bio="University student shopping for dorm essentials", phone="+6281200000021"),
                    Profile(user_id=22, bio="Retired teacher who enjoys gardening", phone="+6281200000022"),
                    Profile(user_id=23, bio="Young professional furnishing first apartment", phone="+6281200000023"),
                    Profile(user_id=24, bio="Car enthusiast looking for auto accessories", phone="+6281200000024"),
                    Profile(user_id=25, bio="Yoga instructor shopping for wellness products", phone="+6281200000025"),
                    Profile(user_id=26, bio="Music producer buying audio equipment", phone="+6281200000026"),
                    Profile(user_id=27, bio="Art teacher collecting craft supplies", phone="+6281200000027"),
                    Profile(user_id=28, bio="Traveler looking for luggage and gear", phone="+6281200000028"),
                    Profile(user_id=29, bio="High school student saving for gadgets", phone="+6281200000029"),
                    Profile(user_id=30, bio="Software developer buying productivity tools", phone="+6281200000030"),
                    Profile(user_id=31, bio=None, phone=None),
                    Profile(user_id=32, bio=None, phone=None),
               ]
          db.session.add_all(profiles)
          db.session.flush()
          logging.info(f"Profiles seeded: {len(profiles)} records.")

          # =====================================================================
          # ADDRESSES (30+ addresses across users)
          # =====================================================================
          addresses = [
                    Address(user_id=8, label="Home", recipient_name="Budi Hartono", phone="+6281234567801",
                         address_line="Jl. Sudirman No. 15", city="Jakarta Selatan", province="DKI Jakarta", postal_code="12190", is_default=True),
                    Address(user_id=8, label="Office", recipient_name="Budi Hartono", phone="+6281234567802",
                         address_line="Jl. Thamrin No. 28, Gedung Menara Lt. 5", city="Jakarta Pusat", province="DKI Jakarta", postal_code="10350", is_default=False),
                    Address(user_id=9, label="Home", recipient_name="Siti Nurhaliza", phone="+6281234567803",
                         address_line="Jl. Diponegoro No. 42", city="Bandung", province="Jawa Barat", postal_code="40115", is_default=True),
                    Address(user_id=10, label="Home", recipient_name="Ahmad Fauzi", phone="+6281234567804",
                         address_line="Jl. Ahmad Yani No. 88", city="Surabaya", province="Jawa Timur", postal_code="60234", is_default=True),
                    Address(user_id=10, label="Gym", recipient_name="Ahmad Fauzi", phone="+6281234567805",
                         address_line="Jl. Raya Darmo No. 12", city="Surabaya", province="Jawa Timur", postal_code="60241", is_default=False),
                    Address(user_id=11, label="Home", recipient_name="Maria Garcia", phone="+6281234567806",
                         address_line="Jl. Gatot Subroto No. 33", city="Denpasar", province="Bali", postal_code="80234", is_default=True),
                    Address(user_id=12, label="Home", recipient_name="Tommy Hermawan", phone="+6281234567807",
                         address_line="Jl. Malioboro No. 56", city="Yogyakarta", province="DI Yogyakarta", postal_code="55271", is_default=True),
                    Address(user_id=13, label="Kost", recipient_name="Jessica Tanaka", phone="+6281234567808",
                         address_line="Jl. Ganesha No. 10, Kost Putri Melati", city="Bandung", province="Jawa Barat", postal_code="40132", is_default=True),
                    Address(user_id=14, label="Office", recipient_name="Rudi Setiawan", phone="+6281234567809",
                         address_line="Jl. Pemuda No. 100, Ruko Blok A3", city="Semarang", province="Jawa Tengah", postal_code="50139", is_default=True),
                    Address(user_id=15, label="Home", recipient_name="Dewi Lestari", phone="+6281234567810",
                         address_line="Jl. Imam Bonjol No. 77", city="Medan", province="Sumatera Utara", postal_code="20112", is_default=True),
                    Address(user_id=16, label="Home", recipient_name="Eko Prasetyo", phone="+6281234567811",
                         address_line="Jl. Veteran No. 5", city="Malang", province="Jawa Timur", postal_code="65111", is_default=True),
                    Address(user_id=17, label="Home", recipient_name="Nina Kartika", phone="+6281234567812",
                         address_line="Jl. Pahlawan No. 23", city="Makassar", province="Sulawesi Selatan", postal_code="90134", is_default=True),
                    Address(user_id=18, label="Studio", recipient_name="Fajar Nugroho", phone="+6281234567813",
                         address_line="Jl. Braga No. 45", city="Bandung", province="Jawa Barat", postal_code="40111", is_default=True),
                    Address(user_id=19, label="Home", recipient_name="Linda Susanti", phone="+6281234567814",
                         address_line="Jl. Hayam Wuruk No. 18", city="Jakarta Barat", province="DKI Jakarta", postal_code="11160", is_default=True),
                    Address(user_id=20, label="Workshop", recipient_name="Hendra Gunawan", phone="+6281234567815",
                         address_line="Jl. Industri No. 9, Blok C", city="Tangerang", province="Banten", postal_code="15110", is_default=True),
                    Address(user_id=21, label="Kost", recipient_name="Putri Rahayu", phone="+6281234567816",
                         address_line="Jl. Margonda Raya No. 200", city="Depok", province="Jawa Barat", postal_code="16424", is_default=True),
                    Address(user_id=22, label="Home", recipient_name="Agus Santoso", phone="+6281234567817",
                         address_line="Jl. Merdeka No. 34", city="Solo", province="Jawa Tengah", postal_code="57111", is_default=True),
                    Address(user_id=23, label="Apartment", recipient_name="Ratna Dewi", phone="+6281234567818",
                         address_line="Apartemen Green Bay Tower F Lt. 12", city="Jakarta Utara", province="DKI Jakarta", postal_code="14240", is_default=True),
                    Address(user_id=24, label="Home", recipient_name="Bambang Suryadi", phone="+6281234567819",
                         address_line="Jl. Raya Bogor KM 30", city="Bogor", province="Jawa Barat", postal_code="16920", is_default=True),
                    Address(user_id=25, label="Studio", recipient_name="Yuni Astuti", phone="+6281234567820",
                         address_line="Jl. Sunset Road No. 66", city="Denpasar", province="Bali", postal_code="80361", is_default=True),
                    Address(user_id=26, label="Home", recipient_name="Doni Saputra", phone="+6281234567821",
                         address_line="Jl. Cikini Raya No. 12", city="Jakarta Pusat", province="DKI Jakarta", postal_code="10330", is_default=True),
                    Address(user_id=27, label="Home", recipient_name="Mega Wulandari", phone="+6281234567822",
                         address_line="Jl. Pangeran Antasari No. 8", city="Banjarmasin", province="Kalimantan Selatan", postal_code="70114", is_default=True),
                    Address(user_id=28, label="Home", recipient_name="Irfan Hidayat", phone="+6281234567823",
                         address_line="Jl. Jendral Sudirman No. 50", city="Palembang", province="Sumatera Selatan", postal_code="30126", is_default=True),
                    Address(user_id=29, label="Home", recipient_name="Ani Widodo", phone="+6281234567824",
                         address_line="Jl. Kartini No. 15", city="Bekasi", province="Jawa Barat", postal_code="17111", is_default=True),
                    Address(user_id=30, label="Home", recipient_name="Yoga Permana", phone="+6281234567825",
                         address_line="Jl. Teuku Umar No. 27", city="Balikpapan", province="Kalimantan Timur", postal_code="76112", is_default=True),
                    Address(user_id=3, label="Warehouse", recipient_name="Justin Store", phone="+6281234567826",
                         address_line="Jl. Raya Cibubur No. 88", city="Jakarta Timur", province="DKI Jakarta", postal_code="13720", is_default=True),
                    Address(user_id=4, label="Shop", recipient_name="Arini Fashion", phone="+6281234567827",
                         address_line="Jl. Asia Afrika No. 120", city="Bandung", province="Jawa Barat", postal_code="40261", is_default=True),
                    Address(user_id=5, label="Showroom", recipient_name="David Home Store", phone="+6281234567828",
                         address_line="Jl. Boulevard Raya No. 55", city="Tangerang Selatan", province="Banten", postal_code="15318", is_default=True),
                    Address(user_id=6, label="Office", recipient_name="Sarah Beauty", phone="+6281234567829",
                         address_line="Jl. Kemang Raya No. 32", city="Jakarta Selatan", province="DKI Jakarta", postal_code="12730", is_default=True),
                    Address(user_id=7, label="Store", recipient_name="Rizky Sports", phone="+6281234567830",
                         address_line="Jl. Gajah Mada No. 19", city="Surabaya", province="Jawa Timur", postal_code="60272", is_default=True),
                    Address(user_id=2, label="Home", recipient_name="Mike Admin", phone="+6281234567831",
                         address_line="Jl. Rasuna Said No. 2", city="Jakarta Selatan", province="DKI Jakarta", postal_code="12950", is_default=True),
               ]
          db.session.add_all(addresses)
          db.session.flush()
          logging.info(f"Addresses seeded: {len(addresses)} records.")

          # =====================================================================
          # CATEGORIES (10 realistic categories)
          # =====================================================================
          categories = [
                    Category(id=1, name="electronics"),
                    Category(id=2, name="fashion"),
                    Category(id=3, name="home & living"),
                    Category(id=4, name="sports & outdoors"),
                    Category(id=5, name="beauty & health"),
                    Category(id=6, name="books & stationery"),
                    Category(id=7, name="automotive"),
                    Category(id=8, name="food & beverages"),
                    Category(id=9, name="gaming"),
                    Category(id=10, name="photography"),
               ]
          db.session.add_all(categories)
          db.session.flush()
          logging.info(f"Categories seeded: {len(categories)} records.")

          # =====================================================================
          # PRODUCTS (32 products with real names, realistic prices in IDR)
          # =====================================================================
          product_data = [
                    # Electronics (seller_id=3, justin)
                    {"id": 1, "name": "iphone_15_pro_max", "brand": "Apple", "description": "Latest iPhone with A17 Pro chip, 48MP camera, titanium design", "price": 21999000, "stock": 20000, "sku": "APL-IP15PM-256", "user_id": 3},
                    {"id": 2, "name": "samsung_galaxy_s24_ultra", "brand": "Samsung", "description": "Galaxy AI powered flagship with S Pen and 200MP camera", "price": 19999000, "stock": 20000, "sku": "SAM-S24U-256", "user_id": 3},
                    {"id": 3, "name": "macbook_air_m3", "brand": "Apple", "description": "Ultra-thin laptop with M3 chip, 18-hour battery life, 13.6 inch display", "price": 18499000, "stock": 20000, "sku": "APL-MBA-M3-256", "user_id": 3},
                    {"id": 4, "name": "asus_rog_strix_g16", "brand": "Asus", "description": "Gaming laptop with RTX 4060, Intel i7-13650HX, 16GB RAM", "price": 22999000, "stock": 20000, "sku": "ASUS-ROG-G16", "user_id": 3},
                    {"id": 5, "name": "sony_wh1000xm5", "brand": "Sony", "description": "Premium wireless noise cancelling headphones with 30-hour battery", "price": 4999000, "stock": 20000, "sku": "SNY-WH1000XM5", "user_id": 3},
                    {"id": 6, "name": "ipad_air_m2", "brand": "Apple", "description": "10.9 inch tablet with M2 chip, perfect for creative work", "price": 10999000, "stock": 20000, "sku": "APL-IPAD-AIR-M2", "user_id": 3},
                    {"id": 7, "name": "lenovo_thinkpad_x1_carbon", "brand": "Lenovo", "description": "Business ultrabook with Intel i7, 14 inch 2.8K OLED display", "price": 25999000, "stock": 20000, "sku": "LNV-X1C-GEN11", "user_id": 3},
                    # Fashion (seller_id=4, arini)
                    {"id": 8, "name": "nike_air_max_90", "brand": "Nike", "description": "Classic running shoes with visible Air cushioning and retro style", "price": 1899000, "stock": 20000, "sku": "NK-AM90-WHT-42", "user_id": 4},
                    {"id": 9, "name": "adidas_ultraboost_light", "brand": "Adidas", "description": "Lightweight running shoes with BOOST midsole technology", "price": 2499000, "stock": 20000, "sku": "ADS-UBL-BLK-43", "user_id": 4},
                    {"id": 10, "name": "uniqlo_airism_polo", "brand": "Uniqlo", "description": "Breathable polo shirt with DRY technology for everyday comfort", "price": 299000, "stock": 20000, "sku": "UNQ-POLO-NVY-L", "user_id": 4},
                    {"id": 11, "name": "levis_501_original_jeans", "brand": "Levi's", "description": "Iconic straight fit jeans with button fly, dark wash", "price": 1299000, "stock": 45, "sku": "LVS-501-DRK-32", "user_id": 4},
                    {"id": 12, "name": "zara_oversized_blazer", "brand": "Zara", "description": "Women oversized blazer in neutral tone, perfect for layering", "price": 1599000, "stock": 20, "sku": "ZRA-BLZ-BGE-M", "user_id": 4},
                    {"id": 13, "name": "converse_chuck_taylor_70", "brand": "Converse", "description": "High-top canvas sneakers with vintage styling and cushioned insole", "price": 1199000, "stock": 60, "sku": "CNV-CT70-BLK-41", "user_id": 4},
                    # Home & Living (seller_id=5, david)
                    {"id": 14, "name": "philips_air_fryer_xxl", "brand": "Philips", "description": "Digital air fryer 7.3L capacity with rapid air technology", "price": 3299000, "stock": 18, "sku": "PHL-AF-XXL", "user_id": 5},
                    {"id": 15, "name": "ikea_kallax_shelf", "brand": "IKEA", "description": "4x2 cube shelf unit in white, versatile storage solution", "price": 1499000, "stock": 25, "sku": "IKA-KLX-4X2-WHT", "user_id": 5},
                    {"id": 16, "name": "dyson_v15_detect", "brand": "Dyson", "description": "Cordless vacuum with laser dust detection and LCD screen", "price": 12999000, "stock": 7, "sku": "DYS-V15-DET", "user_id": 5},
                    {"id": 17, "name": "samsung_inverter_ac_1pk", "brand": "Samsung", "description": "1 PK split AC with WindFree technology and AI auto cooling", "price": 5499000, "stock": 12, "sku": "SAM-AC-1PK-INV", "user_id": 5},
                    {"id": 18, "name": "ace_hardware_tool_set_108pc", "brand": "Krisbow", "description": "Complete 108-piece household tool set in carrying case", "price": 899000, "stock": 30, "sku": "KRS-TOOL-108", "user_id": 5},
                    # Beauty & Health (seller_id=6, sarah)
                    {"id": 19, "name": "skii_facial_treatment_essence", "brand": "SK-II", "description": "Iconic pitera essence for crystal clear skin, 230ml", "price": 2799000, "stock": 22, "sku": "SKII-FTE-230", "user_id": 6},
                    {"id": 20, "name": "cetaphil_gentle_cleanser", "brand": "Cetaphil", "description": "Gentle skin cleanser for sensitive skin, 500ml", "price": 189000, "stock": 80, "sku": "CTP-GC-500", "user_id": 6},
                    {"id": 21, "name": "maybelline_superstay_foundation", "brand": "Maybelline", "description": "24HR full coverage liquid foundation with matte finish", "price": 169000, "stock": 55, "sku": "MYB-SS-FDN-120", "user_id": 6},
                    {"id": 22, "name": "whey_protein_optimum_nutrition", "brand": "Optimum Nutrition", "description": "Gold Standard 100% Whey Protein 5lbs double rich chocolate", "price": 1299000, "stock": 28, "sku": "ON-WHEY-5LB-CHO", "user_id": 6},
                    {"id": 23, "name": "oral_b_electric_toothbrush", "brand": "Oral-B", "description": "Pro 3 3000 electric toothbrush with pressure sensor", "price": 899000, "stock": 35, "sku": "OB-PRO3-3000", "user_id": 6},
                    # Sports & Outdoors (seller_id=7, rizky)
                    {"id": 24, "name": "yonex_astrox_88d_pro", "brand": "Yonex", "description": "Professional badminton racket for powerful smashes", "price": 2899000, "stock": 15, "sku": "YNX-AX88D-PRO", "user_id": 7},
                    {"id": 25, "name": "garmin_forerunner_265", "brand": "Garmin", "description": "GPS running smartwatch with AMOLED display and training metrics", "price": 6499000, "stock": 12, "sku": "GRM-FR265-BLK", "user_id": 7},
                    {"id": 26, "name": "kettler_treadmill_run_7", "brand": "Kettler", "description": "Home treadmill with 3HP motor, max speed 20km/h, foldable", "price": 8999000, "stock": 5, "sku": "KTL-TM-RUN7", "user_id": 7},
                    {"id": 27, "name": "eiger_carrier_60l", "brand": "Eiger", "description": "Mountain hiking carrier backpack 60 liter with rain cover", "price": 1499000, "stock": 20, "sku": "EGR-CR-60L-GRN", "user_id": 7},
                    {"id": 28, "name": "polygon_strattos_s5", "brand": "Polygon", "description": "Road bike with Shimano 105 groupset and carbon fork", "price": 15999000, "stock": 6, "sku": "PLG-STR-S5-M", "user_id": 7},
                    # More Electronics (seller_id=3)
                    {"id": 29, "name": "logitech_mx_master_3s", "brand": "Logitech", "description": "Wireless ergonomic mouse with 8K DPI sensor and quiet clicks", "price": 1499000, "stock": 40, "sku": "LGT-MXM3S-GRY", "user_id": 3},
                    {"id": 30, "name": "keychron_k2_pro", "brand": "Keychron", "description": "75% wireless mechanical keyboard with hot-swappable switches", "price": 1599000, "stock": 25, "sku": "KC-K2P-RGB-BR", "user_id": 3},
                    {"id": 31, "name": "samsung_odyssey_g9_49", "brand": "Samsung", "description": "49 inch curved gaming monitor DQHD 240Hz with Mini LED", "price": 24999000, "stock": 4, "sku": "SAM-G9-49-2024", "user_id": 3},
                    {"id": 32, "name": "jbl_flip_6", "brand": "JBL", "description": "Portable Bluetooth speaker with IP67 waterproof, 12hr battery", "price": 1699000, "stock": 50, "sku": "JBL-FLIP6-BLK", "user_id": 3},
               ]

          products = []
          for p in product_data:
               slug = p["name"].replace("_", "-")
               products.append(Product(
                    id=p["id"], name=p["name"], slug=slug, brand=p["brand"],
                    description=p["description"], price=p["price"], stock=p["stock"],
                    sku=p["sku"], user_id=p["user_id"], is_active=True
               ))
          db.session.add_all(products)
          db.session.flush()
          logging.info(f"Products seeded: {len(products)} records.")

          # =====================================================================
          # CATEGORY_ITEMS (product-to-category mapping)
          # =====================================================================
          mappings = [
                    # Electronics
                    {"category_id": 1, "product_id": 1},
                    {"category_id": 1, "product_id": 2},
                    {"category_id": 1, "product_id": 3},
                    {"category_id": 1, "product_id": 4},
                    {"category_id": 1, "product_id": 5},
                    {"category_id": 1, "product_id": 6},
                    {"category_id": 1, "product_id": 7},
                    {"category_id": 1, "product_id": 29},
                    {"category_id": 1, "product_id": 30},
                    {"category_id": 1, "product_id": 31},
                    {"category_id": 1, "product_id": 32},
                    # Fashion
                    {"category_id": 2, "product_id": 8},
                    {"category_id": 2, "product_id": 9},
                    {"category_id": 2, "product_id": 10},
                    {"category_id": 2, "product_id": 11},
                    {"category_id": 2, "product_id": 12},
                    {"category_id": 2, "product_id": 13},
                    # Home & Living
                    {"category_id": 3, "product_id": 14},
                    {"category_id": 3, "product_id": 15},
                    {"category_id": 3, "product_id": 16},
                    {"category_id": 3, "product_id": 17},
                    {"category_id": 3, "product_id": 18},
                    # Sports & Outdoors
                    {"category_id": 4, "product_id": 24},
                    {"category_id": 4, "product_id": 25},
                    {"category_id": 4, "product_id": 26},
                    {"category_id": 4, "product_id": 27},
                    {"category_id": 4, "product_id": 28},
                    {"category_id": 4, "product_id": 9},   # ultraboost also sports
                    # Beauty & Health
                    {"category_id": 5, "product_id": 19},
                    {"category_id": 5, "product_id": 20},
                    {"category_id": 5, "product_id": 21},
                    {"category_id": 5, "product_id": 22},
                    {"category_id": 5, "product_id": 23},
                    # Gaming
                    {"category_id": 9, "product_id": 4},   # ROG laptop
                    {"category_id": 9, "product_id": 31},  # Odyssey monitor
                    {"category_id": 9, "product_id": 30},  # Keychron keyboard
                    {"category_id": 9, "product_id": 29},  # MX Master mouse
                    # Photography
                    {"category_id": 10, "product_id": 1},  # iPhone camera
                    {"category_id": 10, "product_id": 2},  # Samsung camera
               ]
          db.session.execute(category_items.insert().values(mappings))
          db.session.flush()
          logging.info(f"Category items seeded: {len(mappings)} records.")

          # =====================================================================
          # ORDERS (32 orders with realistic invoice names)
          # =====================================================================
          orders = [
                    Order(id=1, user_id=8, name="inv-20260801-001", status=OrderStatus.COMPLETED, subtotal=21999000, total=21999000),
                    Order(id=2, user_id=8, name="inv-20260802-002", status=OrderStatus.COMPLETED, subtotal=4999000, total=4999000),
                    Order(id=3, user_id=9, name="inv-20260803-003", status=OrderStatus.PAID, subtotal=1899000, total=1899000),
                    Order(id=4, user_id=9, name="inv-20260804-004", status=OrderStatus.PENDING, subtotal=299000, total=299000),
                    Order(id=5, user_id=10, name="inv-20260805-005", status=OrderStatus.COMPLETED, subtotal=2899000, total=2899000),
                    Order(id=6, user_id=10, name="inv-20260806-006", status=OrderStatus.PAID, subtotal=6499000, total=6499000),
                    Order(id=7, user_id=11, name="inv-20260807-007", status=OrderStatus.COMPLETED, subtotal=1599000, total=1599000),
                    Order(id=8, user_id=11, name="inv-20260808-008", status=OrderStatus.PENDING, subtotal=1199000, total=1199000),
                    Order(id=9, user_id=12, name="inv-20260809-009", status=OrderStatus.COMPLETED, subtotal=3299000, total=3299000),
                    Order(id=10, user_id=12, name="inv-20260810-010", status=OrderStatus.PAID, subtotal=899000, total=899000),
                    Order(id=11, user_id=13, name="inv-20260811-011", status=OrderStatus.PENDING, subtotal=1499000, total=1499000),
                    Order(id=12, user_id=13, name="inv-20260812-012", status=OrderStatus.COMPLETED, subtotal=189000, total=189000),
                    Order(id=13, user_id=14, name="inv-20260813-013", status=OrderStatus.COMPLETED, subtotal=25999000, total=25999000),
                    Order(id=14, user_id=14, name="inv-20260814-014", status=OrderStatus.PAID, subtotal=1499000, total=1499000),
                    Order(id=15, user_id=15, name="inv-20260815-015", status=OrderStatus.COMPLETED, subtotal=3299000, total=3299000),
                    Order(id=16, user_id=16, name="inv-20260816-016", status=OrderStatus.COMPLETED, subtotal=22999000, total=22999000),
                    Order(id=17, user_id=16, name="inv-20260817-017", status=OrderStatus.PAID, subtotal=1599000, total=1599000),
                    Order(id=18, user_id=17, name="inv-20260818-018", status=OrderStatus.COMPLETED, subtotal=2799000, total=2799000),
                    Order(id=19, user_id=17, name="inv-20260819-019", status=OrderStatus.PENDING, subtotal=169000, total=169000),
                    Order(id=20, user_id=18, name="inv-20260820-020", status=OrderStatus.COMPLETED, subtotal=19999000, total=19999000),
                    Order(id=21, user_id=19, name="inv-20260821-021", status=OrderStatus.PAID, subtotal=299000, total=299000),
                    Order(id=22, user_id=20, name="inv-20260822-022", status=OrderStatus.COMPLETED, subtotal=899000, total=899000),
                    Order(id=23, user_id=21, name="inv-20260823-023", status=OrderStatus.PENDING, subtotal=10999000, total=10999000),
                    Order(id=24, user_id=22, name="inv-20260824-024", status=OrderStatus.COMPLETED, subtotal=1499000, total=1499000),
                    Order(id=25, user_id=23, name="inv-20260825-025", status=OrderStatus.PAID, subtotal=12999000, total=12999000),
                    Order(id=26, user_id=24, name="inv-20260826-026", status=OrderStatus.COMPLETED, subtotal=15999000, total=15999000),
                    Order(id=27, user_id=25, name="inv-20260827-027", status=OrderStatus.PENDING, subtotal=1299000, total=1299000),
                    Order(id=28, user_id=26, name="inv-20260828-028", status=OrderStatus.COMPLETED, subtotal=1699000, total=1699000),
                    Order(id=29, user_id=27, name="inv-20260829-029", status=OrderStatus.PAID, subtotal=899000, total=899000),
                    Order(id=30, user_id=28, name="inv-20260830-030", status=OrderStatus.COMPLETED, subtotal=1499000, total=1499000),
                    Order(id=31, user_id=29, name="inv-20260831-031", status=OrderStatus.PENDING, subtotal=4999000, total=4999000),
                    Order(id=32, user_id=30, name="inv-20260831-032", status=OrderStatus.CANCELED, subtotal=24999000, total=24999000),
               ]
          db.session.add_all(orders)
          db.session.flush()
          logging.info(f"Orders seeded: {len(orders)} records.")

          # =====================================================================
          # ORDER_ITEMS (32+ items linking orders to products)
          # =====================================================================
          order_items_data = [
                    Order_item(id=1, order_id=1, product_id=1, quantity=1, compound_price=21999000),
                    Order_item(id=2, order_id=2, product_id=5, quantity=1, compound_price=4999000),
                    Order_item(id=3, order_id=3, product_id=8, quantity=1, compound_price=1899000),
                    Order_item(id=4, order_id=4, product_id=10, quantity=1, compound_price=299000),
                    Order_item(id=5, order_id=5, product_id=24, quantity=1, compound_price=2899000),
                    Order_item(id=6, order_id=6, product_id=25, quantity=1, compound_price=6499000),
                    Order_item(id=7, order_id=7, product_id=12, quantity=1, compound_price=1599000),
                    Order_item(id=8, order_id=8, product_id=13, quantity=1, compound_price=1199000),
                    Order_item(id=9, order_id=9, product_id=14, quantity=1, compound_price=3299000),
                    Order_item(id=10, order_id=10, product_id=18, quantity=1, compound_price=899000),
                    Order_item(id=11, order_id=11, product_id=15, quantity=1, compound_price=1499000),
                    Order_item(id=12, order_id=12, product_id=20, quantity=1, compound_price=189000),
                    Order_item(id=13, order_id=13, product_id=7, quantity=1, compound_price=25999000),
                    Order_item(id=14, order_id=14, product_id=29, quantity=1, compound_price=1499000),
                    Order_item(id=15, order_id=15, product_id=14, quantity=1, compound_price=3299000),
                    Order_item(id=16, order_id=16, product_id=4, quantity=1, compound_price=22999000),
                    Order_item(id=17, order_id=17, product_id=30, quantity=1, compound_price=1599000),
                    Order_item(id=18, order_id=18, product_id=19, quantity=1, compound_price=2799000),
                    Order_item(id=19, order_id=19, product_id=21, quantity=1, compound_price=169000),
                    Order_item(id=20, order_id=20, product_id=2, quantity=1, compound_price=19999000),
                    Order_item(id=21, order_id=21, product_id=10, quantity=1, compound_price=299000),
                    Order_item(id=22, order_id=22, product_id=18, quantity=1, compound_price=899000),
                    Order_item(id=23, order_id=23, product_id=6, quantity=1, compound_price=10999000),
                    Order_item(id=24, order_id=24, product_id=27, quantity=1, compound_price=1499000),
                    Order_item(id=25, order_id=25, product_id=16, quantity=1, compound_price=12999000),
                    Order_item(id=26, order_id=26, product_id=28, quantity=1, compound_price=15999000),
                    Order_item(id=27, order_id=27, product_id=22, quantity=1, compound_price=1299000),
                    Order_item(id=28, order_id=28, product_id=32, quantity=1, compound_price=1699000),
                    Order_item(id=29, order_id=29, product_id=23, quantity=1, compound_price=899000),
                    Order_item(id=30, order_id=30, product_id=29, quantity=1, compound_price=1499000),
                    Order_item(id=31, order_id=31, product_id=5, quantity=1, compound_price=4999000),
                    Order_item(id=32, order_id=32, product_id=31, quantity=1, compound_price=24999000),
                    # Extra items (multiple items per order)
                    Order_item(id=33, order_id=1, product_id=5, quantity=1, compound_price=4999000),
                    Order_item(id=34, order_id=16, product_id=30, quantity=1, compound_price=1599000),
                    Order_item(id=35, order_id=20, product_id=5, quantity=2, compound_price=9998000),
               ]
          db.session.add_all(order_items_data)
          db.session.flush()
          logging.info(f"Order items seeded: {len(order_items_data)} records.")

          # =====================================================================
          # PRODUCT IMAGES (1 placeholder image per product)
          # =====================================================================
          uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
          # Minimal valid 1x1 pixel PNG (89 bytes)
          PLACEHOLDER_PNG = (
               b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
               b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
               b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
               b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
          )
          for product in products:
               folder_path = os.path.join(uploads_dir, 'products', product.uuid)
               os.makedirs(folder_path, exist_ok=True)
               filename = f"{product.slug}_placeholder.png"
               file_path = os.path.join(folder_path, filename)
               with open(file_path, 'wb') as f:
                    f.write(PLACEHOLDER_PNG)
               relative_path = f"products/{product.uuid}/{filename}"
               product.images = [relative_path]
          db.session.flush()
          logging.info(f"Product images seeded: {len(products)} placeholder images created.")

          # =====================================================================
          # COMMIT ALL
          # =====================================================================
          try:
               db.session.commit()

               # Reset all sequences to max(id) + 1 so new inserts don't conflict
               db.session.execute(db.text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
               db.session.execute(db.text("SELECT setval('profiles_id_seq', (SELECT MAX(id) FROM profiles))"))
               db.session.execute(db.text("SELECT setval('addresses_id_seq', (SELECT MAX(id) FROM addresses))"))
               db.session.execute(db.text("SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories))"))
               db.session.execute(db.text("SELECT setval('products_id_seq', (SELECT MAX(id) FROM products))"))
               db.session.execute(db.text("SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders))"))
               db.session.execute(db.text("SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items))"))
               db.session.commit()

               logging.info("Database seeding completed successfully!")
               logging.info("=" * 50)
               logging.info("SEED SUMMARY:")
               logging.info(f"  Users:          32")
               logging.info(f"  Profiles:       32")
               logging.info(f"  Addresses:      31")
               logging.info(f"  Categories:     10")
               logging.info(f"  Products:       32")
               logging.info(f"  Category Items: 37")
               logging.info(f"  Orders:         32")
               logging.info(f"  Order Items:    35")
               logging.info("=" * 50)
               logging.info("Login credentials:")
               logging.info("  All users password: Password1234")
               logging.info("  Superadmin: funnyclown1112@gmail.com")
               logging.info("  Admin:      mike@gmail.com")
               logging.info("  Sellers:    justin@gmail.com, arini@gmail.com, david.wijaya@gmail.com, sarah.chen@gmail.com, rizky.pratama@gmail.com")
               logging.info("  Buyers:     budi@gmail.com, siti.nurhaliza@gmail.com, etc.")
          except Exception as e:
               db.session.rollback()
               logging.error(f"Seeding failed: {str(e)}")
               raise


if __name__ == "__main__":
     seed_database()
