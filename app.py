from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from flask import jsonify
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import redis
import json
from bson import json_util
import datetime

app = Flask(__name__)
app.secret_key = 'tft_c_cool'  
client = MongoClient('mongodb://localhost:27017/')
db = client['gestion_stock']
collection = db['articles']
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['gestion_stock']
collection = db['articles']

# Page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Page de saisie d'un nouvel article
@app.route('/nouvel_article', methods=['GET', 'POST'])
def nouvel_article():
    if request.method == 'POST':
        designation = request.form['designation']
        prix_unitaire = float(request.form['prix_unitaire'])

        # Enregistrement dans la base de données
        collection.insert_one({'designation': designation, 'prix_unitaire': prix_unitaire})

        return redirect(url_for('index'))

    return render_template('nouvel_article.html')

# Page de recherche d'articles
@app.route('/recherche', methods=['GET', 'POST'])
def recherche():
    if request.method == 'POST':
        terme_recherche = request.form['terme_recherche']

        # Vérifiez d'abord si les résultats sont en cache dans Redis
        cached_results = redis_client.get(terme_recherche)
        if cached_results:
            # Chargez les résultats depuis Redis et convertissez les ObjectId
            articles = json.loads(cached_results, object_hook=object_hook)
        else:
            # Effectuez la recherche dans la base de données
            articles = collection.find({'designation': {'$regex': terme_recherche, '$options': 'i'}})
            
            # Convertissez les résultats en liste pour l'affichage
            articles = list(articles)

            # Sérialisez les résultats en JSON avec la conversion ObjectId
            redis_client.setex(terme_recherche, 3600, json.dumps(articles, default=json_util.default))

        # Convertissez les résultats en liste pour l'affichage
        articles_list = list(articles)

        return render_template('recherche.html', articles=articles_list, terme_recherche=terme_recherche)

    return render_template('recherche.html')

# Fonction de conversion pour ObjectId
def object_hook(dct):
    for key, value in dct.items():
        if isinstance(value, dict):
            dct[key] = object_hook(value)
        elif key == "$oid":
            return ObjectId(value)
    return dct

if __name__ == '__main__':
    app.run(debug=True)
