from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from flask import jsonify

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
        # Obtenez le terme de recherche à partir du formulaire
        terme_recherche = request.form['terme_recherche']

        # Effectuez la recherche dans la base de données
        articles = collection.find({'designation': {'$regex': terme_recherche, '$options': 'i'}})
        
        # Convertissez les résultats en liste pour l'affichage
        articles_list = list(articles)

        return render_template('recherche.html', articles=articles_list, terme_recherche=terme_recherche)

    return render_template('recherche.html')

if __name__ == '__main__':
    app.run(debug=True)
