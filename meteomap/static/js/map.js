// Generated by CoffeeScript 1.3.3
(function() {
  var BLACK, CODES, City, MAX_BLUE, MAX_GREEN, MAX_RED, MEDIUM_GREEN, MIN_BLUE, MIN_GREEN, MIN_RED, MONTHNAMES, NB_CITIES_PER_100PX_SQ, WHITE, colorToHtml, getColor, global, gradient, loadCitiesFromJson, loadStatsFromJson, prevNextClick, refreshCities, rgb2hex, updateCitiesMonth, updateMeteoTables, updateMeteoTablesWidth,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  MONTHNAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  CODES = ['avgHigh', 'avgLow', 'precipitation', 'precipitationDays', 'monthlySunHours'];

  NB_CITIES_PER_100PX_SQ = 1;

  MIN_RED = [255, 230, 230];

  MAX_RED = [204, 0, 0];

  MIN_BLUE = [230, 230, 255];

  MAX_BLUE = [0, 0, 204];

  MIN_GREEN = [230, 255, 230];

  MEDIUM_GREEN = [20, 150, 20];

  MAX_GREEN = [0, 120, 0];

  BLACK = [0, 0, 0];

  WHITE = [255, 255, 255];

  global = {
    stats_info: null,
    cities: {},
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

  updateMeteoTablesWidth = function() {
    var c, k, n, _ref;
    n = $('.meteo-table').length;
    if (n > 0) {
      $('#meteo-tables-placeholder').hide();
      $('.right').addClass('right-exp-width');
      $('.right').removeClass('right-width');
      $('.left').addClass('left-exp-width');
      return $('.left').removeClass('left-width');
    } else {
      $('#meteo-tables-placeholder').show();
      $('#meteo-tables-clear-all').hide();
      _ref = global.cities;
      for (k in _ref) {
        c = _ref[k];
        c.inTable = false;
      }
      $('.right').removeClass('right-exp-width');
      $('.right').addClass('right-width');
      $('.left').removeClass('left-exp-width');
      return $('.left').addClass('left-width');
    }
  };

  updateCitiesMonth = function(month) {
    var c, k, _ref, _results;
    _ref = global.cities;
    _results = [];
    for (k in _ref) {
      c = _ref[k];
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
    return updateMeteoTablesWidth();
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
    if (code === 'avgHigh' || code === 'avgLow') {
      if (value > 10) {
        rgb = gradient(MIN_RED, MAX_RED, 10, 40, value);
      } else {
        rgb = gradient(MAX_BLUE, MIN_BLUE, -15, 10, value);
      }
    } else if (code === 'precipitation') {
      if (value < 400) {
        rgb = gradient(MIN_GREEN, MEDIUM_GREEN, 0, 400, value);
      } else {
        rgb = gradient(MEDIUM_GREEN, MAX_GREEN, 400, 800, value);
      }
    } else if (code === 'precipitationDays') {
      rgb = gradient(MIN_GREEN, MAX_GREEN, 0, 30, value);
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
    var li;
    li = $('<li>').addClass('temperature');
    li.css('background-color', rgb2hex.apply(null, color));
    li.css('color', rgb2hex.apply(null, BLACK));
    li.html(value);
    return li;
  };

  City = (function() {

    function City(name, country, coords, meteo) {
      this.name = name;
      this.country = country;
      this.coords = coords;
      this.meteo = meteo;
      this.addToTable = __bind(this.addToTable, this);

      this.iconHtml = __bind(this.iconHtml, this);

      this.inTable = false;
    }

    City.prototype.getData = function(code, month) {
      if (!(code in this.meteo)) {
        return null;
      }
      return this.meteo[code][month];
    };

    City.prototype.iconHtml = function(month) {
      var code, color, div, ul, value, _i, _len;
      div = $('<div>');
      ul = $('<ul>').appendTo(div);
      for (_i = 0, _len = CODES.length; _i < _len; _i++) {
        code = CODES[_i];
        value = this.getData(code, month);
        if (!(value != null)) {
          continue;
        }
        value = this.formatValue(value);
        color = getColor(code, value);
        ul.append(colorToHtml(value, color, code));
      }
      return div[0].outerHTML;
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
      var btn, code, container, data, header, month, stat_infos, stat_name, table, tr, value, _i, _j, _len,
        _this = this;
      if (this.inTable) {
        return;
      }
      container = $('<div class="meteo-table-container">').appendTo('#meteo-tables').hover((function() {
        return $(this).find('.btn').show();
      }), (function() {
        return $(this).find('.btn').hide();
      }));
      btn = $('<button type="button" class="btn btn-danger btn-xs' + ' meteo-table-close" style="display:none">').append('<span class="glyphicon glyphicon-remove"' + ' aria-hidden="true"></span>').click(function() {
        $(this).parent().parent().remove();
        return updateMeteoTablesWidth();
      }).click(function() {
        return _this.inTable = false;
      });
      header = $('<div class="meteo-table-header">').append("<strong>" + this.name + ", " + this.country + "</strong>").append(btn).appendTo(container);
      table = $('<table class="meteo-table">').appendTo(container);
      for (_i = 0, _len = CODES.length; _i < _len; _i++) {
        code = CODES[_i];
        if (!(code in this.meteo)) {
          continue;
        }
        data = this.meteo[code];
        stat_infos = global.stats[code];
        stat_name = stat_infos['name'];
        if (stat_name === 'Precipitation Days') {
          stat_name = 'Precip. Days';
        }
        tr = $('<tr>').appendTo(table);
        $('<th>').html("" + stat_name + " (" + stat_infos['unit'] + ")").appendTo(tr);
        for (month = _j = 0; _j < 12; month = ++_j) {
          value = data[month];
          if (value >= 100) {
            value = this.formatValue(value);
          }
          $('<td>').html(value).css('background-color', rgb2hex.apply(null, getColor(code, value))).addClass('stat-table-data-col').addClass("stat-table-data-col-" + month).appendTo(tr);
        }
      }
      $('#meteo-tables-clear-all').show();
      updateMeteoTables(global.month);
      updateMeteoTablesWidth();
      return this.inTable = true;
    };

    City.prototype.formatValue = function(val) {
      if (val >= 100) {
        return val.toPrecision(3);
      }
      return val;
    };

    return City;

  })();

  loadCitiesFromJson = function(jsonData) {
    var city_data, infos, new_id, new_ids, ni, oi, old_id, old_ids, _results;
    city_data = jsonData;
    new_ids = Object.keys(city_data).sort();
    old_ids = Object.keys(global.cities).sort();
    ni = oi = 0;
    _results = [];
    while (true) {
      old_id = old_ids[oi];
      new_id = new_ids[ni];
      if (!(old_id != null) && !(new_id != null)) {
        break;
      } else if (!(new_id != null) || old_id < new_id) {
        global.cities[old_id].removeFromMap(global.map);
        delete global.cities[old_id];
        _results.push(++oi);
      } else if (!(old_id != null) || new_id < old_id) {
        infos = city_data[new_id];
        global.cities[new_id] = new City(infos.name, infos.country, infos.coords, infos.month_stats);
        global.cities[new_id].addToMap(global.month, global.map);
        _results.push(++ni);
      } else {
        ++oi;
        _results.push(++ni);
      }
    }
    return _results;
  };

  refreshCities = function(e) {
    var bounds, coords, map, nb;
    bounds = global.map.getBounds();
    coords = {
      n: bounds.getNorth(),
      s: bounds.getSouth(),
      e: bounds.getEast(),
      w: bounds.getWest()
    };
    map = $('#map');
    nb = map.width() * map.height() / 100 / 100 * NB_CITIES_PER_100PX_SQ;
    nb = nb.toFixed();
    coords['nb'] = nb;
    return $.get('data', coords, loadCitiesFromJson, 'json');
  };

  global.map.on('moveend', refreshCities);

  refreshCities({});

}).call(this);
