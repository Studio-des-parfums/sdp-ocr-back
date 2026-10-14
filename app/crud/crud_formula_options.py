import pymysql


def create(connection: pymysql.connections.Connection, formula_id: int, name: str) -> None:
    """
    Associe une option choisie à une formule. Pas de FK vers la table `options` du
    dashboard : elle vit dans une base MySQL distincte (voir formula_option, migration
    q3r4s5t6u7v8) — on stocke juste le nom, même principe que les notes.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO formula_option (formula_id, name) VALUES (%s, %s)",
            (formula_id, name),
        )
        connection.commit()
    except Exception as e:
        print(f"Erreur création option pour la formule {formula_id} : {e}")
        connection.rollback()
    finally:
        cursor.close()


def get_by_formula(connection: pymysql.connections.Connection, formula_id: int) -> list:
    """Récupère les noms des options choisies pour une formule donnée."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT name FROM formula_option WHERE formula_id = %s ORDER BY id ASC",
            (formula_id,),
        )
        return [row["name"] for row in cursor.fetchall()]
    finally:
        cursor.close()


def delete_by_formula(connection: pymysql.connections.Connection, formula_id: int) -> None:
    """Retire toutes les options associées à une formule (pas d'id exposé côté API pour les
    options : on remplace toujours la liste entière plutôt que de diffier par id, contrairement
    aux notes)."""
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM formula_option WHERE formula_id = %s", (formula_id,))
        connection.commit()
    except Exception as e:
        print(f"Erreur suppression options pour la formule {formula_id} : {e}")
        connection.rollback()
    finally:
        cursor.close()


def replace_for_formula(connection: pymysql.connections.Connection, formula_id: int, names: list) -> None:
    """Remplace toutes les options d'une formule par la liste donnée."""
    delete_by_formula(connection, formula_id)
    for name in names:
        cleaned = (name or "").strip()
        if cleaned:
            create(connection, formula_id, cleaned)
