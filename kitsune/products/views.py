import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from product_details import product_details

from kitsune.products.models import Product, Topic
from kitsune.wiki.decorators import check_simple_wiki_locale
from kitsune.wiki.facets import topics_for, documents_for
from kitsune.wiki.utils import get_featured_articles


@check_simple_wiki_locale
def product_list(request):
    """The product picker page."""
    template = "products/products.html"
    products = Product.objects.filter(visible=True)
    return render(request, template, {"products": products})


@check_simple_wiki_locale
def product_landing(request, slug):
    """The product landing page."""
    product = get_object_or_404(Product, slug=slug)
    user = request.user
    template = "products/product.html"

    if request.is_ajax():
        # Return a list of topics/subtopics for the product
        topic_list = list()
        for t in Topic.objects.filter(product=product, visible=True):
            topic_list.append({"id": t.id, "title": t.title})
        return HttpResponse(
            json.dumps({"topics": topic_list}), content_type="application/json"
        )

    if slug == "firefox":
        latest_version = product_details.firefox_versions["LATEST_FIREFOX_VERSION"]
    else:
        versions = product.versions.filter(default=True)
        if versions:
            latest_version = versions[0].min_version
        else:
            latest_version = 0

    return render(
        request,
        template,
        {
            "product": product,
            "products": Product.objects.filter(visible=True),
            "topics": topics_for(product=product, parent=None),
            "search_params": {"product": slug},
            "latest_version": latest_version,
            "subscribed_products_ids": (
                user.profile.products.all().values_list("id", flat=True)
                if user.is_authenticated()
                else []
            ),
            "featured": get_featured_articles(product),
        },
    )


@check_simple_wiki_locale
def document_listing(request, product_slug, topic_slug, subtopic_slug=None):
    """The document listing page for a product + topic."""
    product = get_object_or_404(Product, slug=product_slug)
    topic = get_object_or_404(
        Topic, slug=topic_slug, product=product, parent__isnull=True
    )
    template = "products/documents.html"

    doc_kw = {"locale": request.LANGUAGE_CODE, "products": [product]}

    if subtopic_slug is not None:
        subtopic = get_object_or_404(
            Topic, slug=subtopic_slug, product=product, parent=topic
        )
        doc_kw["topics"] = [subtopic]
    else:
        subtopic = None
        doc_kw["topics"] = [topic]

    documents, fallback_documents = documents_for(**doc_kw)

    return render(
        request,
        template,
        {
            "product": product,
            "topic": topic,
            "subtopic": subtopic,
            "topics": topics_for(product=product, parent=None),
            "subtopics": topics_for(product=product, parent=topic),
            "documents": documents,
            "fallback_documents": fallback_documents,
            "search_params": {"product": product_slug},
        },
    )
