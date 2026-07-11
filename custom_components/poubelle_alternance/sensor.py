"""Capteurs Poubelle Alternance."""
from __future__ import annotations

from datetime import timedelta

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .collecte import couleur_de_la_semaine, prochaine_collecte
from .const import (
    CONF_DATE_REFERENCE,
    CONF_EXCEPTIONS,
    CONF_HEURE_SORTIE,
    CONF_ICON_IMPAIRE,
    CONF_ICON_PAIRE,
    CONF_JAUNE_SUR_PAIRE,
    CONF_JOUR_COLLECTE,
    CONF_JOUR_SORTIE,
    CONF_LABEL_IMPAIRE,
    CONF_LABEL_PAIRE,
    CONF_NAME,
    DEFAULT_DATE_REFERENCE,
    DEFAULT_HEURE_SORTIE,
    DEFAULT_ICON_IMPAIRE,
    DEFAULT_ICON_PAIRE,
    DEFAULT_JAUNE_SUR_PAIRE,
    DEFAULT_JOUR_COLLECTE,
    DEFAULT_JOUR_SORTIE,
    DEFAULT_LABEL_IMPAIRE,
    DEFAULT_LABEL_PAIRE,
    DEFAULT_NAME,
    DOMAIN,
)

# Recalcul chaque heure : l'état ne change qu'au changement de jour/semaine,
# mais on rafraîchit régulièrement pour couvrir le passage à minuit et le soir.
SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs depuis l'entrée de configuration."""
    async_add_entities(
        [
            PoubelleSemaineSensor(entry),
            ProchaineCollecteSensor(entry),
        ]
    )


class _BasePoubelle(SensorEntity):
    """Base commune : accès à la configuration (options prioritaires)."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    def _conf(self, key: str, default):
        return self._entry.options.get(key, self._entry.data.get(key, default))

    @property
    def _nom_base(self) -> str:
        return self._conf(CONF_NAME, DEFAULT_NAME)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._nom_base,
            "manufacturer": "verturin",
            "model": "Poubelle Alternance",
        }


class PoubelleSemaineSensor(_BasePoubelle):
    """Poubelle de la semaine courante (Jaune / Noire)."""

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_semaine"

    @property
    def name(self) -> str:
        return self._nom_base

    def _couleur(self) -> str:
        return couleur_de_la_semaine(
            dt_util.now().date(),
            self._conf(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE),
            self._conf(CONF_LABEL_IMPAIRE, DEFAULT_LABEL_IMPAIRE),
            self._conf(CONF_JAUNE_SUR_PAIRE, DEFAULT_JAUNE_SUR_PAIRE),
            self._conf(CONF_DATE_REFERENCE, DEFAULT_DATE_REFERENCE),
        )

    @property
    def native_value(self) -> str:
        return self._couleur()

    @property
    def icon(self) -> str:
        label_paire = self._conf(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE)
        if self._couleur() == label_paire:
            return self._conf(CONF_ICON_PAIRE, DEFAULT_ICON_PAIRE)
        return self._conf(CONF_ICON_IMPAIRE, DEFAULT_ICON_IMPAIRE)

    @property
    def extra_state_attributes(self) -> dict:
        now = dt_util.now()
        return {
            "semaine_iso": now.isocalendar()[1],
            "semaine_paire": now.isocalendar()[1] % 2 == 0,
        }


class ProchaineCollecteSensor(_BasePoubelle):
    """Prochaine collecte : date effective, couleur, et rappel du soir.

    Tient compte des exceptions (annulation / report) et du rythme
    « sortie mercredi soir, ramassage jeudi matin ».
    """

    _attr_device_class = "date"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_prochaine_collecte"

    @property
    def name(self) -> str:
        return f"{self._nom_base} - prochaine collecte"

    def _calcul(self):
        now = dt_util.now()
        return now, prochaine_collecte(
            maintenant=now,
            jour_collecte_iso=int(
                self._conf(CONF_JOUR_COLLECTE, DEFAULT_JOUR_COLLECTE)
            ),
            label_paire=self._conf(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE),
            label_impaire=self._conf(CONF_LABEL_IMPAIRE, DEFAULT_LABEL_IMPAIRE),
            jaune_sur_paire=self._conf(
                CONF_JAUNE_SUR_PAIRE, DEFAULT_JAUNE_SUR_PAIRE
            ),
            exceptions=self._conf(CONF_EXCEPTIONS, []),
            date_reference=self._conf(
                CONF_DATE_REFERENCE, DEFAULT_DATE_REFERENCE
            ),
        )

    @property
    def native_value(self):
        _, collecte = self._calcul()
        if collecte is None:
            return None
        return collecte.date_collecte.isoformat()

    @property
    def icon(self) -> str:
        _, collecte = self._calcul()
        if collecte is None:
            return "mdi:trash-can-outline"
        label_paire = self._conf(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE)
        if collecte.couleur == label_paire:
            return self._conf(CONF_ICON_PAIRE, DEFAULT_ICON_PAIRE)
        return self._conf(CONF_ICON_IMPAIRE, DEFAULT_ICON_IMPAIRE)

    @property
    def extra_state_attributes(self) -> dict:
        now, collecte = self._calcul()
        if collecte is None:
            return {"couleur": None, "a_sortir_ce_soir": False}

        jour_sortie = int(self._conf(CONF_JOUR_SORTIE, DEFAULT_JOUR_SORTIE))
        heure_sortie = int(self._conf(CONF_HEURE_SORTIE, DEFAULT_HEURE_SORTIE))

        # "À sortir ce soir" = la veille de la collecte (jour de sortie),
        # après l'heure configurée. On calcule la veille effective de la collecte.
        veille = collecte.date_collecte - timedelta(days=1)
        a_sortir_ce_soir = (
            now.date() == veille and now.hour >= heure_sortie
        )
        # Cas où le jour de sortie configuré diffère : on se cale sur la veille réelle.
        jours_restants = (collecte.date_collecte - now.date()).days

        return {
            "couleur": collecte.couleur,
            "date_collecte": collecte.date_collecte.isoformat(),
            "jours_restants": jours_restants,
            "a_sortir_ce_soir": a_sortir_ce_soir,
            "jour_sortie_prevu": veille.isoformat(),
            "collecte_exceptionnelle": collecte.exceptionnelle,
            "reportee_depuis": (
                collecte.reportee_depuis.isoformat()
                if collecte.reportee_depuis
                else None
            ),
        }
