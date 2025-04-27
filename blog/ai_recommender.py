import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from blog.models import Product, Recommendation
from django.contrib.auth.models import User

def generate_recommendations():
    # 1. Fetch products
    products = Product.objects.all()

    # 2. Build a dataframe
    data = []
    for p in products:
        data.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'tags': " ".join([tag.name for tag in p.tags.all()]),
        })

    df = pd.DataFrame(data)

    # 3. Combine text fields
    df['combined'] = df['title'] + " " + df['description'] + " " + df['tags']

    # 4. TF-IDF Vectorizer
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined'])

    # 5. Compute similarity
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # 6. For each user (or demo for now)
    users = User.objects.all()
    for user in users:
        # you could later improve it using user's browsing/cart history
        liked_products = Product.objects.all()[:5]  # dummy - recommend based on trending or cart later

        for lp in liked_products:
            idx = df.index[df['id'] == lp.id][0]
            sim_scores = list(enumerate(cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:11]  # top 10 similar

            for i, score in sim_scores:
                rec_product = Product.objects.get(id=int(df.iloc[i]['id']))
                Recommendation.objects.update_or_create(
                    user=user,
                    product=rec_product,
                    defaults={'score': float(score)}
                )
