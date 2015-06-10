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

