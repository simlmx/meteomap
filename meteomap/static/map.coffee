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
map = L.map('map').setView([45.505, -73.0], 5)
# create a tile layer sourced from mapbox
L.tileLayer('https://{s}.tiles.mapbox.com/v4/simlmx.3899a192/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2ltbG14IiwiYSI6IjhiOGM5MTQwNzcwYjI2N2I2OWZmZDJmZDEzZmM1MjRmIn0.9gqLDwhf2tDseRNXlFTGRg').addTo(map)
# FIXME put the keys from mapbox in the config and delete those keys...
#

month = (new Date()).getMonth()
$('#month').text(MONTHNAMES[month])

updateCitiesMonth = ->
    for k,c of cities
        c.updateMonth(month)
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

    iconHtml: (month) ->
        high = @getData('avgHigh', month)
        prec = @getData('precipitation', month)
        if prec is null
            prec = @getData('rain', month)
        html = "#{temperatureToHtml(high)}"
        html += "#{precipitationToHtml(prec)}"
        return html

    makeIcon: (month) ->
        L.divIcon({className: 'citydata', html: @iconHtml(month), \
                   iconSize: null})

    updateMonth: (month) ->
        icon = @makeIcon(month)
        @marker.setIcon(icon)

    addToMap: (month, map) ->
        icon = @makeIcon(month)
        # effectively, @marker are the last marker we added to
        # a map...
        @marker = L.marker(@coords, {title:@name, icon:icon})
        @marker.addTo map

    removeFromMap: (map) ->
        map.removeLayer @marker

cities = {}
loadCitiesFromJson = (jsonData) ->
    new_ids = Object.keys(jsonData).sort()
    old_ids = Object.keys(cities).sort()

    # nb_del=nb_new=nb_stay=0
    ni=oi=0
    while true
        old_id = old_ids[oi]
        new_id = new_ids[ni]
        if not old_id? and not new_id?
            break
        # old city needs to be removed
        else if not new_id? or old_id < new_id
            cities[old_id].removeFromMap(map)
            delete cities[old_id]
            # ++nb_del
            ++oi
        # new city needs to be added
        else if not old_id? or new_id < old_id
            infos = jsonData[new_id]
            cities[new_id] = new City(infos.name, infos.coords,
                                      infos.month_stats)
            # ++nb_new
            cities[new_id].addToMap(month, map)
            ++ni
        else
            ++oi
            ++ni
            # ++nb_stay

    # console.log 'new', nb_new
    # console.log 'del', nb_del
    # console.log 'stay', nb_stay

refreshCities = (e) ->
    bounds = map.getBounds()
    coords = 
        n: bounds.getNorth()# - (bounds.getNorth() - bounds.getSouth())*.1
        s: bounds.getSouth()# + (bounds.getNorth() - bounds.getSouth())*.1
        e: bounds.getEast()# - (bounds.getEast() - bounds.getWest())*.1
        w: bounds.getWest()# + (bounds.getEast() - bounds.getWest())*.1

    $.get('data', coords, loadCitiesFromJson, 'json')

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
