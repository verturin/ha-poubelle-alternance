"""Config flow (UI) pour Poubelle Alternance."""
from __future__ import annotations

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
        }
    )


class PoubelleAlternanceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration initial."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape de configuration lancée par l'utilisateur."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=_schema({})
        )

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
        """Initialise le flux d'options."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modifie les paramètres."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Les options écrasent les données initiales si présentes
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(current)
        )
