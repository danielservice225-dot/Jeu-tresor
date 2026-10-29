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

# Renforcer l'anti-triche : le premier départ de l'onglet entraîne GAME OVER.
anti_start = html.find("// ===================== ANTI-CHEAT =====================")
anti_end = html.find("// ===================== ADMIN =====================", anti_start)
if anti_start < 0 or anti_end < 0:
    raise SystemExit("ERREUR : bloc anti-triche introuvable ; déploiement annulé.")
anti_cheat = r'''// ===================== ANTI-CHEAT =====================
let cheatHandled = false;
function registerCheatAttempt(reason) {
  if (!state.started || state.cheated || cheatHandled) return;
  cheatHandled = true;
  state.cheated = true;
  clearInterval(state.timerInterval);
  savePlayer({ status: "cheater", score: state.score, level: state.level + 1, alert: reason, alertTime: new Date().toISOString() });
  document.getElementById("goMessage").innerHTML =
    "🚨 <strong>" + (state.player || "Joueur") + "</strong>, sortie détectée (" + reason + ").<br><br>" +
    "<strong>GAME OVER</strong> : ta partie est interrompue. Tu dois recommencer depuis le début.";
  state.started = false;
  showScreen("gameover");
  document.getElementById("cheatOverlay").classList.add("show");
  playSound("error");
}
document.addEventListener("visibilitychange", () => {
  if (state.started && document.hidden) registerCheatAttempt("onglet quitté ou application masquée");
});
// Sur mobile, window.blur peut se déclencher à l’ouverture du clavier virtuel.\n// On évite ce faux positif qui empêchait la saisie et le démarrage dans Chrome.\n// ===================== ADMIN =====================
'''
html = html[:anti_start] + anti_cheat + html[anti_end + len("// ===================== ADMIN ====================="):]
 

# Rendre les énigmes moins guidées : ne pas donner le nom exact du commentaire/source à chercher.
html = html.replace(
    'Cherche un commentaire HTML contenant <code>INDICE_NIVEAU_4</code>.<br>Quel est le <strong>code secret</strong> mentionné ?',
    'Explore les traces laissées par le créateur dans cette page et retrouve le <strong>code secret</strong>.'
)

# Habillage motivant, façon jeu éducatif : micro-animations, progression et encouragements.
style_patch = r"""
<style id="quest-motivation-style">
:root{--quest-violet:#7657ff;--quest-lime:#b7f34a;--quest-ink:#17223b}
button,.btn{transition:transform .16s ease,filter .16s ease,box-shadow .16s ease}
button:hover,.btn:hover{transform:translateY(-2px);filter:brightness(1.05);box-shadow:0 8px 22px #7657ff30}
button:active,.btn:active{transform:scale(.97)}
.quest-cheer{position:fixed;z-index:99999;left:50%;top:16px;transform:translate(-50%,-18px);opacity:0;pointer-events:none;background:#17223b;color:white;border:2px solid #b7f34a;border-radius:22px;padding:13px 20px;font-weight:800;box-shadow:0 12px 35px #11182735;max-width:90vw;text-align:center;transition:opacity .25s,transform .25s}
.quest-cheer.show{opacity:1;transform:translate(-50%,0)}
.quest-confetti{position:fixed;z-index:99998;top:-20px;width:9px;height:14px;border-radius:3px;pointer-events:none;animation:questFall 1.8s ease-in forwards}
@keyframes questFall{to{transform:translateY(110vh) rotate(720deg);opacity:.15}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
"""
if "quest-motivation-style" not in html:
    html = html.replace("</head>", style_patch + "\n</head>", 1)

motivation_script = r"""
<script id="quest-motivation-script">
(function(){
  if(window.__questMotivationLoaded)return;window.__questMotivationLoaded=true;
  const cheer=document.createElement('div');cheer.className='quest-cheer';cheer.setAttribute('role','status');cheer.setAttribute('aria-live','polite');document.body.appendChild(cheer);
  let last='';let hideTimer;
  function celebrate(message){
    if(!message||message===last)return;last=message;cheer.textContent=message;cheer.classList.add('show');clearTimeout(hideTimer);hideTimer=setTimeout(()=>cheer.classList.remove('show'),2300);
    for(let i=0;i<18;i++){const p=document.createElement('i');p.className='quest-confetti';p.style.left=(Math.random()*100)+'vw';p.style.background=['#7657ff','#b7f34a','#ffca55','#ff6b9a','#45d7f2'][i%5];p.style.animationDelay=(Math.random()*.35)+'s';document.body.appendChild(p);setTimeout(()=>p.remove(),2300)}
  }
  const success=/bonne réponse|bravo|correct|félicitations|bien joué|excellent|énigme résolue|niveau terminé|trésor trouvé/i;
  const observer=new MutationObserver(records=>{for(const r of records){for(const n of r.addedNodes){if(n.nodeType!==1)continue;const t=(n.innerText||n.textContent||'').trim();if(t.length<100&&success.test(t)){celebrate(['🌟 Super, tu avances !','🔥 Excellent travail !','🧠 Esprit de détective !','🎉 Bravo, continue !'][Math.floor(Math.random()*4)]);return}}}});
  observer.observe(document.body,{childList:true,subtree:true});
})();
</script>
"""
if "quest-motivation-script" not in html:
    html = html.replace("</body>", motivation_script + "\n</body>", 1)

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
