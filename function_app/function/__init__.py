import logging
import azure.functions as func
import pandas as pd
from azure.storage.blob import BlobServiceClient
from .hybrid_recommender import HybridRecommender
import json
import os

# Variable globale pour stocker les datasets en mémoire
datasets_loaded = False
clicks_data = None
articles_metadata = None
user_id_data = None

def load_data_from_blob(blob_service_client, container_name, blob_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        download_stream = blob_client.download_blob()
        return pd.read_csv(download_stream)
    except Exception as e:
        logging.error(f"Erreur lors du chargement du blob {blob_name}: {str(e)}")
        return None

def save_data_to_blob(blob_service_client, container_name, blob_name, dataframe):
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        output_stream = dataframe.to_csv(index=False)
        blob_client.upload_blob(output_stream, overwrite=True)
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du blob {blob_name}: {str(e)}")

def main(req: func.HttpRequest) -> func.HttpResponse:
    global datasets_loaded, clicks_data, articles_metadata, user_id_data
    logging.info('Python HTTP trigger function processed a request.')

    # Charger les configurations nécessaires
    connect_str = os.getenv('AzureWebJobsStorage')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    if not datasets_loaded:
        clicks_data = load_data_from_blob(blob_service_client, 'model', 'clicks_data.csv')
        articles_metadata = load_data_from_blob(blob_service_client, 'model', 'articles_metadata.csv')
        user_id_data = load_data_from_blob(blob_service_client, 'model', 'user_id.csv')
        if clicks_data is None or articles_metadata is None or user_id_data is None:
            return func.HttpResponse("Erreur lors du chargement des données, veuillez réessayer plus tard.", status_code=500)
        datasets_loaded = True

    # Initialiser le recommender
    recommender = HybridRecommender(clicks_data, articles_metadata, user_id_data, top_n=5)

    # Gérer les différentes requêtes
    action = req.params.get('action')
    user_id = req.params.get('user_id')
    article_id = req.params.get('article_id')

    # Vérifier si l'action est définie
    if not action:
        return func.HttpResponse("Bonjour ! Bienvenue sur notre application de recommendation de contenu !", status_code=200)

    if action == "load_datasets":
        datasets = {
            "clicks_data": clicks_data.to_dict(),
            "articles_metadata": articles_metadata.to_dict(),
            "user_id_data": user_id_data.to_dict()
        }
        return func.HttpResponse(json.dumps(datasets), mimetype="application/json")

    if action == "recommend":
        if not user_id:
            return func.HttpResponse("Veuillez fournir un ID utilisateur pour continuer.", status_code=400)

        user_id = int(user_id)

        if user_id in clicks_data['user_id'].values or user_id in user_id_data['user_id'].values:
            result = recommender.get_recommendations(user_id)
            return func.HttpResponse(json.dumps(result), mimetype="application/json")
        else:
            return func.HttpResponse(
                f"L'utilisateur avec l'ID {user_id} n'existe pas. Le dernier ID utilisateur enregistré est {user_id_data['user_id'].max()}. "
                "Si vous voulez en ajouter un nouveau, allez dans la section 'Ajouter un utilisateur ou un article'.",
                status_code=404
            )

    elif action == "add_user":
        new_user_id = recommender.add_new_user()
        save_data_to_blob(blob_service_client, 'model', 'user_id.csv', recommender.user_data)
        datasets_loaded = False  # Forcer le rechargement la prochaine fois
        return func.HttpResponse(f"Nouvel utilisateur ajouté avec l'ID : {new_user_id}", status_code=200)

    elif action == "add_article":
        words_count = int(req.params.get('words_count'))
        cluster_choice = int(req.params.get('cluster_choice'))
        new_article_id, article_size = recommender.add_new_article(words_count, cluster_choice)
        save_data_to_blob(blob_service_client, 'model', 'articles_metadata.csv', recommender.articles_metadata)
        datasets_loaded = False  # Forcer le rechargement la prochaine fois
        return func.HttpResponse(f"Nouvel article ajouté avec l'ID : {new_article_id}. Il compte {words_count} mots et appartient au cluster {cluster_choice}.", status_code=200)

    else:
        return func.HttpResponse("Action invalide", status_code=400)
