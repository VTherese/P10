import pandas as pd

class HybridRecommender:
    def __init__(self, clicks_data, articles_metadata, user_data, top_n=5):
        self.clicks_data = clicks_data
        self.articles_metadata = articles_metadata
        self.user_data = user_data
        self.top_n = top_n
        self.top_clicked_articles = self.get_top_clicked_articles()

    def get_top_clicked_articles(self):
        return self.clicks_data['click_article_id'].value_counts().head(self.top_n).index.tolist()

    def get_user_interactions(self, user_id):
        return pd.merge(
            self.clicks_data[self.clicks_data['user_id'] == user_id],
            self.articles_metadata[['article_id', 'id_cluster_embedding', 'article_size']],
            left_on='click_article_id',
            right_on='article_id',
            how='left'
        )

    def get_content_based_recommendations(self, cluster_id, exclude_articles, preferred_size=None):
        candidates = self.articles_metadata[
            (self.articles_metadata['id_cluster_embedding'] == cluster_id) &
            (~self.articles_metadata['article_id'].isin(exclude_articles))
        ]
        if preferred_size:
            filtered_candidates = candidates[candidates['article_size'] == preferred_size]
            if len(filtered_candidates) < self.top_n:
                return pd.concat([filtered_candidates, candidates]).head(self.top_n)['article_id'].tolist()
            return filtered_candidates.head(self.top_n)['article_id'].tolist()
        return candidates.head(self.top_n)['article_id'].tolist()

    def recommend_for_new_user(self):
        return self.top_clicked_articles

    def recommend_for_user(self, user_interactions):
        if len(user_interactions) == 1:
            article_id = user_interactions['click_article_id'].iloc[0]
            if article_id in self.top_clicked_articles:
                return [art for art in self.top_clicked_articles if art != article_id]
            return self.get_content_based_recommendations(
                user_interactions['id_cluster_embedding'].iloc[0],
                exclude_articles=[article_id],
                preferred_size=user_interactions['article_size'].iloc[0]
            )

        cluster_counts = user_interactions['id_cluster_embedding'].value_counts()
        sorted_clusters = cluster_counts.index

        recommendations = []
        for cluster_id in sorted_clusters:
            size_preference = user_interactions[user_interactions['id_cluster_embedding'] == cluster_id]['article_size'].mode()[0]
            recommendations += self.get_content_based_recommendations(
                cluster_id,
                exclude_articles=user_interactions['click_article_id'].tolist(),
                preferred_size=size_preference
            )
            if len(recommendations) >= self.top_n:
                break

        return recommendations[:self.top_n]

    def get_recommendations(self, user_id):
        user_interactions = self.get_user_interactions(user_id)
        if user_interactions.empty:
            return {"recommendations": self.recommend_for_new_user(), "strategy": 1}
        elif len(user_interactions) == 1:
            if user_interactions['click_article_id'].iloc[0] in self.top_clicked_articles:
                return {"recommendations": self.recommend_for_user(user_interactions), "strategy": 2}
            else:
                return {"recommendations": self.recommend_for_user(user_interactions), "strategy": 3}
        else:
            clusters = user_interactions['id_cluster_embedding'].nunique()
            if clusters == 1:
                return {"recommendations": self.recommend_for_user(user_interactions), "strategy": 4}
            else:
                return {"recommendations": self.recommend_for_user(user_interactions), "strategy": 5}

    def add_new_user(self):
        new_user_id = self.user_data['user_id'].max() + 1
        new_user = pd.DataFrame({'user_id': [new_user_id]})
        self.user_data = pd.concat([self.user_data, new_user], ignore_index=True)
        return new_user_id

    def add_new_article(self, words_count, cluster_choice):
        new_article_id = self.articles_metadata['article_id'].max() + 1
        mean_words_count = self.articles_metadata['words_count'].mean()
        std_words_count = self.articles_metadata['words_count'].std()
        small_threshold = mean_words_count - std_words_count
        medium_threshold = mean_words_count + std_words_count

        def categorize_article_size(word_count):
            if word_count <= small_threshold:
                return 'small'
            elif word_count <= medium_threshold:
                return 'medium'
            else:
                return 'long'

        article_size = categorize_article_size(words_count)

        new_article = pd.DataFrame({
            'article_id': [new_article_id],
            'words_count': [words_count],
            'id_cluster_embedding': [cluster_choice],
            'article_size': [article_size]
        })

        self.articles_metadata = pd.concat([self.articles_metadata, new_article], ignore_index=True)
        return new_article_id, article_size
