from typing import Optional
import pymysql


def create(
    connection: pymysql.connections.Connection,
    customer_id: Optional[int],
    file_id: Optional[int],
    customer_review_id: Optional[int] = None,
    reference: Optional[str] = None,
    perfume_name: Optional[str] = None,
    date: Optional[str] = None,
    quantity: Optional[str] = None,
    source: Optional[str] = None,
    supervisor_id: Optional[int] = None,
    box_type: Optional[str] = None,
    atelier_id: Optional[int] = None,
    atelier_name: Optional[str] = None,
) -> Optional[int]:
    """
    Crée une nouvelle formule liée à un customer (ou customer_review) et à un fichier.

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer (peut être None si review)
        file_id: ID du fichier source (customer_files.id), None pour le flux tablette
        customer_review_id: ID du customer_review (peut être None si customer)
        reference: Référence/identifiant de la formule
        perfume_name: Nom du parfum
        date: Date extraite du formulaire OCR
        quantity: Quantité choisie (10ml, 30ml, 50ml, 100ml, Brume)
        source: Origine de la formule ('ocr' ou 'tablet')
        box_type: Coffret utilisé (optionnel)
        atelier_id: ID de l'atelier choisi côté tablette (référentiel sdp-dashboard, optionnel)
        atelier_name: Nom traduit de l'atelier au moment de la soumission (optionnel)

    Returns:
        ID de la formule créée ou None si erreur
    """
    cursor = None
    try:
        cursor = connection.cursor()

        # Colonnes optionnelles (quantity/source) insérées seulement si fournies,
        # pour rester compatible avec une base sans ces colonnes
        data = {
            "customer_id": customer_id,
            "file_id": file_id,
            "customer_review_id": customer_review_id,
            "reference": reference,
            "perfume_name": perfume_name,
            "date": date,
        }
        if quantity is not None:
            data["quantity"] = quantity
        if source is not None:
            data["source"] = source
        if supervisor_id is not None:
            data["supervisor_id"] = supervisor_id
        if box_type is not None:
            data["box_type"] = box_type
        if atelier_id is not None:
            data["atelier_id"] = atelier_id
        if atelier_name is not None:
            data["atelier_name"] = atelier_name

        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)

        query = f"""
            INSERT INTO formula ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        cursor.execute(query, list(data.values()))

        connection.commit()
        formula_id = cursor.lastrowid

        return formula_id

    except Exception as e:
        print(f"Erreur création formula : {e}")
        connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_id(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> Optional[dict]:
    """
    Récupère une formule par son ID.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule

    Returns:
        Dictionnaire avec les données de la formule ou None si non trouvée
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT f.id, f.customer_id, f.file_id, f.customer_review_id, f.comment,
                   f.reference, f.perfume_name, f.date, f.quantity, f.source, f.reuse_count,
                   f.supervisor_id, f.box_type, f.atelier_id, f.atelier_name,
                   CONCAT(u.first_name, ' ', u.last_name) AS supervisor_name
            FROM formula f
            LEFT JOIN users u ON u.id = f.supervisor_id
            WHERE f.id = %s
        """
        cursor.execute(query, (formula_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération formula {formula_id} : {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_customer_id(
    connection: pymysql.connections.Connection,
    customer_id: int,
) -> list[dict]:
    """
    Récupère l'historique des formules d'un client, triées des plus récentes aux plus anciennes.

    Args:
        connection: Connexion MySQL
        customer_id: ID du client

    Returns:
        Liste de dictionnaires (peut être vide)
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, perfume_name, date, quantity, reuse_count
            FROM formula
            WHERE customer_id = %s
            ORDER BY date DESC, id DESC
        """
        cursor.execute(query, (customer_id,))
        return cursor.fetchall() or []

    except Exception as e:
        print(f"Erreur récupération formules du customer {customer_id} : {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()


def increment_reuse_count(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> Optional[int]:
    """
    Incrémente le compteur de réutilisation d'une formule.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule

    Returns:
        Nouvelle valeur de reuse_count ou None si erreur/formule inconnue
    """
    cursor = None
    try:
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE formula SET reuse_count = reuse_count + 1 WHERE id = %s",
            (formula_id,),
        )
        connection.commit()

        if cursor.rowcount == 0:
            return None

        cursor.execute("SELECT reuse_count FROM formula WHERE id = %s", (formula_id,))
        row = cursor.fetchone()
        return row["reuse_count"] if row else None

    except Exception as e:
        print(f"Erreur incrémentation reuse_count formula {formula_id} : {e}")
        connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_reference(
    connection: pymysql.connections.Connection,
    reference: str,
) -> Optional[dict]:
    """
    Récupère une formule par sa référence.

    Args:
        connection: Connexion MySQL
        reference: Référence de la formule

    Returns:
        Dictionnaire avec les données de la formule ou None si non trouvée
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, customer_id, file_id, customer_review_id, comment, reference, perfume_name, date
            FROM formula
            WHERE reference = %s
        """
        cursor.execute(query, (reference,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération formula par référence {reference} : {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_pending_review_emails(
    connection: pymysql.connections.Connection,
    delay_hours: int = 24,
) -> list[dict]:
    """
    Formules créées depuis au moins `delay_hours`, issues du parcours tablette,
    dont l'email de demande d'avis Google n'a pas encore été envoyé, pour un
    client avec une adresse email connue.

    Returns:
        Liste de dicts {formula_id, perfume_name, customer_id, email, first_name, last_name}
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT f.id AS formula_id, f.perfume_name, c.id AS customer_id,
                   c.email, c.first_name, c.last_name
            FROM formula f
            JOIN customers c ON c.id = f.customer_id
            WHERE f.source = 'tablet'
              AND f.review_email_sent_at IS NULL
              AND f.created_at <= DATE_SUB(NOW(), INTERVAL %s HOUR)
              AND c.email IS NOT NULL AND c.email != ''
        """
        cursor.execute(query, (delay_hours,))
        return cursor.fetchall() or []

    except Exception as e:
        print(f"Erreur récupération formules en attente d'email avis : {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()


def mark_review_email_sent(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> bool:
    """Marque l'email de demande d'avis Google comme envoyé pour cette formule."""
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE formula SET review_email_sent_at = NOW() WHERE id = %s",
            (formula_id,),
        )
        connection.commit()
        return True

    except Exception as e:
        print(f"Erreur marquage email avis envoyé pour formule {formula_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def generate_tablet_reference(
    connection: pymysql.connections.Connection,
    year_month: str,
) -> str:
    """
    Génère la prochaine référence tablette au même format que les références OCR
    (suite de chiffres commençant par '20'), sur le préfixe année+mois donné.

    Args:
        connection: Connexion MySQL
        year_month: Préfixe 'YYMM' (ex: '2607' pour juillet 2026)

    Returns:
        Référence au format '20{YYMM}{NNNNN}' (ex: '20260700001')
    """
    prefix = f"20{year_month}"
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT reference
            FROM formula
            WHERE reference LIKE %s
            ORDER BY reference DESC
            LIMIT 1
        """
        cursor.execute(query, (f"{prefix}%",))
        result = cursor.fetchone()

        last_sequence = 0
        if result and result.get("reference"):
            suffix = result["reference"][len(prefix):]
            if suffix.isdigit():
                last_sequence = int(suffix)

        next_sequence = last_sequence + 1
        return f"{prefix}{next_sequence:05d}"

    finally:
        if cursor is not None:
            cursor.close()


