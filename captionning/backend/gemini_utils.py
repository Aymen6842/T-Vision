import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Setup Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

RULES = """
RÈGLES DE GÉNÉRATION DE LÉGENDES

1. Format
- La sortie doit contenir une seule phrase.
- La phrase doit être rédigée au présent de l’indicatif.
- La longueur maximale est de 50 mots.

2. Contenu autorisé
- Décrire uniquement les éléments directement visibles dans l’image.
- Ne pas formuler d’hypothèses, d’interprétations ou de déductions.
- Éviter toute expression d’incertitude (ex. : probablement, semble, pourrait).

3. Structure obligatoire
- La description doit suivre l’ordre suivant :
  sujet principal → action observable → contexte (lieu, objets visibles).
- Cet ordre ne doit pas être modifié.

4. Action
- Décrire uniquement des actions clairement observables.
- En l’absence d’action évidente, utiliser une description statique
  (ex. : est debout, est assis, se tient immobile).

5. Ton et style
- Employer un ton neutre, factuel et objectif.
- Utiliser un vocabulaire simple et descriptif.
- Éviter les adjectifs subjectifs ou évaluatifs.

6. Restrictions
- Ne pas inclure de descriptions graphiques ou choquantes
  (blessures détaillées, sang, violence explicite).
- Ne pas mentionner d’éléments hors champ ou non visibles.
- Ne pas identifier des personnes, marques ou entités spécifiques.
"""

def rewrite_caption_french_cloud(raw_caption):
    prompt = f"{RULES}\n\nTraduit cette phrase : {raw_caption}"

    # Gemini 2.5 Flash
    response = client.models.generate_content(
        model="gemini-2.5-flash", # Notebook mentioned 2.5-flash but 2.0-flash is current. Notebook had AIza... key.
        contents=prompt
    )

    return response.text.strip()
