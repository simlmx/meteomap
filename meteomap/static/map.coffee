MONTHNAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
    'Oct', 'Nov', 'Dec']

MIN_RED = [255,230,230]
MAX_RED = [204,0,0]
MIN_BLUE = [230,230,255]
MAX_BLUE = [0,0,204]
MIN_GREEN = [230,255,230]
MAX_GREEN = [0,120,0]
BLACK = [0,0,0]

# create a map in the "map" div, set the view to a given place and zoom
map = L.map('map').setView([51.505, -0.09], 5)
# create a tile layer sourced from mapbox
L.tileLayer('https://{s}.tiles.mapbox.com/v4/simlmx.3899a192/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2ltbG14IiwiYSI6IjhiOGM5MTQwNzcwYjI2N2I2OWZmZDJmZDEzZmM1MjRmIn0.9gqLDwhf2tDseRNXlFTGRg').addTo(map)
# FIXME put the keys from mapbox in the config and delete those keys...
#

month = (new Date()).getMonth()
$('#month').text(MONTHNAMES[month])

updateCitiesMonth = ->
    for c in cities
        c.removeFromMap(map)
        c.addToMap(month, map)
        $('#month').text(MONTHNAMES[month])

$('#prev_btn').click ->
    month -= 1
    if month < 0
        month += 12
    updateCitiesMonth()

$('#next_btn').click ->
    month += 1
    if month > 11
        month -= 12
    updateCitiesMonth()

rgb2hex = (red, green, blue) ->
    rgb = blue | (green << 8) | (red << 16)
    return '#' + (0x1000000 + rgb).toString(16).slice(1)

# rgb_min = min color
# rgb_max = max color
# min = min value
# max = max value
# val = value we want a color for
gradient = (rgb_min, rgb_max, min, max, val) ->
    if val <= min
        return rgb_min
    else if val >= max
        return rgb_max
    delta = (rgb_max[i] - rgb_min[i] for i in [0,1,2])
    # FIXME make a better interpolation
    rgb = (rgb_min[i] + delta[i] * (val-min)/(max-min) for i in [0,1,2])
    return rgb

# perceivedBrightness = (rgb) ->
#     [r,g,b] = rgb
#     return Math.sqrt(
#         r*r * .299 +
#         g*g * .587 +
#         b*b * .114)

# textColorFromBg = (rgb) ->
#     console.log perceivedBrightness(rgb)
#     if perceivedBrightness(rgb) > 120
#         return [0,0,0]
#     return [255,255,255]

temperatureToHtml = (value) ->
    if value is null
        return ""
    if value > 10
        rgb = gradient(MIN_RED, MAX_RED, 10, 40, value)
    else
        rgb = gradient(MAX_BLUE, MIN_BLUE, -15, 10, value)
    # rgb_txt = textColorFromBg(rgb)
    rgb_txt = BLACK
    return "<div class=\"temperature\" style=\"\
            background-color: #{rgb2hex(rgb...)};\
            color: #{rgb2hex(rgb_txt...)}\
            \">#{value}°C</div>"

precipitationToHtml = (value) ->
    if value is null
        return ""
    rgb = gradient(MIN_GREEN, MAX_GREEN, 0, 250, value)
    # rgb_txt = textColorFromBg(rgb)
    rgb_txt = BLACK
    return "<div class=\"temperature\" style=\"\
            background-color: #{rgb2hex(rgb...)};\
            color: #{rgb2hex(rgb_txt...)}\
            \">#{value}mm</div>"


class City
    constructor: (@name, @coords, @meteo) ->

    getData: (code, month) ->
        if code not of @meteo
            return null
        return @meteo[code][month]

    addToMap: (month, map) ->
        high = @getData('avgHigh', month)
        prec = @getData('precipitation', month)
        if prec is null
            prec = @getData('rain', month)
        html = "#{temperatureToHtml(high)}"
        html += "#{precipitationToHtml(prec)}"

        # FIXME update markers (and corresponding icons) when we move the map
        # but only do $('icon').html(...) when we move the month slider
        icon = L.divIcon({className: 'citydata', html: html, iconSize: null})
        @marker = L.marker(@coords, {title:@name, icon:icon})
        # @marker2 = L.marker(@coords)
        @marker.addTo map
        # @marker2.addTo map

    removeFromMap: (map) ->
        map.removeLayer @marker
        # map.removeLayer @marker2

cities = []
loadCities = (data) ->
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
        city.addToMap(month, map)

refreshCities = (e) ->
    bounds = map.getBounds()
    coords = 
        n: bounds.getNorth()# - (bounds.getNorth() - bounds.getSouth())*.1
        s: bounds.getSouth()# + (bounds.getNorth() - bounds.getSouth())*.1
        e: bounds.getEast()# - (bounds.getEast() - bounds.getWest())*.1
        w: bounds.getWest()# + (bounds.getEast() - bounds.getWest())*.1

    $.get('data', coords, loadCities, 'json')

    # debug
    # while frame.length > 0
    #     map.removeLayer frame.pop()
    # polygon = L.polygon([[coords.n, coords.w],
    #                      [coords.n, coords.e],
    #                      [coords.s, coords.e],
    #                      [coords.s, coords.w]])
    # frame.push polygon
    # polygon.addTo(map)

map.on('moveend', refreshCities)
refreshCities({})

# debuging
# map.on('click', onClick)
# onClick = (e) ->
#     m = L.marker(e.latlng, {title:e.latlng})
#     markers.push m
#     m.addTo map
