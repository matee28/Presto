# https://huggingface.co/sentence-transformers
# https://www.sbert.net/

from sentence_transformers import SentenceTransformer, util
import torch

class FoodRecommend:

    def __debug_print(self, message):
        if self.debug:
            print("[" + self.__class__.__name__ + "] " + message)

    def __init__(self, debug=False):
        self.debug = debug
        self.__debug_print("Načítání modelu...")
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2") 

    def recommend(self, history_list: list[str], menu_list: list[str]):

        history_embeddings = self.model.encode(history_list, convert_to_tensor=True)
        menu_embeddings = self.model.encode(menu_list, convert_to_tensor=True)
        
        best_dish = None
        max_score = -1

        cosine_scores = util.cos_sim(menu_embeddings, history_embeddings)

        for i, dish in enumerate(menu_list):
            total_similarity_score = torch.sum(cosine_scores[i]).item()
            
            avg_score = total_similarity_score / len(history_list)

            self.__debug_print(f"Jídlo: '{dish}'; shoda: {int(avg_score * 100)} %")

            if total_similarity_score > max_score:
                max_score = total_similarity_score
                best_dish = dish

        return best_dish