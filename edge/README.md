# Edge Agent — EdgeSentinel

## Prérequis

**Python 3.11 est requis** (pas 3.12+, pas 3.14). PyTorch, dont dépend
Ultralytics/YOLOv8, ne publie ses builds que pour un sous-ensemble de
versions Python à un instant donné — au moment de l'écriture, 3.11 est la
version la plus sûre et la plus largement supportée par tout l'écosystème.

Vérifiez votre version disponible :
```bash
python3.11 --version
```

Si absente (macOS) :
```bash
brew install python@3.11
```

## Installation

```bash
$(brew --prefix python@3.11)/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pip install -r requirements.txt
```
