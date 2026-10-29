from pathlib import Path
import re
import subprocess
import sys

html_path = Path("public/index.html")
if not html_path.exists():
    raise SystemExit("ERREUR : public/index.html absent après extraction du ZIP.")

html = html_path.read_text(encoding="utf-8")

# JavaScript n'autorise pas les retours à la ligne bruts dans ces chaînes entre guillemets.
fixes = [
    (
        'text: "Un Arduino Uno possède <strong>14 broches digitales</strong> (0 à 13).<br>\n    Si on allume les broches paires uniquement (0, 2, 4, 6, 8, 10, 12),<br>\n    <strong>combien de broches sont allumées ?</strong>",',
        'text: "Un Arduino Uno possède <strong>14 broches digitales</strong> (0 à 13).<br>Si on allume les broches paires uniquement (0, 2, 4, 6, 8, 10, 12),<br><strong>combien de broches sont allumées ?</strong>",'
    ),
    (
        'text: "Un message est caché dans le code source de cette page...<br><br>\n    Cherche un commentaire HTML contenant <code>INDICE_NIVEAU_4</code>.<br>\n    Quel est le <strong>code secret</strong> mentionné ?",',
        'text: "Un message est caché dans le code source de cette page...<br><br>Cherche un commentaire HTML contenant <code>INDICE_NIVEAU_4</code>.<br>Quel est le <strong>code secret</strong> mentionné ?",'
    )
]
for old, new in fixes:
    if old not in html:
        # Idempotence : si déjà corrigé, continuer ; sinon arrêter au lieu de publier un jeu cassé.
        if new not in html:
            raise SystemExit("ERREUR : la structure attendue d'une question a changé ; déploiement annulé.")
    else:
        html = html.replace(old, new)

html_path.write_text(html, encoding="utf-8")

match = re.search(r"<script[^>]*>(.*?)</script>", html, re.S)
if not match:
    raise SystemExit("ERREUR : aucun script JavaScript trouvé dans index.html.")

check_path = Path("/tmp/game-check.js")
check_path.write_text(match.group(1), encoding="utf-8")
result = subprocess.run(["node", "--check", str(check_path)], capture_output=True, text=True)
if result.returncode:
    sys.stderr.write(result.stderr)
    raise SystemExit("ERREUR : syntaxe JavaScript invalide ; le site ne doit pas être publié.")
print("OK : HTML extrait, deux erreurs de syntaxe corrigées, JavaScript validé.")
