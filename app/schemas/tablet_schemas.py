from pydantic import BaseModel, Field


class TabletNote(BaseModel):
    """Note choisie sur la tablette (nom canonique du référentiel)"""

    name: str
    quantity: str | None = None


class TabletSubmissionCreate(BaseModel):
    """Payload complet envoyé par la tablette après confirmation"""

    gender: str | None = None
    first_name: str
    last_name: str
    birth_date: str | None = Field(None, description="Format YYYY-MM-DD")
    job: str | None = None
    country: str | None = None
    city: str | None = None
    booking_source: str | None = None
    phone: str
    email: str
    has_allergy: bool | None = None
    liability_accepted: bool | None = None
    rgpd_consent: bool
    quantity: str | None = None
    perfume_name: str | None = None
    supervisor_id: int | None = None
    atelier_id: int | None = None
    atelier_name: str | None = None
    reused_from_formula_id: int | None = Field(
        None,
        description="Si renseigné, la référence est dérivée de celle de cette formule (ex: 20260900001-2)",
    )
    top_notes: list[TabletNote] = []
    heart_notes: list[TabletNote] = []
    base_notes: list[TabletNote] = []
    booster_notes: list[TabletNote] = []
    options: list[str] = []


class TabletSubmissionResponse(BaseModel):
    """Résultat de l'enregistrement d'une soumission tablette"""

    customer_id: int
    formula_id: int
    customer_was_existing: bool
    matched_by: str | None = Field(None, description="'email' ou 'phone' si client existant")


class NoteCatalogItem(BaseModel):
    """Une note du référentiel"""

    code: str
    name: str


class NotesCatalogResponse(BaseModel):
    """Référentiel des notes disponibles, groupées par type"""

    top_notes: list[NoteCatalogItem]
    heart_notes: list[NoteCatalogItem]
    base_notes: list[NoteCatalogItem]


class CustomerSearchResult(BaseModel):
    """Client retrouvé par email ou téléphone, à faire valider par le client"""

    id: int
    first_name: str | None = None
    last_name: str | None = None
    city: str | None = None
    email: str | None = None
    phone: str | None = None
    gender: str | None = None


class FormulaHistoryItem(BaseModel):
    """Une formule passée d'un client, pour l'écran de choix"""

    id: int
    perfume_name: str | None = None
    date: str | None = None
    quantity: str | None = None
    reuse_count: int = 0


class FormulaDetail(FormulaHistoryItem):
    """Détail complet d'une formule, pour la modal de consultation"""

    top_notes: list[TabletNote] = []
    heart_notes: list[TabletNote] = []
    base_notes: list[TabletNote] = []
    booster_notes: list[TabletNote] = []
    options: list[str] = []
    atelier_id: int | None = None
    atelier_name: str | None = None


class FormulaReuseResponse(BaseModel):
    """Résultat de l'incrémentation du compteur de réutilisation"""

    formula_id: int
    reuse_count: int


class SuggestQuantitiesRequest(BaseModel):
    """Notes choisies + préférences client, pour dosage IA en ml"""

    top_notes: list[str] = []
    heart_notes: list[str] = []
    base_notes: list[str] = []
    intensity: str = Field(
        ..., description="'light', 'moderate' ou 'strong' (libellé localisé accepté)"
    )
    total_volume_ml: float = Field(..., gt=0, description="Taille du flacon souhaitée, en ml")
    box_set: str | None = Field(
        None,
        description="Coffret choisi (ex: 'Classic'), pour appliquer les bonnes règles de dosage max",
    )


class SuggestedNoteQuantity(BaseModel):
    """Quantité en ml calculée par l'IA pour une note"""

    name: str
    quantity_ml: float


class SuggestQuantitiesResponse(BaseModel):
    """Répartition en ml de chaque note, calculée par l'IA selon l'intensité et le volume total"""

    top_notes: list[SuggestedNoteQuantity] = []
    heart_notes: list[SuggestedNoteQuantity] = []
    base_notes: list[SuggestedNoteQuantity] = []
    total_volume_ml: float
