# Product Refactoring

## All
- [ ] test\_upload.py
9:from app.models import Product, User, UserRole
16:    product = Product.query.filter(Product.deleted\_at.is\_(None)).first()
26:    print(f"Product: {product.name} (ID: {product.id}, UUID: {product.uuid}, Slug: {product.slug})")

- [ ] seeds/initial\_seed.py
6:from app.models import User, UserRole, AuthProvider, Product, SellerProduct, Category, Order, Order\_item
362:               products.append(Product(
373:          products.append(Product(

- [ ] app/\_\_init\_\_.py
69:        from app.models import User, Product, SellerProduct, Order, Category, category\_items, Order\_item, Profile, Address

## Models
- [ ] app/models/seller\_product\_model.py
14:    A single seller's offer (listing) for a catalog \`Product\`.
42:    # Product.listings for the reverse direction.
43:    catalog = db.relationship('Product', backref='listings')

- [ ] app/models/product\_model.py
17:class Product(db.Model):

- [ ] app/models/\_\_init\_\_.py
2:from app.models.product\_model import Product, ProductStatus
15:    'Product', 

## Schemas

- [ ] app/schemas/order\_item\_schema.py
24:        error\_messages={"required": "Product ID is required."}
45:        "summary": "Product ID Not Provided",
48:            "errors": {"json": {"product\_id": ["Product ID is required."]}},
91:        "summary": "Product ID Not Found",
94:            "errors": "Product with id '99' is not found.",
100:        "summary": "Product Already Exists in Order",
103:            "errors": "Product already exists in this order.",

- [ ] app/schemas/product\_schema.py
3:from app.models import Product
14:        model                 = Product
29:        validate=ma.validate.Length(min=1, error="Product name cannot be empty."),
30:        error\_messages={"required": "Product name is not provided."}
68:        model                 = Product

- [ ] app/schemas/payment\_schema.py
106:        "summary": "Product No Longer Available",
109:            "message": "Product with id '5' is no longer available",

- [ ] app/schemas/seller\_product\_schema.py
20:                         error\_messages={"required": "Product name is not provided."})
-e 
## Routes

- [ ] app/routes/v1/category\_routes\_v1.py
163:# NOTE: GET /categories/<id>/products was removed. Product listing by category

- [ ] app/routes/v1/product\_routes\_v1.py
31:    description='Product Data Operations'
81:            return jsonify({"success": True, "message": "Product created successfully", "data": product.to\_dict()}), 201
99:            abort(404, message="Product is not found")
125:            return jsonify({"success": True, "message": "Product updated successfully", "data": product.to\_dict()}), 200

- [ ] app/routes/v1/admin\_routes\_v1.py
4:from app.models import Product, Order, UserRole
30:        query = query.filter(Product.name.ilike(f"%{search}%"))
34:        query = query.filter(Product.categories.any(Category.id == category\_id))
42:        query = query.filter(Product.deleted\_at.is\_(None))
45:    sort\_columns = {"name": Product.name, "created\_at": Product.created\_at}
51:        query = query.order\_by(Product.id.asc())
93:        query = \_apply\_admin\_product\_filters(Product.query, query\_args)
266:        query = Product.query.filter(Product.categories.any(Category.id == category\_id))
-e 
## Services

- [ ] app/services/upload\_service.py
5:from app.models import Product, SellerProduct, UserRole

- [ ] app/services/product\_service.py
13:from app.models import Product, SellerProduct, ProductStatus, UserRole
39:        query = query.filter(Product.name.ilike(f"%{search}%"))
43:        query = query.filter(Product.categories.any(Category.id == category\_id))
47:        query = query.filter(Product.categories.any(Category.name.ilike(f"%{category\_name}%")))
50:    sort\_columns = {"name": Product.name, "created\_at": Product.created\_at}
57:        query = query.order\_by(Product.id.asc())
70:        query = Product.query.filter(Product.deleted\_at.is\_(None))
72:            query = query.filter(Product.id.in\_(\_catalog\_has\_active\_listing\_subquery()))
84:        product = Product.query.filter(
85:            Product.id == product\_id,
86:            Product.deleted\_at.is\_(None),
107:    \`product\_instance\` is a Product model built by ProductSchema(load\_instance).
138:        product = Product.query.filter(
139:            Product.id == product\_id,
140:            Product.deleted\_at.is\_(None),
143:            return ValidationResponse(success=False, message="Product not found")
179:        product = Product.query.filter(Product.id == product\_id).first()
181:            return ValidationResponse(success=False, message="Product not found", status\_code=404)
211:            return ValidationResponse(success=True, message=f"Product {product\_id} permanently deleted", status\_code=200)
214:            return ValidationResponse(success=False, message="Product is already deleted", status\_code=400)
218:        return ValidationResponse(success=True, message=f"Product {product\_id} soft-deleted", status\_code=200)

- [ ] app/services/payment\_service.py
6:from app.models import Order, OrderStatus, Product, SellerProduct, ProductStatus

- [ ] app/services/seller\_product\_service.py
4:A \`SellerProduct\` is one seller's offer for a catalog \`Product\`. This module owns:
23:    Product, SellerProduct, ProductStatus, UserRole,
95:            .join(Product, Product.id == SellerProduct.product\_id)
97:                Product.deleted\_at.is\_(None),
108:                Product.brand.ilike(like),
109:                Product.name.ilike(like),
110:                Product.model.ilike(like),
116:            query = query.filter(Product.categories.any(Category.id == category\_id))
219:    Returns (Product, error\_or\_None).
224:        catalog = Product.query.filter(
225:            Product.barcode == barcode,
226:            Product.deleted\_at.is\_(None),
232:    catalog = Product(

- [ ] app/services/order\_service.py
5:from app.models import Order, OrderStatus, Product, SellerProduct, ProductStatus, UserRole
160:                .join(Product, Product.id == SellerProduct.product\_id)
165:                    Product.deleted\_at.is\_(None),
-e 
## Tests

- [ ] tests/services/test\_payment\_service.py
10:from app.models.product\_model import Product, ProductStatus
61:        p = Product(user\_id=seller.id, name=f'PProd{n}', slug=f'pprod{n}', uuid=f'puuid{n}',

- [ ] tests/services/test\_upload\_service.py
5:from app.models import User, Product, ProductStatus
78:        prod = Product(user\_id=seller.id, name='UplProd', slug='uplprod', uuid='upluuid1',
93:        prod = Product(user\_id=seller.id, name='UplOk', slug='uplok', uuid='uplokuuid',
115:        prod = Product(user\_id=seller.id, name='UplMax', slug='uplmax', uuid='uplmaxuuid',
150:        prod = Product(user\_id=seller.id, name='DelProd', slug='delprod-upl', uuid='deluuid1',
165:        prod = Product(user\_id=seller.id, name='NoImg', slug='noimg', uuid='noimguuid',
180:        prod = Product(user\_id=seller.id, name='DelOk', slug='delok', uuid='delokuuid',

- [ ] tests/services/test\_product\_service.py
1:from app.models import User, Product, ProductStatus
36:            product = Product(user\_id=seller.id, name='del\_prod', slug='del-prod', uuid='uuid-del',
51:        product = Product(user\_id=seller.id, name='soft\_prod', slug='soft-prod', uuid='uuid-soft',
61:        """Product linked to a PAID order cannot be deleted (409)."""
72:        product = Product(user\_id=seller.id, name='paid\_prod', slug='paid-prod', uuid='uuid-paid',
97:        product = Product(name='new\_prod', brand='b', description='d',
113:        product = Product(name='badcat\_prod', brand='b', description='d',
129:        product = Product(user\_id=seller.id, name='old\_prod', slug='old-prod', uuid='uuid-upd',
148:        product = Product(user\_id=owner.id, name='owned', slug='owned-prod', uuid='uuid-owned',

- [ ] tests/services/test\_order\_service.py
53:from app.models import User, Product, ProductStatus, Order, Category
71:            product = Product(user\_id=seller.id, name='test prod', slug='test-prod-1', uuid='uuid1',
97:            product = Product(user\_id=seller.id, name='low stock', slug='low-stock-1', uuid='uuid2',

- [ ] tests/routes/v1/test\_admin\_routes.py
15:    @patch('app.routes.v1.admin\_routes\_v1.Product')
59:from app.models import User, Product, ProductStatus, Order, Category, Profile, Address
76:        p1 = Product(user\_id=seller.id, name='active prod', slug='active-prod-adm', uuid='uadm1',
78:        p2 = Product(user\_id=seller.id, name='deleted prod', slug='deleted-prod-adm', uuid='uadm2',

- [ ] tests/routes/v1/test\_product\_routes.py
65:        mock\_svc.return\_value = ValidationResponse(success=True, message="Product 1 soft-deleted", status\_code=200)
72:        mock\_svc.return\_value = ValidationResponse(success=False, message="Product not found", status\_code=404)
86:from app.models import User, Product, ProductStatus, Order, Category
126:        prod = Product(user\_id=seller.id, name='GetProd', slug='getprod', uuid='getprod-uuid',
144:        p1 = Product(user\_id=seller.id, name='Prod1', slug='prod1-int', uuid='p1uuid',
146:        p2 = Product(user\_id=seller.id, name='Prod2', slug='prod2-int', uuid='p2uuid',
160:        prod = Product(user\_id=seller.id, name='OldName', slug='oldname-upd', uuid='upduuid',
178:        prod = Product(user\_id=seller.id, name='DelProd', slug='delprod-int', uuid='deluuid',
193:        prod = Product(user\_id=seller.id, name='HardDel', slug='harddel-int', uuid='harduuid',
213:        prod = Product(user\_id=seller.id, name='LinkedProd', slug='linkedprod', uuid='linkuuid',

- [ ] tests/routes/v1/test\_order\_routes.py
60:from app.models import User, Product, ProductStatus, Order, Category
79:        prod = Product(user\_id=seller.id, name='OrdProd', slug='ordprod', uuid='orduuid1',
104:        prod = Product(user\_id=seller.id, name='LowStock', slug='lowstock', uuid='lowuuid',
202:        prod = Product(user\_id=seller.id, name='UpdProd', slug='updprod-ord', uuid='upduuid2',
231:        prod = Product(user\_id=seller.id, name='CancelProd', slug='cancelprod', uuid='canceluuid',
262:        prod = Product(user\_id=seller.id, name='HardDelProd', slug='harddelprod-ord', uuid='hdorduuid',
295:        prod = Product(user\_id=seller.id, name='OrdProdGet', slug='ordprodget', uuid='opgtuuid',
326:        prod = Product(user\_id=seller.id, name='DupProd', slug='dupprod-ord', uuid='dupuuid2',

- [ ] tests/routes/v1/test\_category\_routes.py
71:from app.models import User, Product, Category
82:from app.models import Category, Product, User, ProductStatus
168:        prod = Product(user\_id=seller.id, name='catprod1', slug='catprod1', uuid='cpuuid1',
