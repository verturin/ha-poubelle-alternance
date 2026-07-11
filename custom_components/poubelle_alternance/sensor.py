"""Capteur Poubelle Alternance."""
from __future__ import annotations

from datetime import timedelta

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ICON_IMPAIRE,
    CONF_ICON_PAIRE,
    CONF_JAUNE_SUR_PAIRE,
    CONF_LABEL_IMPAIRE,
    CONF_LABEL_PAIRE,
    CONF_NAME,
    DEFAULT_ICON_IMPAIRE,
    DEFAULT_ICON_PAIRE,
    DEFAULT_JAUNE_SUR_PAIRE,
    DEFAULT_LABEL_IMPAIRE,
    DEFAULT_LABEL_PAIRE,
    DEFAULT_NAME,
    DOMAIN,
)

# Recalcul régulier : l'état ne change qu'au changement de semaine,
# mais on rafraîchit chaque heure pour couvrir le passage à minuit.
SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure le capteur depuis l'entrée de configuration."""
    async_add_entities([PoubelleAlternanceSensor(entry)])


class PoubelleAlternanceSensor(SensorEntity):
    """Capteur indiquant la poubelle de la semaine courante."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialise le capteur."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_poubelle"

    def _conf(self, key: str, default):
        """Récupère une valeur de config (options prioritaires)."""
        return self._entry.options.get(
            key, self._entry.data.get(key, default)
        )

    @property
    def name(self) -> str:
        """Nom du capteur."""
        return self._conf(CONF_NAME, DEFAULT_NAME)

    def _est_paire(self) -> bool:
        """Retourne True si la semaine ISO courante est paire."""
        semaine = dt_util.now().isocalendar()[1]
        return semaine % 2 == 0

    def _est_jaune(self) -> bool:
        """Détermine si c'est la semaine de la poubelle 'paire' (jaune)."""
        jaune_sur_paire = self._conf(
            CONF_JAUNE_SUR_PAIRE, DEFAULT_JAUNE_SUR_PAIRE
        )
        return self._est_paire() == jaune_sur_paire

    @property
    def native_value(self) -> str:
        """État : libellé de la poubelle de la semaine."""
        if self._est_jaune():
            return self._conf(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE)
        return self._conf(CONF_LABEL_IMPAIRE, DEFAULT_LABEL_IMPAIRE)

    @property
    def icon(self) -> str:
        """Icône dynamique selon la poubelle."""
        if self._est_jaune():
            return self._conf(CONF_ICON_PAIRE, DEFAULT_ICON_PAIRE)
        return self._conf(CONF_ICON_IMPAIRE, DEFAULT_ICON_IMPAIRE)

    @property
    def extra_state_attributes(self) -> dict:
        """Attributs supplémentaires utiles pour les automations."""
        return {
            "semaine_iso": dt_util.now().isocalendar()[1],
            "semaine_paire": self._est_paire(),
        }

    @property
    def device_info(self) -> dict:
        """Regroupe l'entité sous un appareil dédié."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._conf(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "verturin",
            "model": "Poubelle Alternance",
        }
