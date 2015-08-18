// Generated by CoffeeScript 1.3.3
(function() {
  var BLACK, City, MAX_BLUE, MAX_GREEN, MAX_RED, MIN_BLUE, MIN_GREEN, MIN_RED, MONTHNAMES, WHITE, cities, colorToHtml, getColor, global, gradient, loadCitiesFromJson, loadStatsFromJson, prevNextClick, refreshCities, rgb2hex, updateCitiesMonth, updateMeteoTables,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  MONTHNAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  MIN_RED = [255, 230, 230];

  MAX_RED = [204, 0, 0];

  MIN_BLUE = [230, 230, 255];

  MAX_BLUE = [0, 0, 204];

  MIN_GREEN = [230, 255, 230];

  MAX_GREEN = [0, 120, 0];

  BLACK = [0, 0, 0];

  WHITE = [255, 255, 255];

  global = {
    stats_info: null,
    cities: null,
    map: null
  };

  loadStatsFromJson = function(jsonData) {
    return global.stats = jsonData;
  };

  $.get('stats', [], loadStatsFromJson, 'json');

  global.map = L.map('map', {
    worldCopyJump: true
  }).setView([45.505, -73.0], 5);

  L.tileLayer('https://{s}.tiles.mapbox.com/v4/simlmx.3899a192/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2ltbG14IiwiYSI6IjhiOGM5MTQwNzcwYjI2N2I2OWZmZDJmZDEzZmM1MjRmIn0.9gqLDwhf2tDseRNXlFTGRg').addTo(global.map);

  global.month = (new Date()).getMonth();

  $('#month').text(MONTHNAMES[global.month]);

  updateMeteoTables = function(month) {
    $(".stat-table-data-col").css('border', 'none');
    return $(".stat-table-data-col-" + month).css('border', '1px solid');
  };

  updateCitiesMonth = function(month) {
    var c, k, _results;
    _results = [];
    for (k in cities) {
      c = cities[k];
      c.updateMonth(month);
      _results.push($('#month').text(MONTHNAMES[month]));
    }
    return _results;
  };

  prevNextClick = function(sign) {
    global.month += sign;
    if (global.month < 0) {
      global.month += 12;
    } else if (global.month > 11) {
      global.month -= 12;
    }
    updateCitiesMonth(global.month);
    return updateMeteoTables(global.month);
  };

  $('#prev-btn').click(function() {
    return prevNextClick(-1);
  });

  $('#next-btn').click(function() {
    return prevNextClick(1);
  });

  $('#meteo-tables-clear-all').click(function() {
    $('#meteo-tables').empty();
    $('#meteo-tables-clear-all').hide();
    return $('#meteo-tables-placeholder').show();
  });

  rgb2hex = function(red, green, blue) {
    var rgb;
    rgb = blue | (green << 8) | (red << 16);
    return '#' + (0x1000000 + rgb).toString(16).slice(1);
  };

  gradient = function(rgb_min, rgb_max, min, max, val) {
    var delta, i, rgb;
    if (val <= min) {
      return rgb_min;
    } else if (val >= max) {
      return rgb_max;
    }
    delta = (function() {
      var _i, _len, _ref, _results;
      _ref = [0, 1, 2];
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        i = _ref[_i];
        _results.push(rgb_max[i] - rgb_min[i]);
      }
      return _results;
    })();
    rgb = (function() {
      var _i, _len, _ref, _results;
      _ref = [0, 1, 2];
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        i = _ref[_i];
        _results.push(rgb_min[i] + delta[i] * (val - min) / (max - min));
      }
      return _results;
    })();
    return rgb;
  };

  getColor = function(code, value) {
    var gray, rgb, yellow;
    if (!(value != null)) {
      return WHITE;
    }
    if (code === 'avgHigh') {
      if (value > 10) {
        rgb = gradient(MIN_RED, MAX_RED, 10, 40, value);
      } else {
        rgb = gradient(MAX_BLUE, MIN_BLUE, -15, 10, value);
      }
    } else if (code === 'precipitation') {
      rgb = gradient(MIN_GREEN, MAX_GREEN, 0, 250, value);
    } else if (code === 'monthlySunHours') {
      gray = [180, 175, 100];
      yellow = [255, 250, 100];
      rgb = gradient(gray, yellow, 125, 250, value);
    } else {
      return WHITE;
    }
    return rgb;
  };

  colorToHtml = function(value, color, code) {
    var div;
    div = $('<div>').addClass('temperature');
    if (!(value != null)) {
      return div.html();
    }
    div.css('background-color', rgb2hex.apply(null, color));
    div.css('color', rgb2hex.apply(null, BLACK));
    div.html(value + " " + global.stats[code].unit);
    return div[0].outerHTML;
  };

  City = (function() {

    function City(name, coords, meteo) {
      this.name = name;
      this.coords = coords;
      this.meteo = meteo;
      this.addToTable = __bind(this.addToTable, this);

    }

    City.prototype.getData = function(code, month) {
      if (!(code in this.meteo)) {
        return null;
      }
      return this.meteo[code][month];
    };

    City.prototype.iconHtml = function(month) {
      var code, color, html, value, _i, _len, _ref;
      html = "";
      _ref = ['avgHigh', 'precipitation', 'monthlySunHours'];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        code = _ref[_i];
        value = this.getData(code, month);
        color = getColor(code, value);
        html += colorToHtml(value, color, code);
      }
      return html;
    };

    City.prototype.makeIcon = function(month) {
      return L.divIcon({
        className: 'citydata',
        html: this.iconHtml(month),
        iconSize: null
      });
    };

    City.prototype.updateMonth = function(month) {
      var icon;
      icon = this.makeIcon(month);
      return this.marker.setIcon(icon);
    };

    City.prototype.addToMap = function(month, map) {
      var icon;
      icon = this.makeIcon(month);
      this.marker = L.marker(this.coords, {
        title: this.name,
        icon: icon
      });
      this.marker.addTo(map);
      return this.marker.on('click', this.addToTable);
    };

    City.prototype.removeFromMap = function(map) {
      return map.removeLayer(this.marker);
    };

    City.prototype.addToTable = function() {
      var btn, code, container, data, header, month, stat_infos, table, td, tr, value, _i, _ref;
      container = $('<div class="meteo-tables-div">').appendTo('#meteo-tables').hover((function() {
        return $(this).find('.btn').show();
      }), (function() {
        return $(this).find('.btn').hide();
      }));
      btn = $('<button type="button" class="btn btn-default btn-xs" style="display:none; float:right">').append('<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>').click(function() {
        return $(this).parent().parent().remove();
      });
      header = $('<div class="meteo-table-header">').append("<strong>" + this.name + "</strong>").append(btn).appendTo(container);
      table = $('<table class="table table-condensed meteo-table">').appendTo(container);
      _ref = this.meteo;
      for (code in _ref) {
        data = _ref[code];
        stat_infos = global.stats[code];
        tr = $('<tr>').appendTo(table);
        td = $('<th>').html("" + stat_infos['name'] + " (" + stat_infos['unit'] + ")").appendTo(tr);
        for (month = _i = 0; _i < 12; month = ++_i) {
          value = data[month];
          $('<td>').html(value).css('background-color', rgb2hex.apply(null, getColor(code, value))).addClass('stat-table-data-col').addClass("stat-table-data-col-" + month).appendTo(tr);
        }
      }
      $('#meteo-tables-clear-all').show();
      updateMeteoTables(global.month);
      return $('#meteo-tables-placeholder').hide();
    };

    return City;

  })();

  cities = {};

  loadCitiesFromJson = function(jsonData) {
    var city_data, infos, new_id, new_ids, ni, oi, old_id, old_ids, _results;
    city_data = jsonData;
    new_ids = Object.keys(city_data).sort();
    old_ids = Object.keys(cities).sort();
    ni = oi = 0;
    _results = [];
    while (true) {
      old_id = old_ids[oi];
      new_id = new_ids[ni];
      if (!(old_id != null) && !(new_id != null)) {
        break;
      } else if (!(new_id != null) || old_id < new_id) {
        cities[old_id].removeFromMap(global.map);
        delete cities[old_id];
        _results.push(++oi);
      } else if (!(old_id != null) || new_id < old_id) {
        infos = city_data[new_id];
        cities[new_id] = new City(infos.name, infos.coords, infos.month_stats);
        cities[new_id].addToMap(global.month, global.map);
        _results.push(++ni);
      } else {
        ++oi;
        _results.push(++ni);
      }
    }
    return _results;
  };

  refreshCities = function(e) {
    var bounds, coords;
    bounds = global.map.getBounds();
    coords = {
      n: bounds.getNorth(),
      s: bounds.getSouth(),
      e: bounds.getEast(),
      w: bounds.getWest()
    };
    return $.get('data', coords, loadCitiesFromJson, 'json');
  };

  global.map.on('moveend', refreshCities);

  refreshCities({});

}).call(this);
