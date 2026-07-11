"""Constantes pour l'intégration Poubelle Alternance."""

DOMAIN = "poubelle_alternance"

# Clés de configuration
CONF_NAME = "name"
CONF_LABEL_PAIRE = "label_paire"
CONF_LABEL_IMPAIRE = "label_impaire"
CONF_ICON_PAIRE = "icon_paire"
CONF_ICON_IMPAIRE = "icon_impaire"
CONF_JAUNE_SUR_PAIRE = "jaune_sur_paire"
CONF_JOUR_SORTIE = "jour_sortie"
CONF_JOUR_COLLECTE = "jour_collecte"
CONF_HEURE_SORTIE = "heure_sortie"
CONF_EXCEPTIONS = "exceptions"
CONF_DATE_REFERENCE = "date_reference"

# Valeurs par défaut
DEFAULT_NAME = "Poubelle de la semaine"
DEFAULT_LABEL_PAIRE = "Jaune"
DEFAULT_LABEL_IMPAIRE = "Noire"
DEFAULT_ICON_PAIRE = "mdi:recycle"
DEFAULT_ICON_IMPAIRE = "mdi:trash-can"
DEFAULT_JAUNE_SUR_PAIRE = True

# Date de référence : un jour de la semaine où la poubelle "paire" (Jaune) est
# de sortie. L'alternance est ensuite comptée en nombre de semaines depuis
# cette date (méthode infaillible, insensible au changement d'année ISO).
# 2026-06-03 (mercredi) = semaine Jaune, comme l'ancien template YAML.
DEFAULT_DATE_REFERENCE = "2026-06-03"

# Rythme de collecte : sortie le mercredi soir, ramassage le jeudi matin.
# Indices ISO : lundi=1 … dimanche=7
DEFAULT_JOUR_SORTIE = 3       # mercredi (soir où l'on sort le bac)
DEFAULT_JOUR_COLLECTE = 4     # jeudi (matin du ramassage)
DEFAULT_HEURE_SORTIE = 18     # heure à partir de laquelle on considère "à sortir ce soir"

# --- Exceptions (jours spéciaux définis à la main) ---
# Chaque exception est un dict :
#   {"date": "2026-12-25", "type": "annulation"}
#   {"date": "2026-05-01", "type": "report", "nouvelle_date": "2026-05-02"}
#   {"date": "2026-04-02", "type": "report", "nouvelle_date": "2026-04-03",
#    "couleur": "Jaune"}   # couleur optionnelle pour forcer la poubelle ce jour-là
EXC_TYPE_ANNULATION = "annulation"
EXC_TYPE_REPORT = "report"
