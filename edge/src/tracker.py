"""Tracking multi-objets par appariement de centroïdes.

Algorithme volontairement simple (pas de filtre de Kalman, pas de
ré-identification par apparence) mais suffisant pour associer une
détection à une identité stable d'une frame à l'autre.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import count
from typing import Dict, List

from .detector import Detection

# Générateur d'identifiants uniques et croissants pour les nouveaux tracks.
# `itertools.count` produit une séquence infinie (1, 2, 3, ...) — chaque
# appel à next() donne le prochain entier, jamais réutilisé.
_id_generator = count(start=1)
