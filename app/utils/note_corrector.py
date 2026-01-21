import unicodedata
import re
from typing import Optional, Dict, List, Any, Tuple
from rapidfuzz import process, fuzz

class NoteCorrector:
    """
    Système de reconnaissance de parfums avec Fuzzy Matching avancé.
    Gère les catégories (Tête, Cœur, Fond) et les codes associés.
    """

    # Données source structurées
    DATA = {
        "T": {
            "T001": "Bambou", "T002": "Bergamote", "T003": "Bergamote verte", "T004": "Cardamome ginger", 
            "T005": "Citron amère", "T006": "Citron doux", "T008": "Fleur d'oranger", "T009": "Florale fraîche",
            "T010": "Freesia", "T011": "Fruit de cassis", "T012": "Géranium sauvage", "T013": "Gingembre",
            "T014": "Grenadier", "T015": "Lavande sauvage", "T016": "Lotus", "T018": "Mandarine portofino",
            "T019": "Note verte", "T020": "Oeillet fleuri", "T021": "Orange", "T022": "Orange amère",
            "T023": "Ozone", "T024": "Pamplemousse", "T025": "Poivre sichuan", "T026": "Pomme",
            "T027": "Rose de mai", "T028": "Spice bang", "T029": "Thé vert"
        },
        "C": {
            "C001": "Cocktail", "C002": "Concombre", "C003": "Figue", "C004": "Fleur de jacinthe",
            "C005": "Fleur de pêche", "C006": "Fleur de tiaré", "C008": "Geranium", "C009": "Glycine",
            "C010": "Hedione", "C011": "Jasmin musqué", "C012": "Jasmin oriental", "C013": "Jonquille",
            "C014": "Lylibell", "C015": "Mangue", "C016": "Marine", "C018": "Muguet musqué",
            "C019": "Mure", "C020": "Note cannelle", "C021": "Note safran", "C023": "Oeillet cuir",
            "C024": "Oeillet fruité", "C025": "Pivoine", "C026": "Rhubarbe", "C028": "Romarin",
            "C029": "Rose d'orient", "C030": "Rose fruitée cerise", "C031": "Tabac blond", "C032": "Tabac gris",
            "C033": "Tilleul", "C034": "Violette", "C035": "Ylang coton"
        },
        "F": {
            "F001": "Accord musc", "F002": "Amande", "F003": "Ambre", "F004": "Ambre oriental",
            "F005": "Ambre vert", "F006": "Ambreine", "F008": "Bois ambré", "F009": "Bois booster",
            "F010": "Bois de cachemire", "F011": "Bois épicé", "F012": "Boisé ambre", "F013": "Boisé cèdre",
            "F014": "Bouquet fleuri", "F015": "Cèdre", "F016": "Chocolat au lait", "F018": "Coco des îles",
            "F019": "Cuir", "F020": "Fève tonka", "F021": "Fleur de jasmin", "F022": "Frangipane",
            "F023": "Iris", "F024": "Lilas", "F025": "Mousse", "F026": "Musc blanc", "F028": "Musc floral",
            "F029": "Myrrhe encens", "F030": "Note praline", "F031": "Opoponax", "F032": "Oud d'or",
            "F033": "Patchouli", "F034": "Poudre d'iris", "F035": "Santal", "F036": "Santal d'Inde",
            "F038": "Santal d'orient", "F039": "Santal exotique", "F040": "Santaline", "F041": "Tonka",
            "F042": "Tubereuse", "F043": "Vanille", "F044": "Vetiver", "F045": "Virginia"
        }
    }

    def __init__(self):
        self.all_perfumes = []
        self.name_to_info = {}

        for cat, items in self.DATA.items():
            for code, name in items.items():
                self.all_perfumes.append(name)
                self.name_to_info[name] = {"code": code, "categorie": cat}

    @staticmethod
    def normaliser(texte: str) -> str:
        """
        Normalise un texte pour améliorer le matching
        - Convertir en minuscules
        - Retirer les accents (é → e, à → a, etc.)
        - Garder les espaces et lettres uniquement
        """
        if not texte:
            return ""
        
        texte = texte.lower()
        texte = unicodedata.normalize('NFKD', texte).encode('ASCII', 'ignore').decode('utf-8')
        
        # Corrections spécifiques OCR
        texte = texte.replace("noto", "note")
        texte = re.sub(r'^notes?\s+', '', texte)
        
        return texte.strip()

    def trouver_parfum(self, mot_saisi: str, seuil: int = 60, categorie: Optional[str] = None) -> Dict[str, Any]:
        """
        Trouve le parfum le plus proche d'un mot saisi.
        
        Args:
            mot_saisi: le texte entré par l'utilisateur
            seuil: score minimum (0-100)
            categorie: 'T', 'C', ou 'F' pour restreindre la recherche (optionnel)
            
        Returns:
            Dict avec les détails de la correspondance
        """
        if not mot_saisi:
            return {
                "trouve": False,
                "nom": None,
                "code": None,
                "categorie": None,
                "score": 0,
                "entree": mot_saisi,
                "meilleure_tentative": None
            }

        # Choix de la liste de recherche
        if categorie and categorie in self.DATA:
            candidats = list(self.DATA[categorie].values())
        else:
            candidats = self.all_perfumes

        mot_normalise = self.normaliser(mot_saisi)

        result = process.extractOne(
            mot_normalise,
            candidats,
            scorer=fuzz.WRatio,
            processor=self.normaliser
        )

        if result:
            nom_trouve, score, _ = result
            
            if score >= seuil:
                info = self.name_to_info.get(nom_trouve, {})
                return {
                    "trouve": True,
                    "nom": nom_trouve,
                    "code": info.get("code"),
                    "categorie": info.get("categorie"),
                    "score": round(score, 2),
                    "entree": mot_saisi
                }
            else:
                 return {
                    "trouve": False,
                    "nom": None,
                    "code": None,
                    "categorie": None,
                    "score": round(score, 2),
                    "entree": mot_saisi,
                    "meilleure_tentative": nom_trouve
                }
        
        return {
            "trouve": False,
            "nom": None,
            "code": None,
            "categorie": None,
            "score": 0,
            "entree": mot_saisi,
            "meilleure_tentative": None
        }

    # Helper pour compatibilité avec le code existant si besoin
    def correct_note_name(self, raw_name: str, threshold: float = 60.0) -> str:
        """
        Wrapper pour compatibilité avec l'existant.
        Retourne uniquement le nom ou 'A définir'.
        """
        result = self.trouver_parfum(raw_name, seuil=int(threshold))
        if result["trouve"]:
            return result["nom"]
        return "A définir"

note_corrector = NoteCorrector()
