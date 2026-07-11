"""Intégration Poubelle Alternance pour Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_EXCEPTIONS,
    CONF_HEURE_SORTIE,
    CONF_JOUR_COLLECTE,
    CONF_JOUR_SORTIE,
    CONF_LABEL_IMPAIRE,
    DEFAULT_HEURE_SORTIE,
    DEFAULT_JOUR_COLLECTE,
    DEFAULT_JOUR_SORTIE,
    DEFAULT_LABEL_IMPAIRE,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure l'intégration depuis une entrée de configuration (UI)."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée de configuration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migre les anciennes entrées (v1 -> v2) sans les casser.

    Comble les nouveaux paramètres avec les valeurs par défaut et remplace
    l'ancien libellé "Grise" par "Noire" s'il n'a pas été personnalisé.
    """
    if entry.version < 2:
        data = {**entry.data}

        if data.get(CONF_LABEL_IMPAIRE) == "Grise":
            data[CONF_LABEL_IMPAIRE] = DEFAULT_LABEL_IMPAIRE

        data.setdefault(CONF_JOUR_COLLECTE, DEFAULT_JOUR_COLLECTE)
        data.setdefault(CONF_JOUR_SORTIE, DEFAULT_JOUR_SORTIE)
        data.setdefault(CONF_HEURE_SORTIE, DEFAULT_HEURE_SORTIE)
        data.setdefault(CONF_EXCEPTIONS, [])

        hass.config_entries.async_update_entry(entry, data=data, version=2)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharge l'intégration quand les options changent."""
    await hass.config_entries.async_reload(entry.entry_id)
