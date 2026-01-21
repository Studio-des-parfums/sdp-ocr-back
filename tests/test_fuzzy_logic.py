from app.utils.note_corrector import note_corrector

def test_advanced_corrections():
    # Cas de test spécifiés + cas additionnels
    test_cases = [
        ("Noto Morinc", "Marine", True),
        ("vanile", "Vanille", True),
        ("bois cashmir", "Bois de cachemire", True),
        ("jasmin musque", "Jasmin musqué", True),
        ("santale", "Santal", True),
        ("fleur orenger", "Fleur d'oranger", True),
        ("Inconnu total", None, False), # Doit échouer (si score > 60, c'est un problème de seuil)
        ("Inconnu", None, False),
        ("citron", "Citron doux", True), # Citron doux ou citron amère ?
    ]    
    
    # ... code ...

    print("=== Test Système Avancé de Correction des Notes ===")

    # DEBUG: Voir la normalisation
    # print(f"DEBUG Norm 'Noto Morinc': '{note_corrector.normaliser('Noto Morinc')}'")
    
    all_passed = True

    for input_name, expected_name, should_find in test_cases:
        result = note_corrector.trouver_parfum(input_name, seuil=65) # Augmenter seuil à 65 pour éviter faux positifs 'Cocktail'
        
        found = result["trouve"]
        nom = result["nom"]
        score = result["score"]
        code = result["code"]
        
        status = "✅ PASS"
        
        if should_find:
            if not found:
                 status = "❌ FAIL (Not found)"
                 all_passed = False
            elif nom != expected_name and not (input_name == "citron" and "Citron" in nom):
                status = f"❌ FAIL (Wrong match: {nom})"
                all_passed = False
        else:
            if found:
                status = f"❌ FAIL (Should not find, got {nom})"
                all_passed = False

        print(f"{status} | Input: '{input_name:15}' -> Found: '{nom}' (Code: {code}, Score: {score})")
        if not found and result["meilleure_tentative"]:
             print(f"      -> Meilleure tentative (rejetée): '{result['meilleure_tentative']}'")

    print(f"\nGlobal Result: {'✅ SUCCESS' if all_passed else '❌ FAILURE'}")

    # Test méthode compatibilité
    print("\n--- Test Compatibilité ---")
    legacy_res = note_corrector.correct_note_name("Noto Morinc")
    print(f"Legacy call 'Noto Morinc' -> '{legacy_res}'")

if __name__ == "__main__":
    test_advanced_corrections()
