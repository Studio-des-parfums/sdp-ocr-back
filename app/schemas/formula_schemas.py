from pydantic import BaseModel


class NoteBase(BaseModel):
    """
    Schéma de base pour une note de parfum
    """

    name: str
    quantity: str | None = None


class NoteCreate(NoteBase):
    """
    Schéma pour créer une note (sans ID)
    """

    pass


class NoteUpdate(BaseModel):
    """
    Schéma pour mettre à jour une note
    """

    id: int | None = None  # Si présent = UPDATE, si absent = INSERT
    name: str
    quantity: str | None = None


class NoteResponse(NoteBase):
    """
    Schéma de réponse pour une note
    """

    id: int
    formula_id: int

    class Config:
        from_attributes = True


class FormulaBase(BaseModel):
    """
    Schéma de base pour une formule
    """

    customer_id: int | None = None
    file_id: int | None = None
    customer_review_id: int | None = None
    comment: str | None = None
    reference: str | None = None
    perfume_name: str | None = None
    date: str | None = None
    quantity: str | None = None
    source: str | None = None
    supervisor_id: int | None = None
    box_type: str | None = None
    atelier_id: int | None = None
    atelier_name: str | None = None


class FormulaCreate(FormulaBase):
    """
    Schéma pour créer une formule avec ses notes (issue d'une fiche scannée)
    """

    file_id: int
    top_notes: list[NoteCreate] = []
    heart_notes: list[NoteCreate] = []
    base_notes: list[NoteCreate] = []


class FormulaUpdateNotes(BaseModel):
    """
    Schéma pour mettre à jour les notes d'une formule

    Pour chaque type de note:
    - Notes avec 'id' → UPDATE si modifiées
    - Notes sans 'id' → INSERT (nouvelles notes)
    - Notes absentes de la liste → DELETE (supprimées)
    """

    top_notes: list[NoteUpdate] | None = None
    heart_notes: list[NoteUpdate] | None = None
    base_notes: list[NoteUpdate] | None = None
    booster_notes: list[NoteUpdate] | None = None
    options: list[str] | None = None
    comment: str | None = None
    reference: str | None = None
    perfume_name: str | None = None
    date: str | None = None
    box_type: str | None = None


class FormulaResponse(FormulaBase):
    """
    Schéma de réponse pour une formule avec ses notes
    """

    id: int
    supervisor_name: str | None = None
    top_notes: list[NoteResponse] = []
    heart_notes: list[NoteResponse] = []
    base_notes: list[NoteResponse] = []
    booster_notes: list[NoteResponse] = []
    options: list[str] = []

    class Config:
        from_attributes = True


class FormulaDeleteResponse(BaseModel):
    """
    Schéma de réponse pour la suppression d'une formule
    """

    success: bool
    message: str
    formula_id: int
