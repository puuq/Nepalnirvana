from django.utils import timezone

from django.contrib import messages

from django.db.models import Count

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
import json

from django.urls import reverse_lazy

from .models import *
from .models import Delivery
from .models import Product

from .forms import CreateUserForm, AccountForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.generic import FormView
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth import logout

from django.db.models import Q


import random

from taggit.models import Tag

from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse



def homePage(request, tag_slug=None):
    products = Product.objects.filter(status='published')
    tag =None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = Product.objects.filter(tags__in=[tag])

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)

        order, created = Order.objects.get_or_create(customer=customer, coplete=False)
        order_items_count = order.get_total_products

    else:
        order_items_count = 0


    # Paginate Site With 6 Items Per A Page
    paginator = Paginator(products, 8)
    page = request.GET.get('page')

    # Post Of Certain Page
    try:
        products = paginator.page(page)

    # If Page Not Integer
    except PageNotAnInteger:
        products = paginator.page(1)

    # If Page NOt Exists
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'page': page,
        'order_items_count':  order_items_count,
    }
    return render(request, 'blog/partials/content.html', context)


from django.shortcuts import render, get_object_or_404
from .models import Product

def product_detail(request, pk, slug):
    product = get_object_or_404(Product, id=pk, slug=slug, status='published')

    order_items_count = 0
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, coplete=False)
        order_items_count = order.get_total_products

    # Get similar products based on tags
    product_tags = product.tags.values_list('id', flat=True)

    similar_products = Product.objects.filter(tags__in=product_tags, status='published').exclude(id=product.id)
    similar_products = similar_products.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    # Fallback if no similar products found
    if not similar_products.exists():
        similar_products = Product.objects.filter(status='published').exclude(id=product.id).order_by('-publish')[:4]

    context = {
        'product': product,
        'similar_products': similar_products,
        'order_items_count': order_items_count,
    }
    return render(request, 'blog/partials/product_detail.html', context)





from django.utils import timezone  # Make sure this is at the top


def cart(request):
    if not request.user.is_authenticated:
        return redirect('blog:login')

    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, coplete=False)
    items = OrderItem.objects.filter(order=order)
    delivery = Delivery.objects.filter(active=True)  # Ensure there are active delivery options

    if request.method == "POST":
        code = request.POST.get('code')
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                valid_from__lte=now,
                valid_to__gte=now,
                active=True
            )
            order.coupons = coupon
            order.save()
            messages.success(request, f"Discount: -${coupon.discount}")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon code.")

    context = {
        'items': items,
        'order': order,
        'order_items_count': order.get_total_products,  # Access as attribute
        'delivery': delivery,  # Ensure active deliveries are passed
    }

    return render(request, 'blog/partials/cart.html', context)


def products_view(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 6)  # 6 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/partials/content.html', {
        'products': page_obj  # <--- this part is crucial
    })

def about_view(request):
    return render(request, 'blog/partials/about.html')


def checkout(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, coplete=False)
        items = OrderItem.objects.filter(order=order)
        if not (customer.first_name and customer.last_name and customer.address and customer.email and customer.phone):
            messages.error(request, 'complete your personal information')
            return redirect('blog:cart')
    else:
        items = []
        order = {
            'get_total_price': 0,
            'get_total_products': 0,
        }
        return redirect('blog:login')
    order_items_count = order.get_total_products
    context = {
        'items': items,
        'order': order,
        'order_items_count': order_items_count,
        'customer': customer,
    }
    return render(request, 'blog/partials/checkout.html', context)



def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=request.user.customer, coplete=False)
    orderItem, created = OrderItem.objects.get_or_create(product=product, order=order)


    if action == "add":
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == "remove":
        orderItem.quantity = (orderItem.quantity - 1)
    elif action == "delete":
        orderItem.delete()

    orderItem.save()
    if action == "delete":
        orderItem.delete()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('update item', safe=False)


class registerPage(FormView):
    template_name = 'blog/account/register.html'
    form_class = CreateUserForm
    success_url = reverse_lazy('blog:login')

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('blog:home')
        return super().get(*args, **kwargs)


    def form_valid(self, form):
        user = form.save()
        email = form.cleaned_data['email']
        customer = Customer.objects.create(user=user, email=email)
        return super().form_valid(form)


class loginPage(LoginView):
    template_name = 'blog/account/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('blog:home')

    def form_invalid(self, form):
        messages.error(self.request, 'Username or password is Incorrect')
        return super().form_invalid(self)


@login_required
def logoutPage(request):
    logout(request)
    return redirect('blog:login')


@login_required
def accountPage(request):
    customer = request.user.customer
    order_history = Order.objects.filter(customer=customer, coplete=True)
    if request.method == "POST":
        accForm = AccountForm(data=request.POST)
        if accForm.is_valid():
            accForm = AccountForm(data=request.POST)
            if accForm.is_valid():
                cd = accForm.cleaned_data
                customer.first_name = cd['first_name']
                customer.last_name = cd['last_name']
                customer.email = cd['email']
                customer.phone = cd['phone']
                customer.address = cd['address']
                image = request.FILES.get('image')
                if image:
                    customer.image = image
                customer.save()
                return redirect('blog:account')
    else:
        accForm = AccountForm()
    context = {
        'customer': customer,
        'accForm': accForm,
        'order_history': order_history,
    }
    return render(request, 'blog/account/account.html', context)


def post_search(request):
    if 'query' in request.GET:
        query = request.GET.get('query')
        all_products = Product.objects.filter(status='published')

        documents = []
        for product in all_products:
            text = f"{product.title} {product.description}"
            documents.append(text)

        documents.append(query)

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        similarity_matrix = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
        similarities = similarity_matrix.flatten()

        matched_products = []

        for idx, score in enumerate(similarities):
            if score > 0.1:
                matched_products.append(all_products[int(idx)])
            else:
                # NEW: fuzzy matching if TF-IDF is low
                fuzzy_ratio = fuzz.partial_ratio(query.lower(), documents[idx].lower())
                if fuzzy_ratio > 70:  # Adjust threshold if needed
                    matched_products.append(all_products[int(idx)])

    else:
        matched_products = []

    context = {
        'products': matched_products,
    }
    return render(request, 'blog/partials/content.html', context)


@login_required
@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        data = json.loads(request.body)
        order_id = data.get('order_id')
        address = data.get('address')
        city = data.get('city')

        from .models import Order, ShippingAddress

        try:
            order = Order.objects.get(id=order_id, coplete=False)
            order.coplete = True
            order.transaction_id = f"demo_txn_{order_id}"  # Just create a fake transaction ID
            order.save()

            customer = order.customer

            # Save Shipping Address
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=address,
                city=city
            )

            return JsonResponse({"status": "success"})
        
        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "reason": "Order not found"})

    return JsonResponse({"status": "failed", "reason": "Invalid request"})

def top_products_view(request):
    return render(request, 'blog/top_products.html')

@login_required
def most_viewed_products_view(request):
    return render(request, 'blog/most_viewed_products.html')