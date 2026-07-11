# Poubelle Alternance 🗑️♻️

Intégration Home Assistant qui indique **quelle poubelle sortir**, en alternant **une semaine sur deux** selon la parité du numéro de semaine ISO, avec gestion du rythme de collecte et des jours spéciaux.

Installation via HACS, configuration par l'interface (config flow), aucune modification de `configuration.yaml`.

## Fonctionnalités

- Capteur **poubelle de la semaine** : état `Jaune` / `Noire` (libellés personnalisables), icône dynamique.
- Capteur **prochaine collecte** : date effective du prochain ramassage, couleur associée, et indicateur « à sortir ce soir ».
- Rythme de collecte configurable — par défaut **sortie le mercredi soir, ramassage le jeudi matin**.
- **Jours spéciaux** définis à la main : annulation ou report d'une collecte, avec couleur forçable.
- Configuration 100 % via l'UI, options modifiables à tout moment.

## Installation via HACS

1. Dans HACS → menu ⋮ → **Dépôts personnalisés**
2. Ajoute `https://github.com/verturin/ha-poubelle-alternance` en catégorie **Intégration**
3. Cherche **Poubelle Alternance** et installe
4. Redémarre Home Assistant
5. **Paramètres → Appareils et services → Ajouter une intégration → Poubelle Alternance**

## Configuration

| Paramètre | Description | Défaut |
|---|---|---|
| Nom du capteur | Nom de base des entités | Poubelle de la semaine |
| Libellé semaine paire | État en semaine paire | Jaune |
| Libellé semaine impaire | État en semaine impaire | Noire |
| Icône semaine paire | Icône MDI | mdi:recycle |
| Icône semaine impaire | Icône MDI | mdi:trash-can |
| Jaune sur semaines paires | Inverse l'alternance si décoché | activé |
| Jour de ramassage | Jour de collecte | Jeudi |
| Jour de sortie du bac | Jour où sortir le bac | Mercredi |
| Heure de sortie | Heure ≥ à partir de laquelle « à sortir ce soir » | 18 |
| Jours spéciaux | Exceptions (voir ci-dessous) | vide |

## Jours spéciaux (exceptions)

Une exception par ligne, dans le champ **Jours spéciaux**. La date est celle du **ramassage habituel** concerné (le jeudi).

```
2026-12-24 annulation
2026-05-01 report 2026-05-02
2026-04-02 report 2026-04-03 Jaune
```

- `annulation` : pas de collecte cette semaine-là.
- `report AAAA-MM-JJ` : la collecte est déplacée à la nouvelle date.
- Une couleur en fin de ligne (`Jaune` / `Noire`) force la poubelle pour cette collecte.
- Les lignes commençant par `#` et les lignes invalides sont ignorées.

## Entités exposées

- `sensor.poubelle_de_la_semaine` → `Jaune` ou `Noire`, attributs `semaine_iso`, `semaine_paire`.
- `sensor.poubelle_de_la_semaine_prochaine_collecte` → date ISO du prochain ramassage, attributs : `couleur`, `date_collecte`, `jours_restants`, `a_sortir_ce_soir`, `jour_sortie_prevu`, `collecte_exceptionnelle`, `reportee_depuis`.

## Exemple d'automation (rappel mercredi soir)

```yaml
alias: Rappel sortie poubelle
trigger:
  - platform: state
    entity_id: sensor.poubelle_de_la_semaine_prochaine_collecte
    attribute: a_sortir_ce_soir
    to: true
action:
  - service: notify.notify
    data:
      title: "🗑️ Sortir la poubelle"
      message: >
        Ce soir, sortez la poubelle
        {{ state_attr('sensor.poubelle_de_la_semaine_prochaine_collecte', 'couleur') }}
        (ramassage {{ states('sensor.poubelle_de_la_semaine_prochaine_collecte') }}).
```

## Note sur le calcul

L'alternance repose sur la parité du numéro de semaine **ISO 8601**. En fin d'année, le passage de la semaine 52/53 à la semaine 1 peut produire deux semaines de même parité consécutives ; utilise un report/annulation ponctuel si besoin.

## Licence

MIT
