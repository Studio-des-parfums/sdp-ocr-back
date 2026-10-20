"""
Tests pour la correction automatique des domaines email

Ce script teste la fonctionnalité de correction automatique des fautes
dans les domaines email (ex: gmil.com → gmail.com)
"""

from app.services.email.email_domain_corrector import email_domain_corrector


def test_gmail_corrections():
    """Test des corrections Gmail"""
    print("\n📧 Tests Gmail:")
    print("-" * 50)

    test_cases = [
        ("user@gmil.com", "user@gmail.com"),
        ("user@gmai.com", "user@gmail.com"),
        ("user@gwol.com", "user@aol.com"),  # Note: gwol plus proche de aol
        ("user@gmial.com", "user@gmail.com"),
        ("user@gmaill.com", "user@gmail.com"),
        ("user@gmail.com", "user@gmail.com"),  # Déjà correct
    ]

    for original, expected in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(original)
        status = "✅" if corrected == expected else "❌"
        print(f"{status} {original:25} → {corrected}")


def test_hotmail_corrections():
    """Test des corrections Hotmail"""
    print("\n🔥 Tests Hotmail:")
    print("-" * 50)

    test_cases = [
        ("user@hotmial.com", "user@hotmail.com"),
        ("user@hotmali.com", "user@hotmail.com"),
        ("user@homail.com", "user@hotmail.com"),
        ("user@hotmai.com", "user@hotmail.com"),
        ("user@hotmail.fr", "user@hotmail.fr"),  # Déjà correct
    ]

    for original, expected in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(original)
        status = "✅" if corrected == expected else "❌"
        print(f"{status} {original:25} → {corrected}")


def test_outlook_corrections():
    """Test des corrections Outlook"""
    print("\n📬 Tests Outlook:")
    print("-" * 50)

    test_cases = [
        ("user@outlock.com", "user@outlook.com"),
        ("user@outlok.com", "user@outlook.com"),
        ("user@otlook.com", "user@outlook.com"),
        ("user@outlook.fr", "user@outlook.fr"),  # Déjà correct
    ]

    for original, expected in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(original)
        status = "✅" if corrected == expected else "❌"
        print(f"{status} {original:25} → {corrected}")


def test_yahoo_corrections():
    """Test des corrections Yahoo"""
    print("\n🟣 Tests Yahoo:")
    print("-" * 50)

    test_cases = [
        ("user@yaho.com", "user@yahoo.com"),
        ("user@yahou.com", "user@yahoo.com"),
        ("user@yhoo.com", "user@yahoo.com"),
        ("user@yahoo.fr", "user@yahoo.fr"),  # Déjà correct
    ]

    for original, expected in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(original)
        status = "✅" if corrected == expected else "❌"
        print(f"{status} {original:25} → {corrected}")


def test_french_providers():
    """Test des fournisseurs français"""
    print("\n🇫🇷 Tests fournisseurs français:")
    print("-" * 50)

    test_cases = [
        ("user@orang.fr", "user@orange.fr"),
        ("user@ornage.fr", "user@orange.fr"),
        ("user@wanadoo.fr", "user@wanadoo.fr"),  # Déjà correct
        ("user@fre.fr", "user@free.fr"),
        ("user@sfr.fr", "user@sfr.fr"),  # Déjà correct
    ]

    for original, expected in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(original)
        status = "✅" if corrected == expected else "❌"
        print(f"{status} {original:25} → {corrected}")


def test_no_correction_needed():
    """Test des emails déjà corrects"""
    print("\n✓  Tests emails déjà corrects:")
    print("-" * 50)

    test_cases = [
        "user@gmail.com",
        "user@hotmail.fr",
        "user@outlook.com",
        "user@yahoo.fr",
        "user@orange.fr",
        "user@free.fr",
        "user@icloud.com",
    ]

    for email in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(email)
        status = "✅" if not was_corrected else "❌"
        print(f"{status} {email:25} (aucune correction)")


def test_distance_limit():
    """Test de la limite de distance"""
    print("\n🚫 Tests limite de distance (max 2):")
    print("-" * 50)

    # Ces domaines ont une distance > 2, donc pas de correction
    test_cases = [
        "user@gmxxxxl.com",  # Distance trop grande
        "user@xxxmail.com",  # Distance trop grande
        "user@completely-wrong.com",  # Domaine inconnu
    ]

    for email in test_cases:
        corrected, was_corrected, _ = email_domain_corrector.correct_email(email)
        status = "✅" if not was_corrected else "❌"
        if not was_corrected:
            print(f"{status} {email:30} → Pas de correction (distance trop grande)")
        else:
            print(f"{status} {email:30} → {corrected}")


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TESTS DE CORRECTION AUTOMATIQUE DES DOMAINES EMAIL")
    print("=" * 70)

    test_gmail_corrections()
    test_hotmail_corrections()
    test_outlook_corrections()
    test_yahoo_corrections()
    test_french_providers()
    test_no_correction_needed()
    test_distance_limit()

    print("\n" + "=" * 70)
    print("✅ Tous les tests terminés !")
    print("=" * 70)
