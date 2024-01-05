from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
import redis
import json
from bson import json_util, ObjectId
import csv
import io

#Connexion à la base de données
app = Flask(__name__) 
app.secret_key = 'tft_c_cool'  
client = MongoClient('mongodb://localhost:27017/')
db = client['gestion_stock']
collection = db['articles']
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

@app.route('/') #Page d'accueil
def index():
    return render_template('index.html')

@app.route('/nouvel_article', methods=['GET', 'POST']) #Page d'ajout d'un nouvel article
def nouvel_article():
    message = None

    if request.method == 'POST':
        designation = request.form['designation']
        prix_unitaire = float(request.form['prix_unitaire'])

        collection.insert_one({'designation': designation, 'prix_unitaire': prix_unitaire}) #Ajout de l'article dans la base de données

        message = 'Ajoute ' + designation + ' ' + str(prix_unitaire) + ' avec succès' #Message de confirmation

    return render_template('nouvel_article.html', message=message)

@app.route('/ajout_de_donnees', methods=['GET', 'POST']) #Page d'ajout de données
def ajout_de_donnees():
    if request.method == 'POST': #Vérification du fichier existant ou le fichier non approprié
        if 'file' not in request.files:
            flash('Aucun fichier n\'a été téléchargé.', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('Aucun fichier sélectionné.', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.txt'): #Vérification du format du fichier
            try:
                text_file = io.TextIOWrapper(file, encoding='utf-8', newline='')
                
                csv_data = csv.reader(text_file, delimiter=';')

                for row in csv_data:
                    designation, prix_unitaire = row
                    prix_unitaire = float(prix_unitaire)

                    collection.insert_one({'designation': designation, 'prix_unitaire': prix_unitaire}) #Ajout de l'article dans la base de données

                flash('Les données ont été ajoutées avec succès.', 'success')
            except Exception as e:
                flash(f"Une erreur s'est produite lors de la lecture du fichier : {str(e)}", 'error')

        else:
            flash('Le fichier doit être au format texte (.txt).', 'error')

    return render_template('ajout_de_donnees.html')

@app.route('/recherche', methods=['GET', 'POST']) #Page de recherche
def recherche():
    if request.method == 'POST':
        terme_recherche = request.form['terme_recherche']
        
        cached_results = redis_client.get(terme_recherche)
        if cached_results:
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


@app.route('/suppression_par_nom', methods=['GET', 'POST']) #Page de suppression par nom
def suppression_par_nom():
    if request.method == 'POST':
        nom_a_supprimer = request.form['nom_a_supprimer']
        article = collection.find_one({'designation': nom_a_supprimer}) #Recherche de l'article dans la base de données
        
        if article:
            collection.delete_one({'designation': nom_a_supprimer}) #Suppression de l'article dans la base de données
            redis_client.flushall()
            message = f"L'article '{nom_a_supprimer}' a été supprimé avec succès."
        else:
            message = f"L'article '{nom_a_supprimer}' n'existe pas."

        return render_template('suppression_par_nom.html', message=message)

    return render_template('suppression_par_nom.html')

    
def object_hook(dct): #Fonction de conversion ObjectId
    for key, value in dct.items():
        if isinstance(value, dict):
            dct[key] = object_hook(value)
        elif key == "_id" and "$oid" in value:
            dct[key] = ObjectId(value["$oid"])
    return dct

if __name__ == '__main__': #Lancement de l'application
    app.run(debug=True)

