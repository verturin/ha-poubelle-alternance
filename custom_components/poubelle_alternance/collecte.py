"""Logique de calcul de la collecte des poubelles.

Centralise le calcul de la couleur de la semaine et de la prochaine
collecte, en tenant compte des exceptions (jours spéciaux) saisies à la main.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .const import EXC_TYPE_ANNULATION, EXC_TYPE_REPORT


def couleur_de_la_semaine(
    jour: date,
    label_paire: str,
    label_impaire: str,
    jaune_sur_paire: bool,
) -> str:
    """Retourne le libellé de la poubelle pour la semaine contenant `jour`.

    Basé sur la parité du numéro de semaine ISO.
    """
    semaine = jour.isocalendar()[1]
    est_paire = semaine % 2 == 0
    # `jaune_sur_paire` True  -> la poubelle "paire" (label_paire) tombe les semaines paires
    if est_paire == jaune_sur_paire:
        return label_paire
    return label_impaire


def _parse_exceptions(exceptions: list | None) -> dict[str, dict]:
    """Indexe les exceptions par date de collecte d'origine (clé ISO 'YYYY-MM-DD').

    Ignore silencieusement les entrées mal formées pour ne jamais planter le capteur.
    """
    resultat: dict[str, dict] = {}
    if not exceptions:
        return resultat
    for exc in exceptions:
        if not isinstance(exc, dict):
            continue
        d = exc.get("date")
        if not d:
            continue
        try:
            # normalise la clé
            cle = date.fromisoformat(str(d)).isoformat()
        except ValueError:
            continue
        resultat[cle] = exc
    return resultat


@dataclass
class Collecte:
    """Représente une collecte concrète (date effective + couleur)."""

    date_collecte: date
    couleur: str
    reportee_depuis: date | None = None  # date d'origine si report
    exceptionnelle: bool = False


def prochaine_collecte(
    maintenant: datetime,
    jour_collecte_iso: int,
    label_paire: str,
    label_impaire: str,
    jaune_sur_paire: bool,
    exceptions: list | None = None,
    horizon_jours: int = 60,
) -> Collecte | None:
    """Calcule la prochaine collecte à partir de `maintenant`.

    - `jour_collecte_iso` : jour de ramassage habituel (1=lundi … 7=dimanche).
    - Les exceptions peuvent annuler ou reporter une collecte, et forcer la couleur.
    - Retourne None si aucune collecte trouvée dans l'horizon.
    """
    exc_index = _parse_exceptions(exceptions)
    aujourdhui = maintenant.date()

    # 1. Rassemble les dates de collecte "théoriques" dans l'horizon,
    #    en partant d'aujourd'hui.
    dates_theoriques: list[date] = []
    for delta in range(horizon_jours + 1):
        jour = aujourdhui + timedelta(days=delta)
        if jour.isocalendar()[2] == jour_collecte_iso:
            dates_theoriques.append(jour)

    # 2. Applique les exceptions et construit la liste des collectes effectives.
    collectes: list[Collecte] = []
    for jour in dates_theoriques:
        exc = exc_index.get(jour.isoformat())
        couleur_defaut = couleur_de_la_semaine(
            jour, label_paire, label_impaire, jaune_sur_paire
        )
        if exc is None:
            collectes.append(Collecte(date_collecte=jour, couleur=couleur_defaut))
            continue

        exc_type = exc.get("type")
        couleur_forcee = exc.get("couleur") or couleur_defaut

        if exc_type == EXC_TYPE_ANNULATION:
            # Pas de collecte ce jour-là : on saute.
            continue

        if exc_type == EXC_TYPE_REPORT:
            nouvelle = exc.get("nouvelle_date")
            try:
                date_reportee = date.fromisoformat(str(nouvelle))
            except (ValueError, TypeError):
                # report mal défini -> on garde la date d'origine
                date_reportee = jour
            collectes.append(
                Collecte(
                    date_collecte=date_reportee,
                    couleur=couleur_forcee,
                    reportee_depuis=jour,
                    exceptionnelle=True,
                )
            )
            continue

        # type inconnu -> collecte normale avec couleur éventuellement forcée
        collectes.append(
            Collecte(
                date_collecte=jour,
                couleur=couleur_forcee,
                exceptionnelle="couleur" in exc,
            )
        )

    # 3. Ajoute les reports "entrants" : une collecte reportée VERS une date
    #    dont l'origine est hors horizon passé proche (cas rare, déjà couvert ci-dessus).
    #    Trie et retourne la première collecte >= aujourd'hui.
    collectes = [c for c in collectes if c.date_collecte >= aujourdhui]
    collectes.sort(key=lambda c: c.date_collecte)

    return collectes[0] if collectes else None
