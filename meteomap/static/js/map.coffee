# MONTHNAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
    # 'Oct', 'Nov', 'Dec']
MONTHNAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December']

MIN_RED = [255,230,230]
MAX_RED = [204,0,0]
MIN_BLUE = [230,230,255]
MAX_BLUE = [0,0,204]
MIN_GREEN = [230,255,230]
MAX_GREEN = [0,120,0]
BLACK = [0,0,0]
WHITE = [255,255,255]

global =
    stats_info: null
    cities:null
    map:null

# get the Stat infos
loadStatsFromJson = (jsonData) ->
    global.stats = jsonData

$.get('stats', [], loadStatsFromJson, 'json')

# create a map in the "map" div, set the view to a given place and zoom
global.map = L.map('map', {worldCopyJump:true}).setView([45.505, -73.0], 5)
# create a tile layer sourced from mapbox
L.tileLayer('https://{s}.tiles.mapbox.com/v4/simlmx.3899a192/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2ltbG14IiwiYSI6IjhiOGM5MTQwNzcwYjI2N2I2OWZmZDJmZDEzZmM1MjRmIn0.9gqLDwhf2tDseRNXlFTGRg').addTo(global.map)
# FIXME put the keys from mapbox in the config and delete those keys...
#

global.month = (new Date()).getMonth()
$('#month').text(MONTHNAMES[global.month])


updateMeteoTables = (month) ->
    $(".stat-table-data-col").css('border', 'none')
    $(".stat-table-data-col-#{month}").css('border', '1px solid')

updateCitiesMonth = (month) ->
    for k,c of cities
        c.updateMonth(month)
        $('#month').text(MONTHNAMES[month])

prevNextClick = (sign) ->
    global.month += sign
    if global.month < 0
        global.month += 12
    else if global.month > 11
        global.month -= 12
    updateCitiesMonth(global.month)
    updateMeteoTables(global.month)


$('#prev-btn').click ->
    prevNextClick(-1)

$('#next-btn').click ->
    prevNextClick(1)

$('#meteo-tables-clear-all').click ->
    $('#meteo-tables').empty()
    $('#meteo-tables-clear-all').hide()
    $('#meteo-tables-placeholder').show()

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

getColor = (code, value) ->
    if not value?
        return WHITE
    if code == 'avgHigh'
        if value > 10
            rgb = gradient(MIN_RED, MAX_RED, 10, 40, value)
        else
            rgb = gradient(MAX_BLUE, MIN_BLUE, -15, 10, value)
    else if code == 'precipitation'
        rgb = gradient(MIN_GREEN, MAX_GREEN, 0, 250, value)
    else if code == 'monthlySunHours'
        gray = [180,175,100]
        yellow = [255, 250, 100]
        rgb = gradient(gray, yellow, 125, 250, value)
    else
        return WHITE

    return rgb


colorToHtml = (value, color, code) ->
    div = $('<div>').addClass('temperature')
    if not value?
        return div.html()
    div.css('background-color', rgb2hex(color...))
    div.css('color', rgb2hex(BLACK...))
    div.html(value + " " + global.stats[code].unit)
    return div[0].outerHTML


class City
    constructor: (@name, @coords, @meteo) ->

    getData: (code, month) ->
        if code not of @meteo
            return null
        return @meteo[code][month]

    iconHtml: (month) ->
        html = ""
        for code in ['avgHigh', 'precipitation', 'monthlySunHours']
            value = @getData(code, month)
            color = getColor(code, value)
            html += colorToHtml(value, color, code)
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
        @marker.on('click', @addToTable)

    removeFromMap: (map) ->
        map.removeLayer @marker

    addToTable: =>
        container = $('<div class="meteo-tables-div">').appendTo('#meteo-tables')
            .hover((-> $(this).find('.btn').show()),
                   (-> $(this).find('.btn').hide()))
        btn = $('<button type="button" class="btn btn-default btn-xs" style="display:none; float:right">')
            .append('<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>')
            .click(-> $(this).parent().parent().remove())
 
        header = $('<div class="meteo-table-header">').append("<strong>#{@name}</strong>").append(btn).appendTo(container)
        table = $('<table class="table table-condensed meteo-table">')
                .appendTo(container)
        for code, data of @meteo
            stat_infos = global.stats[code]
            tr = $('<tr>').appendTo(table)
            td = $('<th>').html("#{stat_infos['name']} (#{stat_infos['unit']})")
                          .appendTo(tr)      
            for month in [0...12]
                value = data[month]
                $('<td>').html(value).css('background-color',
                              rgb2hex(getColor(code,value)...))
                         .addClass('stat-table-data-col')
                         .addClass("stat-table-data-col-#{month}")
                         .appendTo(tr)

        $('#meteo-tables-clear-all').show()
        updateMeteoTables(global.month)
        $('#meteo-tables-placeholder').hide()

        # for code, data of @meteo
        #     table.append($('<tr>'))
        


cities = {}
loadCitiesFromJson = (jsonData) ->
    city_data = jsonData
    new_ids = Object.keys(city_data).sort()
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
            cities[old_id].removeFromMap(global.map)
            delete cities[old_id]
            # ++nb_del
            ++oi
        # new city needs to be added
        else if not old_id? or new_id < old_id
            infos = city_data[new_id]
            cities[new_id] = new City(infos.name, infos.coords,
                                      infos.month_stats)
            # ++nb_new
            cities[new_id].addToMap(global.month, global.map)
            ++ni
        else
            ++oi
            ++ni
            # ++nb_stay

    # console.log 'new', nb_new
    # console.log 'del', nb_del
    # console.log 'stay', nb_stay
    


refreshCities = (e) ->
    bounds = global.map.getBounds()
    coords = 
        n: bounds.getNorth()# - (bounds.getNorth() - bounds.getSouth())*.1
        s: bounds.getSouth()# + (bounds.getNorth() - bounds.getSouth())*.1
        e: bounds.getEast()# - (bounds.getEast() - bounds.getWest())*.1
        w: bounds.getWest()# + (bounds.getEast() - bounds.getWest())*.1

    $.get('data', coords, loadCitiesFromJson, 'json')
    

global.map.on('moveend', refreshCities)
refreshCities({})
