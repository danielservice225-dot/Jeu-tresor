from pathlib import Path
import re

p = Path("public/index.html")
if not p.exists():
    raise SystemExit("Erreur : public/index.html introuvable après extraction du ZIP.")

html = p.read_text(encoding="utf-8")

# Corrige les deux questions dont les chaînes JavaScript contiennent des retours à la ligne bruts.
html = html.replace(
    'text: "Un Arduino Uno possède <strong>14 broches digitales</strong> (0 à 13).<br>\n    Si on allume les broches paires uniquement (0, 2, 4, 6, 8, 10, 12),<br>\n    <strong>combien de broches sont allumées ?</strong>",',
    'text: "Un Arduino Uno possède <strong>14 broches digitales</strong> (0 à 13).<br>Si on allume les broches paires uniquement (0, 2, 4, 6, 8, 10, 12),<br><strong>combien de broches sont allumées ?</strong>",'
)
html = html.replace(
    'text: "Un message est caché dans le code source de cette page...<br><br>\n    Cherche un commentaire HTML contenant <code>INDICE_NIVEAU_4</code>.<br>\n    Quel est le <strong>code secret</strong> mentionné ?",',
    'text: "Un message est caché dans le code source de cette page...<br><br>Cherche un commentaire HTML contenant <code>INDICE_NIVEAU_4</code>.<br>Quel est le <strong>code secret</strong> mentionné ?",'
)

p.write_text(html, encoding="utf-8")

# Vérifie la syntaxe JavaScript du jeu avant de publier.
match = re.search(r"<script[^>]*>(.*?)</script>", html, re.S)
if not match:
    raise SystemExit("Erreur : aucun script JavaScript trouvé.")
Path("/tmp/game-check.js").write_text(match.group(1), encoding="utf-8")
print("Jeu extrait et chaînes JavaScript corrigées.")
