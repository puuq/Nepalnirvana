from django import template
from ..models import Product
from django.db.models import Count, Sum, Q
from ..models import Product, OrderItem, Order

register = template.Library()

@register.inclusion_tag('blog/top_products.html')
def show_top_products(count=4):
    top_products = Product.objects.filter().order_by('-ratings__average')[:4]
    return {"similar_products": top_products}



@register.inclusion_tag('blog/most_viewed_products.html')
def show_most_viewed_products(count=4):
    most_viewed_products = Product.objects.filter().order_by('-hits')[:4]
    return {"similar_products": most_viewed_products}


@register.simple_tag
def define(val=None):
  return val

@register.simple_tag
def show_top_picks(count=4):
    products = Product.objects.filter(status='published')\
        .annotate(
            total_views=Count('hits', distinct=True),
            total_in_carts=Count('orderitem', distinct=True),
            total_bought=Count('orderitem', filter=Q(orderitem__order__coplete=True), distinct=True)
        )

    for product in products:
        product.popularity_score = product.total_views + (2 * product.total_in_carts) + (3 * product.total_bought)

    products = sorted(products, key=lambda p: p.popularity_score, reverse=True)

    return products[:count]

@register.simple_tag(takes_context=True)
def show_picks_for_you(context, count=4):
    request = context['request']
    if not request.user.is_authenticated:
        return Product.objects.none()

    customer = request.user.customer

    past_orders = Order.objects.filter(customer=customer, coplete=True)
    order_items = OrderItem.objects.filter(order__in=past_orders)
    viewed_products = Product.objects.filter(hits__in=[customer.ip_address])

    related_tags = []
    for item in order_items:
        related_tags += list(item.product.tags.all())
    for product in viewed_products:
        related_tags += list(product.tags.all())

    if related_tags:
        related_tag_ids = list(set(tag.id for tag in related_tags))
        recommended_products = Product.objects.filter(tags__in=related_tag_ids, status='published').distinct()
        return recommended_products[:count]
    else:
        return Product.objects.filter(status='published')[:count]