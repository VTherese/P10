import streamlit as st
import requests

# URL de base de la fonction Azure
BASE_URL = "https://recommander.azurewebsites.net/api/my_function"

st.set_page_config(page_title="Content Recommendation App", page_icon="🎯", layout="centered")

st.title("🎯 Content Recommendation App")

menu = st.sidebar.selectbox("Choisissez une action", ["🔍 Recommander des articles", "➕ Ajouter des données"])

def handle_api_errors(response):
    if response.status_code == 404:
        st.error("🚨 L'utilisateur n'existe pas, pour ajouter un utilisateur,  allez dans la section 'Ajouter des données'.")
    elif response.status_code == 400:
        st.error("⚠️ Requête invalide. Veuillez vérifier les paramètres.")
    else:
        st.error(f"❌ Erreur lors de la communication avec l'API : {response.status_code}")

def get_strategy_explanation(strategy_number):
    explanations = {
        1: [
            f"<p style='font-size:28px;'>👤 <strong>Utilisateur : {user_id}</strong></p>",
            "<p style='font-size:18px;'>💡 Nouvel utilisateur sans interaction.</p>",
            "<p style='font-size:18px;'>📈 Recommandation des 5 articles les plus cliqués sur la plateforme.</p>",
            "<p style='font-size:18px;'>🎯 Objectif : Recommandations basées sur le contenu populaire (collaborative filtering).</p>"
        ],
        2: [
            f"<p style='font-size:28px;'>👤 <strong>Utilisateur : {user_id}</strong></p>",
            "<p style='font-size:18px;'>💡 Utilisateur avec une seule interaction</p>",
            "<p style='font-size:18px;'>🔥 L'article lu fait partie des top 5 les plus populaires.</p>",
            "<p style='font-size:18px;'>📋 Recommandation d'autres articles les plus populaires, en excluant celui déjà lu.</p>",
            "<p style='font-size:18px;'>🎯 Objectif : Recommandations basées sur le contenu populaire (collaborative filtering).</p>"
        ],
        3: [
            f"<p style='font-size:28px;'>👤 <strong>Utilisateur : {user_id}</strong></p>",
            "<p style='font-size:18px;'>💡 Utilisateur avec une seule interaction</p>",
            "<p style='font-size:18px;'>⚖️ Recommandation d'articles similaires (même cluster), avec une priorité donnée à une taille similaire.</p>",
            "<p style='font-size:18px;'>🎯 Objectif : Recommandations basées sur la proximité de contenu (content-based filtering).</p>"
        ],
        4: [
            f"<p style='font-size:28px;'>👤 <strong>Utilisateur : {user_id}</strong></p>",
            "<p style='font-size:18px;'>💡 Plusieurs interactions dans un même cluster</p>",
            "<p style='font-size:18px;'>🗂️ Recommandation d'articles supplémentaires dans ce cluster, en respectant les préférences de taille observées.</p>",
            "<p style='font-size:18px;'>🎯 Objectif : Recommandations basées sur la proximité de contenu (content-based filtering).</p>"
        ],
        5: [
            f"<p style='font-size:28px;'>👤 <strong>Utilisateur : {user_id}</strong></p>",
            "<p style='font-size:18px;'>💡 Utilisateur avec plusieurs interactions dans différents clusters</p>",
            "<p style='font-size:18px;'>🧮 Priorisation des clusters où l'utilisateur a montré le plus d'engagement (plus de clics).</p>",
            "<p style='font-size:18px;'>🌀 Diversification des recommandations en tenant compte de la taille préférée des articles dans chaque cluster.</p>",
            "<p style='font-size:18px;'>🔄 Limitation à 3 articles par cluster pour garantir une diversité des recommandations.</p>",
            "<p style='font-size:18px;'>🎯 Objectif : Recommandations diversifiées basées sur les préférences spécifiques de l'utilisateur.</p>"
        ],
    }
    return explanations.get(strategy_number, ["<p style='font-size:18px;'>❓ Stratégie inconnue.</p>"])

if "last_user_id" not in st.session_state:
    st.session_state.last_user_id = None

if menu == "🔍 Recommander des articles":
    st.header("🔍 Recommander des articles")
    
    # Barre de sélection d'ID utilisateur sur toute la page
    user_id = st.number_input("Entrez l'ID utilisateur :", min_value=0, step=1, label_visibility="visible")
    
    if st.button("Recherche de recommandations"):
        if user_id is not None:
            st.session_state.last_user_id = user_id  # Enregistrer l'ID utilisateur dans l'état
            response = requests.get(f"{BASE_URL}?user_id={user_id}&action=recommend")
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", [])
                strategy = data.get("strategy", None)

                if recommendations:
                    col1, col2 = st.columns([1, 2])  # Disposition en deux colonnes pour afficher côte à côte

                    with col1:
                        st.subheader("📑 Articles recommandés")
                        for rec in recommendations:
                            st.button(f"📄 Article ID: {rec}", key=f"rec_{rec}")

                    with col2:
                        if strategy:
                            strategy_title = get_strategy_explanation(strategy)[0]
                            for line in get_strategy_explanation(strategy)[0:]:
                                st.markdown(line, unsafe_allow_html=True)  # Explications détaillées

                else:
                    st.write("Aucune recommandation disponible.")
            else:
                handle_api_errors(response)
        else:
            st.error("Veuillez entrer un ID utilisateur valide.")

    # Restaurer l'ID utilisateur si nécessaire
    if st.session_state.last_user_id:
        user_id = st.session_state.last_user_id

elif menu == "➕ Ajouter des données":
    st.header("➕ Ajouter des données")
    choix = st.selectbox("Choisissez une action", ["👤 Ajouter un utilisateur", "📝 Ajouter un article"])

    if choix == "👤 Ajouter un utilisateur":
        if st.button("Ajouter un nouvel utilisateur ➕"):
            with st.spinner("Ajout de l'utilisateur..."):
                response = requests.get(f"{BASE_URL}?action=add_user")
            if response.status_code == 200:
                st.success(response.text)
            else:
                handle_api_errors(response)

    elif choix == "📝 Ajouter un article":
        word_count = st.number_input("Entrez le nombre de mots :", min_value=1, step=1, label_visibility="visible")
        cluster_id = st.number_input("Entrez l'ID du cluster :", min_value=1, step=1, label_visibility="visible")
        if st.button("Ajouter un nouvel article ➕"):
            with st.spinner("Ajout de l'article..."):
                response = requests.get(f"{BASE_URL}?action=add_article&words_count={word_count}&cluster_choice={cluster_id}")
            if response.status_code == 200:
                st.success(response.text)
            else:
                handle_api_errors(response)
