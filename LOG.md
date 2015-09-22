27 avril 2015
==================

trous dans le data
-------------------

http://dbpedia.org/page/Vancouver  a des properties comme dbpprop:aprChill
mais http://dbpedia.org/page/Seattle en a pas
La seule différence que je vois dans le code de wikipedia c'est que pour
Seattle, la boite meteo est dans un template dans un template.

Dans les 2 cas, je comprends même pas comment la data de Vancouver arrive dans
dbpedia, i.e. je trouve pas le code qui fait ça.

J'essaie de comprendre comment ça se rend là pour commencer, ça va peut-être
me dire ce qu'il aut changer pour que tout fonctionne, ou avoir du code à copier
pour faire ça.

28 avril 2015
=============

trous dans le data
---------------------

Bon j'ai compris je pense : dans le code wikipedia d'un article, ça ressemble à

    {{Weather box
    |location = [[Vancouver International Airport]]
    |metric first = Y
    |single line = Y
    |Jan maximum humidex = 17.2
    |Feb maximum humidex = 18.0
    ...

Et ça ça se fait mapper tout seul à des properties?
Mais le Weather box lui a pas l'air coder en détails, i.e. il doit juste faire
le default behaviour de copier les keys dans des properties et c'est tout.
Alors quand, comme sur la page de Seattle, tout ce qu'il y a c'est un 
{{Seattle weatherbox}} qui en fait pointe vers
http://en.wikipedia.org/wiki/Template:Seattle_weatherbox,
alors on dirait que c'est pas parsé.

Reste à vérifier si c'est bien le cas, et/ou demander à des gens qui
connaissent ça


istanbul
--------

ville manquante, vérifier pourquoi, il y en a sûrement d'autres
probablement pcq c'est pas un dbo:city ?

1er mai 2015
=============

Bon maintenant il y a aussi des templates du genre
http://en.wikipedia.org/wiki/Template:Weather_box/concise_C
qu'il fauddrait parser à part anyway, si je vais à la route de passer par
l'API wikipedia pour trouver tout ce qui utilise le Weather Box et ensuite 
suivre les liens jusqu'aux villes pour les nested templates.

Autre solution : utiliser dbpedia pour identifier les villes, ensuite aller
sur la page wikipedia et pogner l'HTML, et parser le tableau, ça me semble
peut-être le plus simple... Il y aura pas tant de cas étant donné que le
template Weather Box fait tjrs la même chose. Tout ce qui a l'air de changer
ce sont les unités de mesure? (F vs C par exemple)...

5 mai 2015
===========
Parser l'HTML directement semble assez simple (quoi que lent, 5-10 secondes par
ville). Il va rester à voir ce qui est mieux pour trouver toutes les villes
(dbpedia ou un truc du genre API wikipedia directement). Ensuite je risque de
devoir filter les villes (par exemple sur leur population) pour pas aller chercher
la meteo de trop de villes pour rien, pcq lent. 

À faire pour la prochaine fois : pe faire le ménage de dbpedia_experimentation.py
si ça se trouve tout ce qui est pertinent est dans fetch_dbpedia.py. Ensuite
Remplacer les morceaux par le parsing wikipedia et essayer ça? Peut-être utiliser
dbo:Settlement à la place de City et ça va tout régler...?


11 mai
========
commencé à coder rapidement la nouvelle version pour pogner la meteo. voir fichier
add_wiki_data_to_dump.py


7 juin
======
j'avance le code, je l'ai roulé avec toutes les "Settlements" qui ont au moins
1M habitants (ça en fait environ 2600). ÇA va être déjà ça pour tester.
Rester à vérifier que le parser fait tout ça comme il faut (il y a encore des
blobs météos qu'on ne supporte pas ou des trucs qu'il ne parse pas etc.)


9 juin
=======
je semble être capable d'ajouter les données venant de wikipedia (la météo)
directement (et non pas dbpedia) à partir de mes 2600 Settlements. Reste à
vérifier si on a bien toutes les villes de 1M d'habitants et plus ou si qqch
manque au passage...
Il y a tjrs quelques cas que je ne parse pas comme il faut dans le tableau du
climat, voir les logs de add_wiki_data_to_dump.py

10 juin
========
commencé à utiliser le logging python

11 juin
========
Tout le pipeline est pas mal là. Tout semble rouler pour pogner le data.
Reste à faire quelques petites vérifications voir si tout est là et à quel point
j'ai du data de trop (genre de provinces et cie)...

12 juin
========
On semble avoir quelques populations brisées, et ça semble être de la faute de
dbpedia qui parse ça moyennement bien. Je vais essayer de mitiger les problèmes
mais au final c'est peut-être pas tant grave. On a aussi plusieurs districts
trop gros pour être des villes.
Finalement j'ai réglé tout ça (je crois). je fetch dbp:city OR yago:city au lieu
de Settlements, ca a l'air d'être mieux.

Il y a encore Porthmouth qui à 76 de pop (TODO sûrement rang 76, vérifier ça)

16 juin
=======
premier vrai problème de mapping! En gros ce qu'on voit de la carte sur un
écran, ce n'est pas un rectangle, mais une forme louche, donc je ne peux pas
seulement avec une query SQL seulement trouver les villes qui sont entre les 4
coins du "rectangle". Je dois trouver les villes qui sont à l'intérieur de la
forme louche qui m'apparait à moi comme un rectangle.

17 juin
=======
les coordonnés lat/long venant de dbpedia sont pas bonnes tout le temps, 
ça utilise 35E devient 35 au lieu de -35, ou quelque chose comme ça
exemple : melbourne. le package python wikipedia est capable d'aller chercher
les coordonnées comme du monde lui, alors l'utiliser ou le faire même-moi,
à partir de wikipedia

ça s'en vient je pogne ça de l,API, mais y a certains villes (e.g. suffolk,
virginia) où les coordonnées sont bizarre. premièrement je dois mettre
coprimary=all comme option et deuxièmement je reçois qqch de bizarre

