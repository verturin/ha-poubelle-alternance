# Poubelle Alternance 🗑️♻️

Intégration Home Assistant qui expose un capteur indiquant **quelle poubelle sortir**, en alternant **une semaine sur deux** selon la parité du numéro de semaine ISO.

Reproduit la logique d'un template sensor, mais packagée proprement : installation via HACS, configuration par l'interface (config flow), aucune modification de `configuration.yaml`.

## Fonctionnalités

- Capteur avec état `Jaune` / `Grise` (libellés personnalisables)
- Icône dynamique selon la poubelle de la semaine
- Configuration 100 % via l'UI (installation + options modifiables à tout moment)
- Choix de la poubelle qui tombe sur les semaines paires
- Attributs `semaine_iso` et `semaine_paire` exploitables dans les automations

## Installation via HACS

1. Dans HACS → menu ⋮ → **Dépôts personnalisés**
2. Ajoute `https://github.com/verturin/ha-poubelle-alternance` en catégorie **Intégration**
3. Cherche **Poubelle Alternance** et installe
4. Redémarre Home Assistant
5. **Paramètres → Appareils et services → Ajouter une intégration → Poubelle Alternance**

## Configuration

| Paramètre | Description | Défaut |
|---|---|---|
| Nom du capteur | Nom de l'entité | Poubelle de la semaine |
| Libellé semaine paire | État affiché en semaine paire | Jaune |
| Libellé semaine impaire | État affiché en semaine impaire | Grise |
| Icône semaine paire | Icône MDI | mdi:recycle |
| Icône semaine impaire | Icône MDI | mdi:trash-can |
| Jaune sur semaines paires | Inverse l'alternance si décoché | activé |

## Exemple d'automation

```yaml
alias: Rappel poubelle jaune
trigger:
  - platform: time
    at: "19:00:00"
condition:
  - condition: time
    weekday:
      - sun
  - condition: state
    entity_id: sensor.poubelle_de_la_semaine
    state: "Jaune"
action:
  - service: notify.notify
    data:
      title: "🗑️ Poubelle jaune"
      message: "C'est la semaine de la poubelle jaune, pense à la sortir !"
```

## Note sur le calcul

L'alternance repose sur la parité du numéro de semaine **ISO 8601**. En fin d'année, le passage de la semaine 52/53 à la semaine 1 peut produire deux semaines de même parité consécutives. Pour une alternance strictement infaillible sur plusieurs années, une future version pourra proposer un calcul basé sur une date de référence.

## Licence

MIT
