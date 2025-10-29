import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import shutil

# Fonctions utilitaires

# Fonction pour récupérer une page et retourner le BeautifulSoup
import time
import random

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
}

def get_soup(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Mise en place d'une pause aléatoire pour ne pas spammer le site car sans ça ça ne marchait pas
            time.sleep(random.uniform(1, 2))
            return BeautifulSoup(response.text, 'html.parser')
        else:
            print(f"Erreur {response.status_code} pour l'URL : {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        return None

# Fonction pour télécharger une image à partir d'une URL
def download_image(img_url, save_path):
    response = requests.get(img_url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
    else:
        print(f"Impossible de télécharger l'image : {img_url}")

# Récupérer toutes les catégories

base_url = "https://books.toscrape.com/"
soup = get_soup(base_url)

categories = {}
for a in soup.select('ul.nav-list ul li a'):
    category_name = a.text.strip()
    category_url = base_url + a['href']
    categories[category_name] = category_url

print("Catégories trouvées :", list(categories.keys()))

# Scraper chaque catégorie
for category_name, category_url in categories.items():
    print(f"\n🔹 Catégorie : {category_name}")
    
    # Création d'un dossier pour les images de cette catégorie
    os.makedirs(f'images/{category_name}', exist_ok=True)
    
    page_url = category_url
    all_books = []
    
    while page_url:
        soup = get_soup(page_url)
        if not soup:
            break
        
        # Parcourir tous les livres sur la page
        books = soup.select('article.product_pod')
        for book in books:
        
            title = book.h3.a['title']
            
            product_url = base_url + 'catalogue/' + book.h3.a['href'].replace('../', '')
            
            price = book.select_one('p.price_color').text.strip()
            
            availability = book.select_one('p.availability').text.strip()
            
            star_rating = book.p['class'][1]
            
            img_url = base_url + book.img['src'].replace('../', '')
            
            product_soup = get_soup(product_url)
            upc = product_soup.select_one('th:contains("UPC") + td').text if product_soup.select_one('th:contains("UPC") + td') else ''
            exact_category = product_soup.select('ul.breadcrumb li a')[-1].text.strip()
            
            import re

            # Nettoyage du titre pour qu'il devienne un nom de fichier valide sur sur windows
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            img_filename = f"images/{category_name}/{safe_title}.jpg"

            img_filename = f"images/{category_name}/{title.replace('/', '-')}.jpg"
            download_image(img_url, img_filename)
            
            all_books.append({
                'Titre': title,
                'Prix': price,
                'Disponibilité': availability,
                'Note': star_rating,
                'URL produit': product_url,
                'URL image': img_url,
                'UPC': upc,
                'Catégorie': exact_category
            })
        
        # Vérifier si y'a une page suivante
        next_btn = soup.select_one('li.next a')
        if next_btn:
            page_url = category_url.replace('index.html', '') + next_btn['href']
        else:
            page_url = None
    
    # Sauvegarder CSV pour la catégorie
    df = pd.DataFrame(all_books)
    df.to_csv(f"{category_name}.csv", index=False)
    print(f" {len(all_books)} livres sauvegardés dans {category_name}.csv")
