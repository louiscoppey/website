#!/usr/bin/env python3
"""
Script pour nettoyer le fichier Blog.csv en supprimant les entrées invalides
"""

import csv
import re

def clean_blog_csv(input_file, output_file):
    """Nettoie le fichier CSV en supprimant les entrées invalides"""
    
    valid_articles = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            # Vérifier si l'URL est valide (doit contenir louicop.medium.com et un identifiant d'article)
            url = row['url']
            if (url.startswith('https://louicop.medium.com/') and 
                len(url.split('/')) > 4 and  # Doit avoir un identifiant d'article
                row['date'] != 'Unknown Date'):
                
                valid_articles.append(row)
                print(f"Article conservé : {row['title'][:60]}...")
            else:
                print(f"Article supprimé (URL invalide ou date inconnue) : {row['title'][:60]}...")
    
    # Sauvegarder le fichier nettoyé
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['date', 'title', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(valid_articles)
    
    print(f"\nNettoyage terminé !")
    print(f"Articles conservés : {len(valid_articles)}")
    print(f"Fichier sauvegardé : {output_file}")

if __name__ == "__main__":
    clean_blog_csv("Blog.csv", "Blog_clean.csv")
    
    # Remplacer le fichier original par la version nettoyée
    import os
    os.rename("Blog_clean.csv", "Blog.csv")
    print("Fichier Blog.csv mis à jour avec la version nettoyée")
