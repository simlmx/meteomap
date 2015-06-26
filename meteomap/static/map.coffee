# create a map in the "map" div, set the view to a given place and zoom
map = L.map('map').setView([51.505, -0.09], 5);
# create a tile layer sourced from mapbox
L.tileLayer('https://{s}.tiles.mapbox.com/v4/simlmx.3899a192/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2ltbG14IiwiYSI6IjhiOGM5MTQwNzcwYjI2N2I2OWZmZDJmZDEzZmM1MjRmIn0.9gqLDwhf2tDseRNXlFTGRg').addTo(map)
# FIXME put the keys from mapbox in the config and delete those keys...

class City
    constructor: (@name, @coords, @meteo) ->

    getData: (code, month) ->
        return @meteo[code][month]

    addToMap: (month, map) ->
        html = "#{@getData('avgLow', month)} -
                #{@getData('avgHigh', month)}"
        icon = L.divIcon({className: 'citydata', html: html, iconSize: null})
        @marker = L.marker(@coords, {title:@name, icon:icon})
        # @marker2 = L.marker(@coords)
        @marker.addTo map
        # @marker2.addTo map

    removeFromMap: (map) ->
        map.removeLayer @marker
        # map.removeLayer @marker2

console.log 'patate'

cities = []
addCities = (data) ->
    # devrait pouvoir etre accelerer en faisant qqch d'intelligent, i.e.
    # ne pas tout deleter a chaque fois. certains markers doivent normalement
    # rester et on va les remettre anyway
    while cities.length > 0
        city = cities.pop()
        city.removeFromMap map

    for name, infos of data
        coords = [infos.lat, infos.long]
        monthly_stats = infos.month_stats
        city = new City(name, coords, monthly_stats)
        cities.push city
        city.addToMap(0, map)

mapCb = (e) ->
    console.log 'patate'
    bounds = map.getBounds()
    coords = 
        n: bounds.getNorth()# - (bounds.getNorth() - bounds.getSouth())*.1
        s: bounds.getSouth()# + (bounds.getNorth() - bounds.getSouth())*.1
        e: bounds.getEast()# - (bounds.getEast() - bounds.getWest())*.1
        w: bounds.getWest()# + (bounds.getEast() - bounds.getWest())*.1

    $.get('data', coords, addCities, 'json')

    # debug
    # while frame.length > 0
    #     map.removeLayer frame.pop()
    # polygon = L.polygon([[coords.n, coords.w],
    #                      [coords.n, coords.e],
    #                      [coords.s, coords.e],
    #                      [coords.s, coords.w]])
    # frame.push polygon
    # polygon.addTo(map)

map.on('moveend', mapCb)
mapCb({})

# debuging
# map.on('click', onClick)
# onClick = (e) ->
#     m = L.marker(e.latlng, {title:e.latlng})
#     markers.push m
#     m.addTo map
