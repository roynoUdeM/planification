import os
from google import genai

# Initialisation du client 
# Assurez-vous que la variable d'environnement GEMINI_API_KEY est définie
client = genai.Client()
MODEL_ID = 'gemini-3.6-flash' # Utilisation de flash pour la rapidité

# --- Base de Connaissances Simulée (RAG) ---
# Dans un système réel, cela serait stocké dans une base vectorielle comme ChromaDB ou FAISS.
DOCUMENTS = [
    "Google AI Studio permet aux développeurs de prototyper rapidement avec l'API Gemini.",
    "L'architecture multi-agent sépare les responsabilités entre plusieurs modèles spécialisés.",
    "Le RAG (Retrieval-Augmented Generation) améliore les réponses en injectant des informations issues d'une base de données externe.",
    "L'agent orchestrateur est le seul point de contact avec l'utilisateur final. Il dissimule la complexité sous-jacente.",
    "Un agent RAG utilise généralement des embeddings pour trouver les documents les plus sémantiquement proches de la requête."
]

def agent_1_analyste(requete_utilisateur: str) -> str:
    """Agent 1 : Analyse la requête et extrait les mots-clés pour la recherche."""
    prompt = f"""Tu es un analyste de requêtes (Agent 1).
Ta tâche est d'analyser la question de l'utilisateur et de générer une requête de recherche optimisée sous forme de mots-clés pour interroger une base de données.
Ne renvoie QUE les mots clés, sans ponctuation supplémentaire.

Question de l'utilisateur : {requete_utilisateur}"""
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
    )
    return response.text.strip()

def agent_2_rag_chercheur(mots_cles: str) -> str:
    """Agent 2 : Simule un RAG, cherche dans la base et extrait le contexte."""
    # Simulation d'une recherche vectorielle : recherche par mots-clés simples pour le PoC
    mots_cles_liste = mots_cles.lower().split()
    documents_pertinents = []
    
    for doc in DOCUMENTS:
        if any(mot in doc.lower() for mot in mots_cles_liste if len(mot) > 3):
            documents_pertinents.append(doc)
            
    if not documents_pertinents:
        # Fallback si aucun mot clé ne matche, on prend les 2 premiers documents
        documents_pertinents = DOCUMENTS[:2] 
        
    contexte_extrait = "\n- ".join(documents_pertinents)
    return contexte_extrait

def agent_3_synthetiseur(requete_utilisateur: str, contexte: str) -> str:
    """Agent 3 : Rédige la réponse finale en utilisant le contexte."""
    prompt = f"""Tu es un rédacteur expert (Agent 3).
Ta tâche est de répondre à la question de l'utilisateur EN TE BASANT UNIQUEMENT sur le contexte fourni.
Structure bien ta réponse. Si le contexte ne contient pas l'information, dis que tu ne sais pas.

Contexte fourni par la recherche RAG :
- {contexte}

Question de l'utilisateur : {requete_utilisateur}"""
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
    )
    return response.text

def agent_orchestrateur(requete_utilisateur: str) -> str:
    """Orchestrateur : Gère la séquence complète de manière transparente pour l'utilisateur."""
    print(f"\n[Orchestrateur] Réception de la requête : '{requete_utilisateur}'")
    
    # 1. Appel de l'Agent 1
    mots_cles = agent_1_analyste(requete_utilisateur)
    print(f"[Orchestrateur] Appel à l'Agent 1... Mots-clés extraits : '{mots_cles}'")
    
    # 2. Appel de l'Agent 2
    contexte = agent_2_rag_chercheur(mots_cles)
    print(f"[Orchestrateur] Appel à l'Agent 2... Contexte RAG récupéré.")
    
    # 3. Appel de l'Agent 3
    reponse_finale = agent_3_synthetiseur(requete_utilisateur, contexte)
    print(f"[Orchestrateur] Appel à l'Agent 3... Réponse finale générée.")
    
    return reponse_finale

if __name__ == "__main__":
    print("=== Démarrage du Système Multi-Agent avec RAG ===")
    print("Assurez-vous que la variable d'environnement GEMINI_API_KEY est configurée.\n")
    
    while True:
        try:
            user_input = input("Vous (Utilisateur) : ")
            if user_input.lower() in ['quitter', 'exit', 'q']:
                print("Fermeture du système.")
                break
                
            # L'utilisateur ne parle qu'à l'orchestrateur
            reponse = agent_orchestrateur(user_input)
            
            print(f"\n[Orchestrateur] Réponse finale pour l'utilisateur :\n{reponse}\n")
            print("-" * 50)
            
        except Exception as e:
            print(f"\nErreur lors de l'exécution : {e}")
