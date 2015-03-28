Database
========

Ville
------------
    - population
    - Point (longitude, latitude)
    - priceOfTravel
    - description wikipedia? (texte)
    - altitude (float)

Monthly stats
---------------
    - month
    - city (foreign key)
    - tempMin
    - tempMax
    - mm de pluie / neige?
    - humidité? (ou c'est trop corrélé avec pluie?)
    - heures d'ensoleillement

Plan
=======
    
    - faire des des schémas avec SqlAlchemy
    - script qui scrape wikipedia pour remplir une database postgresql
    - faire du code Flask avec comme endpoints
        - le data (/data?left=1.2&right=3.4&...) où on passe les coordonnées de
          la boite dans laquelle on zoom et ça nous retourne le data des N
          villes les plus populeuses qui matchent la boite
        - une adresse principale (/) qui met une map et call /data chaque fois
          qu'on déplace ou que le zoom change
            - il y aura aussi un slider global pour la date qui déterminera
              quelle journée sera utilisée. Comme le data est sur 12 mois on
              pourra extrapoler entre ça (on peut sûrement faire mieux que
              linéaire, au moins quadratique)
    - hoster ca qqpart, openshift.com ?


References
==========

SqlAlchemy + GeoAlchemy
http://www.sqlalchemy.org/
https://geoalchemy-2.readthedocs.org/en/0.2.4/

Flask
http://flask.pocoo.org/

Example qui marche (sans sqlalchemy mais avec OSM)
https://github.com/ryanj/flask-postGIS/
https://blog.openshift.com/instant-mapping-applications-with-postgis-and-nodejs/
http://parkgis-shifter.rhcloud.com/

Qui est hosté sur 
www.openshift.com
