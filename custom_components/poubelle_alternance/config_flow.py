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
from homeassistant.helpers import selector

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
    EXC_TYPE_ANNULATION,
    EXC_TYPE_REPORT,
)

JOURS_OPTIONS = [
    {"value": "1", "label": "Lundi"},
    {"value": "2", "label": "Mardi"},
    {"value": "3", "label": "Mercredi"},
    {"value": "4", "label": "Jeudi"},
    {"value": "5", "label": "Vendredi"},
    {"value": "6", "label": "Samedi"},
    {"value": "7", "label": "Dimanche"},
]


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
            ): selector.TextSelector(),
            vol.Required(
                CONF_LABEL_PAIRE,
                default=defaults.get(CONF_LABEL_PAIRE, DEFAULT_LABEL_PAIRE),
            ): selector.TextSelector(),
            vol.Required(
                CONF_LABEL_IMPAIRE,
                default=defaults.get(CONF_LABEL_IMPAIRE, DEFAULT_LABEL_IMPAIRE),
            ): selector.TextSelector(),
            vol.Required(
                CONF_ICON_PAIRE,
                default=defaults.get(CONF_ICON_PAIRE, DEFAULT_ICON_PAIRE),
            ): selector.IconSelector(),
            vol.Required(
                CONF_ICON_IMPAIRE,
                default=defaults.get(CONF_ICON_IMPAIRE, DEFAULT_ICON_IMPAIRE),
            ): selector.IconSelector(),
            vol.Required(
                CONF_JAUNE_SUR_PAIRE,
                default=defaults.get(
                    CONF_JAUNE_SUR_PAIRE, DEFAULT_JAUNE_SUR_PAIRE
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_DATE_REFERENCE,
                default=defaults.get(
                    CONF_DATE_REFERENCE, DEFAULT_DATE_REFERENCE
                ),
            ): selector.TextSelector(),
            vol.Required(
                CONF_JOUR_COLLECTE,
                default=str(
                    defaults.get(CONF_JOUR_COLLECTE, DEFAULT_JOUR_COLLECTE)
                ),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=JOURS_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_JOUR_SORTIE,
                default=str(
                    defaults.get(CONF_JOUR_SORTIE, DEFAULT_JOUR_SORTIE)
                ),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=JOURS_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_HEURE_SORTIE,
                default=int(
                    defaults.get(CONF_HEURE_SORTIE, DEFAULT_HEURE_SORTIE)
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=23, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_EXCEPTIONS,
                default=exceptions_vers_texte(defaults.get(CONF_EXCEPTIONS)),
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
    )


def _normalise(user_input: dict[str, Any]) -> dict[str, Any]:
    """Convertit les types du formulaire et valide les entrées.

    - jours de collecte/sortie : chaîne "1".."7" -> entier
    - heure de sortie : float du NumberSelector -> entier
    - exceptions : texte multi-lignes -> liste structurée
    - date de référence : conservée seulement si valide (sinon repli ISO)
    """
    data = dict(user_input)

    for cle in (CONF_JOUR_COLLECTE, CONF_JOUR_SORTIE):
        try:
            data[cle] = int(data.get(cle))
        except (TypeError, ValueError):
            pass

    try:
        data[CONF_HEURE_SORTIE] = int(float(data.get(CONF_HEURE_SORTIE)))
    except (TypeError, ValueError):
        data[CONF_HEURE_SORTIE] = DEFAULT_HEURE_SORTIE

    data[CONF_EXCEPTIONS] = texte_vers_exceptions(data.get(CONF_EXCEPTIONS, ""))

    ref = (data.get(CONF_DATE_REFERENCE) or "").strip()
    if ref:
        try:
            date.fromisoformat(ref)
            data[CONF_DATE_REFERENCE] = ref
        except ValueError:
            data[CONF_DATE_REFERENCE] = ""
    else:
        data[CONF_DATE_REFERENCE] = ""
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
        return PoubelleAlternanceOptionsFlow()


class PoubelleAlternanceOptionsFlow(OptionsFlow):
    """Gère la modification des options après installation."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modifie les paramètres."""
        if user_input is not None:
            return self.async_create_entry(title="", data=_normalise(user_input))

        # `self.config_entry` est fourni automatiquement par OptionsFlow.
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(current))
