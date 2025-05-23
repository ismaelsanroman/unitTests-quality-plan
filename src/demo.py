class Product:
    def __init__(self, name: str, price: float):
        if price < 0:
            raise ValueError("El precio no puede ser negativo.")
        self.name = name
        self.price = price


class Coupon:
    def __init__(self, code: str, discount: float):
        if not (0 < discount <= 100):
            raise ValueError("El descuento debe estar entre 0 y 100.")
        self.code = code
        self.discount = discount


class ShoppingCart:
    def __init__(self):
        self.products = []
        self.applied_coupon = None

    def add_product(self, product: Product):
        self.products.append(product)

    def remove_product(self, product_name: str):
        original_count = len(self.products)
        self.products = [p for p in self.products if p.name != product_name]
        if len(self.products) == original_count:
            raise ValueError("Producto no encontrado en el carrito.")

    def apply_coupon(self, coupon: Coupon):
        if self.applied_coupon is not None:
            raise ValueError("Ya hay un cupón aplicado.")
        self.applied_coupon = coupon

    def total(self) -> float:
        subtotal = sum(p.price for p in self.products)
        if self.applied_coupon:
            subtotal *= 1 - self.applied_coupon.discount / 100
        return round(subtotal, 2)

    def clear(self):
        self.products = []
        self.applied_coupon = None
