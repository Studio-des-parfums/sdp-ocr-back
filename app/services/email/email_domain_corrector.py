class EmailDomainCorrector:
    """
    Service pour corriger automatiquement les fautes dans les domaines d'email
    """

    # Liste des extensions populaires
    POPULAR_EXTENSIONS = [
        "com",
        "fr",
        "net",
        "org",
        "eu",
        "be",
        "ch",
        "de",
        "uk",
        "it",
        "es",
        "ca",
        "co.uk",
        "com.fr",
    ]

    # Liste des domaines populaires
    POPULAR_DOMAINS = [
        # Gmail
        "gmail.com",
        "googlemail.com",
        # Microsoft
        "hotmail.com",
        "hotmail.fr",
        "outlook.com",
        "outlook.fr",
        "live.com",
        "live.fr",
        "msn.com",
        # Yahoo
        "yahoo.com",
        "yahoo.fr",
        "ymail.com",
        # Orange/Wanadoo
        "orange.fr",
        "wanadoo.fr",
        # Free
        "free.fr",
        # SFR
        "sfr.fr",
        "neuf.fr",
        # Apple
        "icloud.com",
        "me.com",
        "mac.com",
        # ProtonMail
        "protonmail.com",
        "proton.me",
        # Autres
        "laposte.net",
        "aol.com",
    ]

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calcule la distance de Levenshtein entre deux chaînes
        (nombre minimum de modifications pour transformer s1 en s2)

        Args:
            s1: Première chaîne
            s2: Deuxième chaîne

        Returns:
            Distance de Levenshtein (nombre de modifications)
        """
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Coût de l'insertion, suppression, substitution
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def is_likely_typo(self, domain: str, suggested_domain: str, distance: int) -> bool:
        """
        Détermine si c'est vraiment une faute de frappe ou un domaine personnalisé légitime

        Args:
            domain: Domaine original
            suggested_domain: Domaine suggéré
            distance: Distance de Levenshtein

        Returns:
            True si c'est probablement une faute, False si c'est un domaine légitime
        """
        # Si la distance est de 1, c'est très probablement une faute
        if distance == 1:
            return True

        # Si le domaine contient un tiret, c'est probablement un domaine pro personnalisé
        # Ex: mon-entreprise.fr, my-company.com
        if "-" in domain:
            return False

        # Si le domaine a plus de 15 caractères, c'est probablement personnalisé
        # Ex: maentreprisepersonnalisee.fr
        if len(domain) > 20:
            return False

        # Si c'est un domaine très proche d'un fournisseur populaire, c'est une faute
        # Ex: gmil.com → gmail.com (distance 1)
        if distance <= 2:
            return True

        return False

    def suggest_domain(self, domain: str, max_distance: int = 2) -> str | None:
        """
        Suggère une correction pour un domaine mal orthographié
        SEULEMENT si c'est probablement une faute de frappe

        Args:
            domain: Le domaine à vérifier (ex: "gmil.com")
            max_distance: Distance maximale acceptable (par défaut 2)

        Returns:
            Le domaine corrigé ou None si pas de suggestion

        Exemples:
            >>> suggest_domain("gmil.com")
            "gmail.com"

            >>> suggest_domain("mon-entreprise.fr")
            None  # Domaine pro légitime
        """
        domain_lower = domain.lower().strip()

        # Si le domaine est déjà correct
        if domain_lower in self.POPULAR_DOMAINS:
            return None

        best_match = None
        best_distance = float("inf")

        # Comparer avec tous les domaines populaires
        for popular_domain in self.POPULAR_DOMAINS:
            distance = self.levenshtein_distance(domain_lower, popular_domain)

            # Si la distance est acceptable et meilleure que la précédente
            if distance <= max_distance and distance < best_distance:
                best_distance = distance
                best_match = popular_domain

        # Vérifier si c'est vraiment une faute ou un domaine personnalisé
        if best_match and self.is_likely_typo(domain_lower, best_match, best_distance):
            return best_match

        return None

    def fix_punctuation(self, email: str) -> tuple[str, bool]:
        """
        Corrige les problèmes de ponctuation dans l'email

        Args:
            email: Email à corriger

        Returns:
            Tuple (email_corrigé, a_été_corrigé)
        """
        original_email = email
        was_corrected = False

        # Remplacer les virgules par des points dans le domaine
        # contact@gmail,com → contact@gmail.com
        if "@" in email:
            local_part, domain = email.rsplit("@", 1)

            # Remplacer virgule par point
            if "," in domain:
                domain = domain.replace(",", ".")
                email = f"{local_part}@{domain}"
                was_corrected = True
                print(f"🔧 Ponctuation corrigée : {original_email} → {email}")

            # Remplacer point-virgule par point
            if ";" in domain:
                domain = domain.replace(";", ".")
                email = f"{local_part}@{domain}"
                was_corrected = True
                print(f"🔧 Ponctuation corrigée : {original_email} → {email}")

            # Remplacer deux-points par point
            if ":" in domain:
                domain = domain.replace(":", ".")
                email = f"{local_part}@{domain}"
                was_corrected = True
                print(f"🔧 Ponctuation corrigée : {original_email} → {email}")

        return email, was_corrected

    def suggest_extension(self, extension: str, max_distance: int = 1) -> str | None:
        """
        Suggère une correction pour une extension mal orthographiée

        Args:
            extension: L'extension à vérifier (ex: "con", "fer")
            max_distance: Distance maximale acceptable (par défaut 1)

        Returns:
            L'extension corrigée ou None

        Exemples:
            >>> suggest_extension("con")
            "com"

            >>> suggest_extension("fer")
            "fr"
        """
        extension_lower = extension.lower().strip()

        # Si l'extension est déjà correcte
        if extension_lower in self.POPULAR_EXTENSIONS:
            return None

        best_match = None
        best_distance = float("inf")

        # Comparer avec toutes les extensions populaires
        for popular_ext in self.POPULAR_EXTENSIONS:
            distance = self.levenshtein_distance(extension_lower, popular_ext)

            if distance <= max_distance and distance < best_distance:
                best_distance = distance
                best_match = popular_ext

        return best_match

    def correct_email(self, email: str) -> tuple[str, bool, str | None]:
        """
        Corrige automatiquement un email si le domaine contient une faute

        Args:
            email: L'email à vérifier

        Returns:
            Tuple (email_corrigé, a_été_corrigé, domaine_original)
            - email_corrigé: L'email avec le domaine corrigé (ou original si pas de faute)
            - a_été_corrigé: True si une correction a été appliquée
            - domaine_original: Le domaine original s'il a été corrigé, None sinon

        Exemples:
            >>> correct_email("dwain@gmil.com")
            ("dwain@gmail.com", True, "gmil.com")

            >>> correct_email("dwain@gmail.com")
            ("dwain@gmail.com", False, None)
        """
        original_email = email
        was_corrected = False

        # Étape 1 : Corriger la ponctuation
        email, punct_corrected = self.fix_punctuation(email)
        if punct_corrected:
            was_corrected = True

        # Vérifier que c'est un email valide
        if "@" not in email:
            return email, was_corrected, None if not was_corrected else original_email.split("@")[1]

        # Extraire la partie locale et le domaine
        local_part, domain = email.rsplit("@", 1)

        # Étape 2 : Corriger l'extension si elle est mal orthographiée
        # Ex: gmail.con → gmail.com, contact.fer → contact.fr
        if "." in domain:
            domain_parts = domain.rsplit(".", 1)
            if len(domain_parts) == 2:
                domain_name, extension = domain_parts

                suggested_extension = self.suggest_extension(extension)
                if suggested_extension:
                    corrected_domain = f"{domain_name}.{suggested_extension}"
                    domain = corrected_domain
                    email = f"{local_part}@{domain}"
                    was_corrected = True
                    print(f"📧 Extension corrigée : {original_email} → {email}")

        # Étape 3 : Corriger le domaine complet
        suggested_domain = self.suggest_domain(domain)

        if suggested_domain:
            corrected_email = f"{local_part}@{suggested_domain}"
            print(f"📧 Domaine corrigé : {email} → {corrected_email}")
            return (
                corrected_email,
                True,
                original_email.split("@")[1] if "@" in original_email else None,
            )

        if was_corrected:
            return email, True, original_email.split("@")[1] if "@" in original_email else None

        return email, False, None


# Instance globale
email_domain_corrector = EmailDomainCorrector()
