from .carts import Cart


def cart(request):
    """Expose the request's Cart instance to templates.

    The Cart is created once per request and cached on ``request._cart``
    so views and the context processor share the same instance (and the
    same session state) without rebuilding it on every render.
    """
    cached = getattr(request, "_cart", None)
    if cached is None:
        cached = Cart(request)
        request._cart = cached

    cart_instance = cached

    if len(list(cart_instance.cart.keys())) < 1:
        try:
            del cart_instance.session[cart_instance.coupon_id]
            cart_instance.coupon = None
        except KeyError:
            pass

    return {"cart": cart_instance}