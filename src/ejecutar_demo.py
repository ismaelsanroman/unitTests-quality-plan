# Supón que esto está en un archivo llamado demo.py

from src.demo import Coupon, Product, ShoppingCart

# Crear productos
camiseta = Product("Camiseta", 20.0)
pantalon = Product("Pantalón", 35.0)
gorra = Product("Gorra", 15.0)

# Crear un carrito
carrito = ShoppingCart()

# 🛒 Añadir productos
carrito.add_product(camiseta)
carrito.add_product(pantalon)
carrito.add_product(gorra)

print("Total sin descuento:", carrito.total())  # → 70.0

# 💳 Aplicar un cupón
cupon10 = Coupon("DESCUENTO10", 10)
carrito.apply_coupon(cupon10)

print("Total con 10% de descuento:", carrito.total())  # → 63.0

# ❌ Intentar aplicar otro cupón (debería fallar)
try:
    otro_cupon = Coupon("20OFF", 20)
    carrito.apply_coupon(otro_cupon)
except ValueError as e:
    print("Error esperado al aplicar segundo cupón:", e)

# 🧽 Eliminar un producto
carrito.remove_product("Gorra")
print("Total después de eliminar la gorra:", carrito.total())  # → 49.5

# 🧼 Limpiar el carrito
carrito.clear()
print("Total después de limpiar el carrito:", carrito.total())  # → 0.0