21 juin
=======
j'ai réglé l'histoire de suffolk en différenciant title et name pour une ville
(title = "Suffolk, Virginia" que j'utilise pour le wiki API et name je garde
seulement Suffolk).
Maintenant ça marche bien sauf qu'il manque encore des villes. Il y a des villes
dans dbpedia qui ne sont ni dbo:city ni yago:city, comme Lima. Mais Lima était
aussi un yago:capital alors j'ai ajouté ça, on va voir combien on en pogne...

Aussi on devrait pe pogner la liste des pays en premier, ensuite de trouver les
villes les plus grosses par pays. L'intérêt c'est qu'on pourrait afficher sur
la carte N villes par pays. Comme ça les petits pays à côté de gros pays vont
quand même avoir qqch à montrer. Quand on voit le monde au complet, on pourrait
s'Arranger pour pas seulement voir plein de points en chine et aucun en amérique
On pourrait avoir au moins une ville par pays aussi...
Bon j'ai trouvé (comment ça se fait que j'ai pas vu ça avant??) plusieurs
databases des villes du monde. Je pourrais partir de ça. Ensuite par contre ça
va peut-être être plus dur trouver l'entrée wiki qui correspond à ça, par exmeple
pour les villes qui ont le même nom qu'une autre ville plus connue

20 juillet
==========
pleins d'updates. rajouté un region_index et country_index, pour l'instant ça va
faire la job pour bien plotter ça. reste à vérifier les villes qui n'ont pas été
trouvées dans wikipédia (par exemple des myanmar VS burma), voir les logs
ensuite va falloir penser à loader plus efficacement, ça hang un mini peu au début
quand ça load

24 juillet
==========
idées pour mieux dispercer les villes:
faire une genre de moyenne de
- rank par région
- rank par pays
- isolation (distance moyenne des voisins) par région
- isolation (même chose) par pays
- nb de statistiques météo (pertinentes)

découper la map en N rectangles et prendre une ville par rectangle. -> 
idiot si y a de l`ocean... ah non ca marche y aura just emoins de villes, ce
qui est pas fou

25 juillet
==========
j'ai essayé de découper la map en N rectangles. c'est très lent mais je n'ai pas
essayé d'optimiser, sauf que dès qu'on bouge la map à peine, ça doit tout recaculer
refetcher et ça donne un résultat différent (aussi bon mais trop différent pour
avoir à peine bougé).
je suis en train de penser que peut-être chaque ville devrait avoir un zoom level
à partir duquel elle doit apparaitre, calculé en avance et déjà dans la BD. 
Comme ça la query serait seulement "tout ce qu'on fait dans zoom level X". Pour
chaque zoom level plus précis, on ne ferait qu'ajouter plus de ville. Pour
un zoom level donné, là ça a du sens une formule qui prend en compte quelques
critères (population, isolation etc.)... en tous cas penser à ça!

26 juillet
==========
J'ai fini par faire mon idee de priority_index, j'ajoute les villes une après
l'autre dans un ordre qui fait en sorte que chacun nouvelle ville est loin des
autres. ça semble marcher pas pire!

28 juillet
==========
Pour l'instant si on recherce "phnom penh, phnom penh" (ville, region) et qu'on
trouve qqch, même si c'est du caca et que (ville, pays) retourne la bonne chose,
on skip. corriger ça.

17 aout
========
C'est rendu quand même beau avec bootstrap. Reste à arranger les trucs multi-device...
Faudrait mettre les flèches directement sous la map et que le panneau à droite soit
optionnel (seulement sur les grosses devices).
trouver un moyen (j'ai commecné à mettre un "order" pour les stats) d'avoir les
stats tjrs dans le même ordre. Probablement retourner une liste de la database,
déjà en ordre, règlerait le problème
Aussi le clear-all ne devrait pas être dans le panneau qui scroll, il devrait
tjrs rester en place
Londre est pas là!

24 aout
=======
j'ai arrangé le view en utilisant des tables :S au poubelles bootstrap... sauf
pour qq détails
à faire : 
- arranger le look des stats sur la map
- faire quand quand on hover sur une table, ça highlight sa ville... penser à ça

11 sept
=======
y a qq villes, du genre
page.wiki('santa ana, cusco')
qui retournent pas la bonne ville
on pourrait régler ça en cherchant ville, pays avant ville, province, mais ca
ca va faire plein de problèmes pour e.g. springfield aux states
Donc il faudrait plutôt qqch comme vérifier que le titre de la ville marche
la recherche une fois cherchée. Pour mon exemple, on verrait que Cusco != Santa
Ana.
Aussi faut vraiment rajouter un mode Recherche par nom de ville. 

16 sept
=======
j'ai pe réglé le problème pour Santa Ana et autres, en vérifiant que le "title"
de la page wikipedia match (en terme de distance de string) le nom de la ville

