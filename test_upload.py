"""
Test script: Upload a random test image to an existing product.
Run: python test_upload.py
"""
import io
import random
from app import create_app
from app.extensions import db
from app.models import Product, User, UserRole
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Find a product with a seller
    product = Product.query.filter(Product.deleted_at.is_(None)).first()
    if not product:
        print("No products found. Create a product first.")
        exit(1)

    seller = User.query.get(product.user_id)
    if not seller:
        print(f"Seller (user_id={product.user_id}) not found.")
        exit(1)

    print(f"Product: {product.name} (ID: {product.id}, UUID: {product.uuid}, Slug: {product.slug})")
    print(f"Seller: {seller.email} (ID: {seller.id})")

    # Generate a JWT token for the seller
    token = create_access_token(
        identity=str(seller.id),
        additional_claims={
            "roles": [r.value for r in seller.roles],
            "email": seller.email,
        }
    )

    # Create a fake 1x1 PNG image (smallest valid PNG)
    # PNG header + IHDR + IDAT + IEND
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    with app.test_client() as client:
        # Upload via multipart form
        data = {
            'resource': 'products',
            'resource_id': str(product.id),
            'file': (io.BytesIO(png_data), f'test_image_{random.randint(1000,9999)}.png')
        }

        resp = client.post(
            '/api/v1/uploads/',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {token}'}
        )

        print(f"\nStatus: {resp.status_code}")
        print(f"Response: {resp.get_json()}")

        # Verify product images updated
        db.session.refresh(product)
        print(f"\nProduct images array: {product.images}")