def generate_reused_reference(
    connection: pymysql.connections.Connection,
    source_formula_id: int,
) -> Optional[str]:
    """
    Génère la référence d'une formule recréée à partir d'une formule existante
    (parcours "recommencer à partir d'une formule") : '<référence source>-N', où N
    est le prochain numéro de réutilisation de CETTE référence source précise
    (ex: 20260900001 -> 20260900001-2 -> si on repart de -2 : 20260900001-2-2).

    Returns:
        La nouvelle référence, ou None si la formule source n'a pas de référence.
    """
    cursor = None
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT reference FROM formula WHERE id = %s", (source_formula_id,))
        source = cursor.fetchone()
        source_reference = source.get("reference") if source else None
        if not source_reference:
            return None

        prefix = f"{source_reference}-"
        cursor.execute(
            "SELECT reference FROM formula WHERE reference LIKE %s",
            (f"{prefix}%",),
        )
        last_sequence = 1
        for row in cursor.fetchall():
            suffix = row["reference"][len(prefix):]
            if suffix.isdigit():
                last_sequence = max(last_sequence, int(suffix))

        return f"{prefix}{last_sequence + 1}"

    finally:
        if cursor is not None:
            cursor.close()


def delete(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> bool:
    """
    Supprime une formule par son ID.
    Les notes associées sont supprimées automatiquement via CASCADE.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule à supprimer

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM formula
            WHERE id = %s
        """
        cursor.execute(query, (formula_id,))

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur suppression formula {formula_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def update(
    connection: pymysql.connections.Connection,
    formula_id: int,
    **kwargs,
) -> bool:
    """
    Met à jour une formule avec les champs fournis.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule
        **kwargs: Champs à mettre à jour (customer_id, file_id, customer_review_id, comment)

    Returns:
        True si succès, False sinon
    """
    if not kwargs:
        return True

    cursor = None
    try:
        cursor = connection.cursor()

        # Construire la requête dynamiquement
        allowed_fields = {"customer_id", "file_id", "customer_review_id", "comment", "reference", "perfume_name", "date", "box_type"}
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not fields_to_update:
            return True

        set_clause = ", ".join([f"{field} = %s" for field in fields_to_update.keys()])
        values = list(fields_to_update.values()) + [formula_id]

        query = f"""
            UPDATE formula
            SET {set_clause}
            WHERE id = %s
        """
        cursor.execute(query, values)
        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur mise à jour formula {formula_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()


def transfer_formulas_to_customer(
    connection: pymysql.connections.Connection,
    customer_review_id: int,
    customer_id: int
) -> bool:
    """
    Transfère toutes les formules d'un customer_review vers un customer.
    Met à jour customer_id et met customer_review_id à NULL.

    Args:
        connection: Connexion MySQL
        customer_review_id: ID du customer_review source
        customer_id: ID du customer destination

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            UPDATE formula
            SET customer_id = %s, customer_review_id = NULL
            WHERE customer_review_id = %s
        """
        cursor.execute(query, (customer_id, customer_review_id))
        connection.commit()

        rows_affected = cursor.rowcount
        print(f"✅ {rows_affected} formule(s) transférée(s) de customer_review {customer_review_id} vers customer {customer_id}")
        return True

    except Exception as e:
        print(f"Erreur transfert formules : {e}")
        connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()

