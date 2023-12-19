from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from flask import jsonify
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import redis
import json
from bson import json_util
from bson import ObjectId
import datetime

app = Flask(__name__)
app.secret_key = 'tft_c_cool'  
client = MongoClient('mongodb://localhost:27017/')
db = client['gestion_stock']
collection = db['articles']
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nouvel_article', methods=['GET', 'POST'])
def nouvel_article():
    if request.method == 'POST':
        designation = request.form['designation']
        prix_unitaire = float(request.form['prix_unitaire'])

        collection.insert_one({'designation': designation, 'prix_unitaire': prix_unitaire})

        return redirect(url_for('index'))

    return render_template('nouvel_article.html')

@app.route('/recherche', methods=['GET', 'POST'])
def recherche():
    if request.method == 'POST':
        terme_recherche = request.form['terme_recherche']
        
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

# Nouvelle route pour la suppression par nom
@app.route('/suppression_par_nom', methods=['GET', 'POST'])
def suppression_par_nom():
    if request.method == 'POST':
        nom_a_supprimer = request.form['nom_a_supprimer']
        
        # Vérifiez si l'article avec le nom spécifié existe dans la base de données
        article = collection.find_one({'designation': nom_a_supprimer})
        
        if article:
            # Si l'article existe, supprimez-le de la base de données
            collection.delete_one({'designation': nom_a_supprimer})
            redis_client.flushall()
            message = f"L'article '{nom_a_supprimer}' a été supprimé avec succès."
        else:
            # Si l'article n'existe pas, affichez un message approprié
            message = f"L'article '{nom_a_supprimer}' n'existe pas."

        return render_template('suppression_par_nom.html', message=message)

    return render_template('suppression_par_nom.html')

    
# Fonction de conversion pour ObjectId
def object_hook(dct):
    for key, value in dct.items():
        if isinstance(value, dict):
            dct[key] = object_hook(value)
        elif key == "_id" and "$oid" in value:
            dct[key] = ObjectId(value["$oid"])
    return dct

if __name__ == '__main__':
    app.run(debug=True)

