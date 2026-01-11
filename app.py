import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Configuration de la page
st.set_page_config(page_title="Mon Super Scraper", page_icon="🕷️")

st.title("🕷️ Web Scraper avec Streamlit")
st.markdown("Entrez une URL pour extraire les données (Titres et Liens).")

# --- Barre latérale pour les options ---
with st.sidebar:
    st.header("Paramètres")
    element_to_scrape = st.selectbox(
        "Quel élément chercher ?",
        ("h1", "h2", "h3", "a", "p")
    )
    user_agent = st.text_input("User Agent (Optionnel)", placeholder="Mozilla/5.0...")

# --- Fonction de scraping ---
def scrape_website(url, tag):
    # En-têtes pour éviter d'être bloqué (anti-bot basique)
    headers = {
        'User-Agent': user_agent if user_agent else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Vérifie si la requête a réussi (Code 200)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        found_elements = soup.find_all(tag)
        
        data = []
        for el in found_elements:
            # On récupère le texte et le lien si c'est une balise <a>
            text = el.get_text(strip=True)
            link = el.get('href') if tag == 'a' else None
            
            if text: # On garde seulement s'il y a du texte
                row = {'Texte': text}
                if link:
                    row['Lien'] = link
                data.append(row)
                
        return pd.DataFrame(data)

    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la connexion au site : {e}")
        return None

# --- Interface Principale ---
url_input = st.text_input("URL du site web", placeholder="https://exemple.com")
scrape_btn = st.button("Lancer le Scraping")

if scrape_btn and url_input:
    with st.spinner('Scraping en cours...'):
        time.sleep(1) # Simulation d'attente
        df = scrape_website(url_input, element_to_scrape)
        
        if df is not None and not df.empty:
            st.success(f"Succès ! {len(df)} éléments trouvés.")
            
            # Affichage des données
            st.dataframe(df, use_container_width=True)
            
            # Bouton de téléchargement CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name='data_scrape.csv',
                mime='text/csv',
            )
        elif df is not None:
            st.warning("Aucune donnée trouvée avec cette balise.")
