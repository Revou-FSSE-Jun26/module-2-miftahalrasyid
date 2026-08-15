# seed.py
import logging
from app import create_app
from app import db
from app.models import User, Product, Category

# Mengaktifkan logging agar proses terlihat di terminal
logging.basicConfig(level=logging.INFO)

def seed_database():
    app = create_app()
    with app.app_context():
        logging.info("Memulai proses seeding database...")
        
        # 1. Hapus data lama jika ada (Opsional, agar tidak duplikat saat dijalankan ulang)
        # db.drop_all() # Jangan diaktifkan jika tidak ingin menghapus tabel
        
        # 2. Tambah Data Kategori Awal
        if not Category.query.first():
            cat_elektronik = Category(name="Elektronik")
            cat_pakaian = Category(name="Pakaian")
            db.session.add_all([cat_elektronik, cat_pakaian])
            db.session.flush() # Mendapatkan ID kategori sebelum commit
            logging.info("✓ Data Kategori berhasil ditambahkan.")
        
        # 3. Tambah Data User Awal (Memicu @password.setter otomatis)
        if not User.query.filter_by(email="budi@gmail.com").first():
            user_budi = User(
                username="miftah",
                email="rasyidmiftah67@gmail.com",
                age=32,
                password="admin123", # Otomatis di-hash SHA-256 oleh model Anda!
                role="SUPERADMIN"
            )
            db.session.add(user_budi)
            logging.info("✓ Data User Budi berhasil ditambahkan.")

        # 4. Tambah Data Produk Awal
        if not Product.query.first():
            # Mengasumsikan user_id=1 dan category_id=1 ada
            produk_1 = Product(
                name="Smartphone Pro",
                quantity=10,
                brand="Rovodev Tech",
                description="Smartphone canggih untuk developer",
                price=5000000,
                user_id=1
            )
            db.session.add(produk_1)
            logging.info("✓ Data Produk berhasil ditambahkan.")

        # 5. Commit Semua Transaksi ke Database
        try:
            db.session.commit()
            logging.info("🎉 Seeding Database Selesai dengan Sukses!")
        except Exception as e:
            db.session.rollback()
            logging.error(f"❌ Gagal melakukan seeding: {str(e)}")

if __name__ == "__main__":
    seed_database()
