"""Config flow (UI) pour Poubelle Alternance."""
from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
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
    EXC_TYPE_ANNULATION,
    EXC_TYPE_REPORT,
)

JOURS = {
    1: "Lundi",
    2: "Mardi",
    3: "Mercredi",
    4: "Jeudi",
    5: "Vendredi",
    6: "Samedi",
    7: "Dimanche",
}


def exceptions_vers_texte(exceptions: list | None) -> str:
    """Convertit la liste d'exceptions en texte éditable (une par ligne)."""
    if not exceptions:
        return ""
    lignes = []
    for exc in exceptions:
        if not isinstance(exc, dict) or not exc.get("date"):
            continue
        if exc.get("type") == EXC_TYPE_REPORT:
            ligne = f"{exc['date']} report {exc.get('nouvelle_date', '')}".strip()
        else:
            ligne = f"{exc['date']} annulation"
        if exc.get("couleur"):
            ligne += f" {exc['couleur']}"
        lignes.append(ligne)
    return "\n".join(lignes)


def texte_vers_exceptions(texte: str | None) -> list[dict]:
    """Parse le texte des exceptions.

    Formats acceptés (un par ligne) :
      2026-12-25 annulation
      2026-05-01 report 2026-05-02
      2026-04-02 report 2026-04-03 Jaune
      2026-11-11 annulation Noire
    """
    resultat: list[dict] = []
    if not texte:
        return resultat
    for brute in texte.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        parts = ligne.split()
        try:
            date.fromisoformat(parts[0])
        except (ValueError, IndexError):
            # ligne invalide -> ignorée
            continue
        exc: dict[str, Any] = {"date": parts[0]}
        if len(parts) >= 2 and parts[1].lower() == EXC_TYPE_REPORT:
            exc["type"] = EXC_TYPE_REPORT
            if len(parts) >= 3:
                try:
                    date.fromisoformat(parts[2])
                    exc["nouvelle_date"] = parts[2]
                    if len(parts) >= 4:
                        exc["couleur"] = parts[3]
                except ValueError:
                    exc["couleur"] = parts[2]
        else:
            exc["type"] = EXC_TYPE_ANNULATION
            # couleur éventuelle en dernière position
            if len(parts) >= 3:
                exc["couleur"] = parts[2]
        resultat.append(exc)
    return resultat


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Construit le schéma du formulaire avec des valeurs par défaut."""
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
            ): str,
            vol.Required(
                CONF_LABEL_PAIRE,
                default=defaults.get(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE),
            ): str,
            vol.Required(
                CONF_LABEL_IMPAIRE,
                default=defaults.get(CONF_LABEL_IMPAIRE, DEFAULT_LABEL_IMPAIRE),
            ): str,
            vol.Required(
                CONF_ICON_PAIRE,
                default=defaults.get(CONF_ICON_PAIRE, DEFAULT_ICON_PAIRE),
            ): str,
            vol.Required(
                CONF_ICON_IMPAIRE,
                default=defaults.get(CONF_ICON_IMPAIRE, DEFAULT_ICON_IMPAIRE),
            ): str,
            vol.Required(
                CONF_JAUNE_SUR_PAIRE,
                default=defaults.get(
                    CONF_JAUNE_SUR_PAIRE, DEFAULT_JAUNE_SUR_PAIRE
                ),
            ): bool,
            vol.Required(
                CONF_JOUR_COLLECTE,
                default=defaults.get(CONF_JOUR_COLLECTE, DEFAULT_JOUR_COLLECTE),
            ): vol.In(JOURS),
            vol.Required(
                CONF_JOUR_SORTIE,
                default=defaults.get(CONF_JOUR_SORTIE, DEFAULT_JOUR_SORTIE),
            ): vol.In(JOURS),
            vol.Required(
                CONF_HEURE_SORTIE,
                default=defaults.get(CONF_HEURE_SORTIE, DEFAULT_HEURE_SORTIE),
            ): vol.All(int, vol.Range(min=0, max=23)),
            vol.Optional(
                CONF_EXCEPTIONS,
                default=exceptions_vers_texte(defaults.get(CONF_EXCEPTIONS)),
            ): str,
        }
    )


def _normalise(user_input: dict[str, Any]) -> dict[str, Any]:
    """Transforme le texte des exceptions en liste structurée."""
    data = dict(user_input)
    data[CONF_EXCEPTIONS] = texte_vers_exceptions(data.get(CONF_EXCEPTIONS, ""))
    return data


class PoubelleAlternanceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration initial."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape de configuration lancée par l'utilisateur."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=_normalise(user_input)
            )

        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Retourne le flux d'options."""
        return PoubelleAlternanceOptionsFlow(config_entry)


class PoubelleAlternanceOptionsFlow(OptionsFlow):
    """Gère la modification des options après installation."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modifie les paramètres."""
        if user_input is not None:
            return self.async_create_entry(title="", data=_normalise(user_input))

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(current))
