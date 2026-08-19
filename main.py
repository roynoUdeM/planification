import streamlit as st
from google import genai
from google.genai import types
import os

# Configuration de la page
st.set_page_config(page_title="Système de Planification", page_icon="📝", layout="wide")
st.title("📝 Système Intelligent de Planification (Univers Social)")

# Détection sécurisée de la clé API (Environnement ou Secrets Streamlit Cloud)
default_key = os.environ.get("GEMINI_API_KEY", "")
try:
    if "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# --- Barre latérale ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API Google AI Studio", type="password", value=default_key)
    
    st.header("📋 Progression de l'orchestration")
    st.info("L'Agent 2 (Interrogateur) va collecter vos besoins. Ensuite, l'Agent 3 (Architecte) utilisera le RAG (documents du PFEQ) pour générer votre planification.")
    
    # State reset
    if st.button("Recommencer à zéro"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not api_key:
    st.warning("Veuillez entrer une clé API valide.")
    st.stop()

# Initialisation du client de façon persistante pour éviter la fermeture de connexion
@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)
# Utiliser un vrai modèle existant sur l'API publique Google pour le Cloud
MODEL_ID = 'gemini-2.5-pro' if os.environ.get("USE_PRO") else 'gemini-1.5-flash'

# Chargement des fichiers de façon robuste (pour Streamlit Cloud)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def load_file(filename):
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

prompt_agent2 = load_file("prompt_agent2.txt")
prompt_agent3 = load_file("prompt_agent3.txt")
knowledge_base = load_file("knowledge_base.txt")

# --- Initialisation de l'état de l'application ---
if "state" not in st.session_state:
    st.session_state.state = "INTERVIEW"
    st.session_state.messages = []
    
    # Initialisation du Chat avec l'Agent 2
    st.session_state.chat = client.chats.create(
        model='gemini-2.5-flash', # Mise à jour vers le dernier modèle standard
        config=types.GenerateContentConfig(
            system_instruction=prompt_agent2,
            temperature=0.3
        )
    )
    # Lancement de la première question avec capture d'erreur
    try:
        response = st.session_state.chat.send_message("Bonjour, je suis un nouvel enseignant. Je veux de l'aide pour ma planification.")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erreur de l'API Google : {str(e)}")
        st.stop()

# --- Affichage du Chat ---
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.chat_message("assistant", avatar="🤖").markdown(message["content"], unsafe_allow_html=True)
    else:
        st.chat_message("user", avatar="👤").markdown(message["content"], unsafe_allow_html=True)

# --- Logique selon l'État ---
if st.session_state.state == "INTERVIEW":
    if prompt := st.chat_input("Répondez à l'Agent Interrogateur..."):
        st.chat_message("user", avatar="👤").markdown(prompt, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("L'Interrogateur réfléchit..."):
                response = st.session_state.chat.send_message(prompt)
                
                # Détection de la balise de fin
                if "[PROFIL_COMPLÉTÉ]" in response.text:
                    # Extraction du profil (on retire la balise)
                    profil = response.text.replace("[PROFIL_COMPLÉTÉ]", "").strip()
                    st.markdown(profil, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": profil})
                    st.session_state.profile_text = profil
                    
                    st.success("Profil complété ! L'Agent 3 (Architecte) prend le relais...")
                    st.session_state.state = "GENERATING_PLAN"
                    st.rerun()
                else:
                    st.markdown(response.text, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})

elif st.session_state.state == "GENERATING_PLAN":
    with st.chat_message("assistant", avatar="🏗️"):
        st.info("L'Agent 3 (Architecte Curriculaire) analyse les documents du PFEQ et votre profil pour concevoir la planification...")
        
        # Construction du prompt pour l'Agent 3
        prompt_final = f"""
Voici le profil de l'enseignant récolté par l'Agent 2 :
{st.session_state.profile_text}

Voici la base de connaissances officielle (RAG - PFEQ Monde contemporain) :
{knowledge_base}

Génère la macro-planification annuelle en respectant strictement tes contraintes et le format exigé.
"""
        with st.spinner("Génération du tableau de planification (cela peut prendre quelques secondes)..."):
            try:
                response_plan = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_final,
                    config=types.GenerateContentConfig(
                        system_instruction=prompt_agent3,
                        temperature=0.2
                    )
                )
                st.markdown(response_plan.text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_plan.text})
                
                st.session_state.state = "DONE"
            except Exception as e:
                st.error(f"Erreur de l'API Google lors de la génération : {str(e)}")

elif st.session_state.state == "DONE":
    st.success("Planification terminée ! Vous pouvez recommencer à l'aide du bouton dans la barre latérale.")
