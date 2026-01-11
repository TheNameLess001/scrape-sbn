import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import json
import time
import random

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="Glovo JSON Extractor", page_icon="🧬", layout="wide")

st.title("🧬 Extraction Chirurgicale (Via JSON caché)")
st.markdown("""
Au lieu de lire l'écran, ce script cherche la base de données interne (`__NEXT_DATA__`) cachée dans le code source de la page.
**Note :** Si cela échoue sur le Cloud, c'est que Glovo bloque l'adresse IP américaine du serveur. Il faudra lancer ce code sur votre PC.
""")

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # User Agent standard pour passer pour un PC normal
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def extract_json_data(soup):
    # Glovo (et Next.js) stockent tout ici
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    
    if not script_tag:
        return None, "Balise __NEXT_DATA__ introuvable."
    
    try:
        json_content = json.loads(script_tag.string)
        
        # On va chercher récursivement tous les produits dans cet énorme objet JSON
        # Car la structure change souvent (props -> pageProps -> initialStoreState...)
        products = []
        
        # Fonction récursive pour fouiller le JSON
        def search_dict(d):
            if isinstance(d, dict):
                # Si on trouve un objet qui ressemble à un produit (a un nom et un prix)
                if 'name' in d and 'price' in d:
                    try:
                        products.append({
                            'Nom': d.get('name'),
                            'Prix': d.get('price'),
                            'Description': d.get('description', ''),
                            'Catégorie': d.get('categoryName', 'Inconnue') # Parfois disponible
                        })
                    except:
                        pass
                
                # Continuer à fouiller
                for key, value in d.items():
                    search_dict(value)
            
            elif isinstance(d, list):
                for item in d:
                    search_dict(item)

        search_dict(json_content)
        return products, "Succès"
        
    except Exception as e:
        return None, f"Erreur lecture JSON : {e}"

# --- Interface ---
url = st.text_input("URL Glovo Casablanca", placeholder="https://glovoapp.com/...")

if st.button("Extraire les données cachées 🧬"):
    if url:
        status = st.empty()
        status.info("Connexion au site...")
        
        driver = get_driver()
        try:
            driver.get(url)
            time.sleep(5) # On laisse le temps au redirection éventuelle
            
            status.info("Récupération du code source...")
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Vérification du titre pour voir si on a été redirigé
            page_title = driver.title
            st.caption(f"Titre de la page atteinte : {page_title}")
            
            status.info("Recherche des données JSON...")
            data, message = extract_json_data(soup)
            
            if data and len(data) > 0:
                st.success(f"BINGO ! {len(data)} produits extraits depuis le code caché.")
                df = pd.DataFrame(data)
                
                # Nettoyage : Supprimer les doublons exacts
                df = df.drop_duplicates(subset=['Nom'])
                
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Télécharger CSV", csv, "glovo_data.csv", "text/csv")
            else:
                st.error(f"Échec : {message}")
                st.warning("""
                **Diagnostic :** Si le titre est juste "Glovo" et qu'aucune donnée ne sort, c'est que **Glovo bloque l'IP du serveur Streamlit** (Géolocalisation).
                
                👉 **Solution :** Vous devez lancer ce script **sur votre propre ordinateur** (Localhost) et pas sur le Cloud. Sur votre PC, vous avez une IP marocaine, donc Glovo affichera le menu.
                """)
                
        except Exception as e:
            st.error(f"Erreur : {e}")
        finally:
            driver.quit()
