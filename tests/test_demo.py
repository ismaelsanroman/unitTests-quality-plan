import pytest

from src.demo import Coupon, Product, ShoppingCart


@pytest.fixture
def productos_ejemplo():
    camiseta = Product("Camiseta", 20.0)
    pantalon = Product("Pantalón", 35.0)
    gorra = Product("Gorra", 15.0)
    return camiseta, pantalon, gorra


@pytest.fixture
def coupon_ejemplo():
    cup10 = Coupon("DESCUENTO10", 10)
    cup30 = Coupon("DESCUENTO30", 30)
    cup50 = Coupon("DESCUENTO50", 50)
    return cup10, cup30, cup50


@pytest.fixture
def shopping_cart_ejemplo():
    return ShoppingCart()


def test_total_sin_cupon(shopping_cart_ejemplo, productos_ejemplo):
    camiseta, pantalon, gorra = productos_ejemplo
    carrito = shopping_cart_ejemplo

    carrito.add_product(camiseta)
    carrito.add_product(pantalon)
    carrito.add_product(gorra)

    assert carrito.total() == 70.0


def test_total_con_cupon(shopping_cart_ejemplo, productos_ejemplo, coupon_ejemplo):
    camiseta, pantalon, gorra = productos_ejemplo
    cupon10, _, _ = coupon_ejemplo
    carrito = shopping_cart_ejemplo

    carrito.add_product(camiseta)
    carrito.add_product(pantalon)
    carrito.add_product(gorra)
    carrito.apply_coupon(cupon10)

    assert carrito.total() == 63.0  # 70 - 10%


def test_aplicar_segundo_cupon_falla(shopping_cart_ejemplo, coupon_ejemplo):
    cupon10, cupon30, _ = coupon_ejemplo
    carrito = shopping_cart_ejemplo

    carrito.apply_coupon(cupon10)
    with pytest.raises(ValueError, match="Ya hay un cupón aplicado."):
        carrito.apply_coupon(cupon30)


def test_eliminar_producto(shopping_cart_ejemplo, productos_ejemplo):
    camiseta, pantalon, gorra = productos_ejemplo
    carrito = shopping_cart_ejemplo

    carrito.add_product(camiseta)
    carrito.add_product(pantalon)
    carrito.add_product(gorra)
    carrito.remove_product("Pantalón")

    assert carrito.total() == 35.0  # 20 (camiseta) + 15 (gorra)


def test_eliminar_producto_inexistente_lanza_error(shopping_cart_ejemplo):
    carrito = shopping_cart_ejemplo

    with pytest.raises(ValueError, match="Producto no encontrado en el carrito."):
        carrito.remove_product("Calcetines")


def test_clear_carrito(shopping_cart_ejemplo, productos_ejemplo, coupon_ejemplo):
    camiseta, pantalon, _ = productos_ejemplo
    cupon10, _, _ = coupon_ejemplo
    carrito = shopping_cart_ejemplo

    carrito.add_product(camiseta)
    carrito.add_product(pantalon)
    carrito.apply_coupon(cupon10)
    carrito.clear()

    assert carrito.total() == 0.0


def test_total_redondeo_preciso():
    carrito = ShoppingCart()
    producto = Product("Algo Raro", 33.333)
    carrito.add_product(producto)

    assert carrito.total() == 33.33
