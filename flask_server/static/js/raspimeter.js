$(function () {
	
	$("img.lazy").lazyload({event: 'scroll load-images'});
	
	var filters = {};
	
	
	var checkboxes = $('.all-products input[type=checkbox]');

	checkboxes.click(function () {

		var that = $(this),
			specName = that.attr('name');

		// When a checkbox is checked we need to write that in the filters object;
		if(that.is(":checked")) {

			// If the filter for this specification isn't created yet - do it.
			if(!(filters[specName] && filters[specName].length)){
				filters[specName] = [];
			}

			//	Push values into the chosen filter array
			filters[specName].push(that.val());

		}

		// When a checkbox is unchecked we need to remove its value from the filters object.
		if(!that.is(":checked")) {

			if(filters[specName] && filters[specName].length && (filters[specName].indexOf(that.val()) != -1)){

				// Find the checkbox value in the corresponding array inside the filters object.
				var index = filters[specName].indexOf(that.val());

				// Remove it.
				filters[specName].splice(index, 1);

				// If it was the last remaining value for this specification,
				// delete the whole array.
				if(!filters[specName].length){
					delete filters[specName];
				}

			}
		}
		
		// Change the url hash;
		createQueryHash(filters);
		
	});

	// When the "Clear all filters" button is pressed change the hash to '#' (go to the home page)
	$('.clear-filters-button').click(function (e) {
		e.preventDefault();
		window.location.hash = '#';
	});
	
	// Try to recognize all 
	$('.recognize-all-button').click(function (e) {
		
		e.preventDefault();
		
		var meterId = $('.products-list').attr('id');
		var page = $(this).attr('id');
		
		console.log(page);
		
		$.getJSON( "recognize_all?meter_id=" + meterId + "&page=" + page, function(data) {
			
			// TODO loader.gif
			console.log(data);
			window.location.hash = '#';
			
		});
	});
	
	$(window).on('hashchange', function(){
		render(decodeURI(window.location.hash));
	});
	
	$('#delete_button').click(function() {
		deleteMeterImageAndMeterValue();
		// don't reload page
		return false;
	});
	
	$('#save_button').click(function() {
		trainKNNAndStoreIntoDB();
		// don't reload page
		return false;
	});
	
	$('.all-products .products-list').find('li').on('click', function (e) {
		
		e.preventDefault();

		var imageId = $(this).data('index');

		//window.location.hash = '#' + imageId;
		
		// fetch single image data
		$.getJSON( "get_image?id=" + imageId, function(image) {
			
			renderSingleMeterValue(image);
			
		});
	})
			
	
	function renderSingleMeterValue(image){
		
		var page = $('.single-product');
		var container = $('.preview-large');
		
		$.getJSON( "get_digits?image_name=" + image.name, function(digits) {
			
			$.getJSON( "get_meter?id=" + image.name.split("_")[2], function(meter) {
		
				renderMeterDigits(meter, digits, image.flag);
		
			});	
		});
		
		console.log(moment.utc(image.time, "YYYY-MM-DD H:mm:ss").format('lll'));
		
		container.find('h3').text(image.time);
		container.find('img').attr('src', 'static/images/' + image.name);
		container.find('img').attr('image-name', image.name);
		
		$('#save_button').addClass('disabled-button');
		$('#delete_button').addClass('disabled-button');
		$('#use_for_knn').prop('disabled', true);
		$('#use_for_knn').prop('checked', false);
		$(".preview-large .loader").fadeOut("slow");
		// Show the page.
		page.addClass('visible');

	}
	

	function renderMeterDigits(meter, digits, flag) {
		
		var deleteButton = $('#delete_button');
		
		deleteButton.removeClass('disabled-button');
		
		var list = $('.single-product .preview-large .meter-value-rectangle .digits-list');
		
		list.empty();
		
		digits.forEach(function(digit, index) {
			
			var listItem = '<li><div id="' + index + '" class="digit-cell">' + 
			'<input id="' + index + '" class="digit-input" type="number" maxlength="1" size="1" value="' + digit + '">' 
			+ '</div></li>';
			
			list.append(listItem);
			
		});
		
		// not recognized digits and decimal places
		var digitsNumber = parseInt(meter.meter_settings.digits_number);
		var decimalPlaces = parseInt(meter.meter_settings.decimal_places);
		
		$.each(digits, function(index, value) {

			if (value == -1) {
				$('#' + index + '.digit-input').addClass('not-recognized-digit');
				$('#' + index + '.digit-input').val(0);
			}

			if (index >= (digitsNumber - decimalPlaces)) {
				$('div.digit-cell#' + index).addClass('decimal');
			}
		});
		
		
		if (flag != 0) {
			enableSaveButton();
		}
		
		var old_value = 0;

		$('.digit-input').focus(function(){
			
			old_value = $(this).val();            
			$(this).select();
			
		});
		
		
		$('.digit-input').blur(function(){
			
			if (old_value != $(this).val()) {
				
				// enable Save button and checkbox
				enableSaveButton();
				
				$(this).addClass("changed");
				$(this).removeClass('not-recognized-digit');
			
			}
		});
	}
	
	function enableSaveButton() {
		$('#save_button').removeClass('disabled-button');
		$('#use_for_knn').prop('disabled', false);
		$('#use_for_knn').prop('checked', true);
	}
	
	function trainKNNAndStoreIntoDB(){
		
		var container = $('.preview-large');
		var imageName = container.find('img').attr('image-name');

		var list = $('.single-product .preview-large .meter-value-rectangle .digits-list .digit-input');

		var responses = []
		
		list.each(function(index) {
			
			if ($(this).hasClass("changed")) {

				responses.push(parseInt($(this).val()));
			
			} else {
				
				responses.push(-1);
			
			}
		});
		
		console.log(responses);
		
		var train = $('#use_for_knn').prop('checked');
		
		$.getJSON( "/save_digits?image_name=" + imageName + "&train=" + train + "&responses=" +  JSON.stringify(responses), function(resp) {
			
			console.log(resp);
			$('#save_button').addClass('disabled-button');
//    		updatePreview();

		});		
	}
	
	
	function deleteMeterImageAndMeterValue() {
		
		// TODO confirm dialog
		var container = $('.preview-large');
		var time = container.find('h3').text();
		var imageName = container.find('img').attr('image-name');
		
		var perm_delete = $('#permanently_delete').prop('checked');

		$.getJSON( "/delete_meter_value?image_name=" + imageName + "&perm=" + perm_delete, function(resp) {
			
			console.log(resp);
			$("li[id*='" + time + "']").remove();
    		closePreview();

		});	
	}
	

	var singleProductPage = $('.single-product');

	singleProductPage.on('click', function (e) {

		if (singleProductPage.hasClass('visible')) {

			var clicked = $(e.target);

			// If the close button or the background are clicked go to the previous page.
			if (clicked.hasClass('close') || clicked.hasClass('overlay')) {
				closePreview();
			}
		}
	});
	
	
	function closePreview() {
//		createQueryHash(filters);
		var page = $('.single-product');
		// TODO clear content
		page.removeClass('visible');
	}
	
   
	// Navigation
	function render(url) {

		// Get the keyword from the url.
		var temp = url.split('/')[0];

		// Hide whatever page is currently shown.
		$('.main-content .page').removeClass('visible');


		var	map = {

			'': function() {
				
				filters = {};
				checkboxes.prop('checked',false);
				filterImages(filters);

			},

			'#': function() {

				filters = {};
				checkboxes.prop('checked', false);
				filterImages(filters);
				
			},

			// Page with filtered products
			'#filter': function() {

				url = url.split('#filter/')[1].trim();

				try {
					filters = JSON.parse(url);
				}
				catch(err) {
					window.location.hash = '#';
					return;
				}
				
				filterImages(filters);
				
			}
		};

		if(map[temp]){
			map[temp]();
		}
	}

	
	function filterImages(filters) {
		
//		console.log("filter images: ");
//		console.log(filters);
		
		if (typeof filters['flag'] === "undefined") {
			
			$('.all-products .products-list > li').show();
			
		} else {
		
			$('.all-products .products-list > li').hide();
			
			$.each(filters['flag'], function(index, value) {
				
//				console.log($("li[flag='" + value + "']"));
				
				$("li[flag='" + value + "']").show();
				
				$(window).resize();//
				$("img.lazy").trigger("load-images");
				
//				When you initialize lazyload you can tell it which event(s) to trigger on (by default it is set to 'scroll'). I suggest adding a custom event to that list and triggering it whenever it makes sense for you:
//
//					$('.lazy').lazyload({
//					    event: 'scroll whenever-i-want'
//					});
//
//					// whenever you want to trigger your event (after ajax load, on dom ready, etc...)
//					$(document).trigger('whenever-i-want');
//					This leaves the default scroll functionality in but also allows you to trigger the lazy loading on demand.
	
			});
		}
	}


	// Shows the error page.
	function renderErrorPage(){
		var page = $('.error');
		page.addClass('visible');
	}

	// Get the filters object, turn it into a string and write it into the hash.
	function createQueryHash(filters){

		// Here we check if filters isn't empty.
		if(!$.isEmptyObject(filters)){
			// Stringify the object via JSON.stringify and write it after the '#filter' keyword.
			window.location.hash = '#filter/' + JSON.stringify(filters);
		}
		else{
			// If it's empty change the hash to '#' (the homepage).
			window.location.hash = '#';
		}
	}
	
	
	
	/*************** CHARTS ********************************/
		
	// Initial variables for chart-container
	// date for charts for MySQL: "YYYY-MM-DD HH:MM:SS"
	var period = 'd';
		
	var startMoment = moment().subtract(1, 'months').startOf('day');
	var endMoment = moment();
	var DATE_FORMAT = "YYYY-MM-DD HH:mm:ss";
		
	console.log(decodeURI(window.location.pathname));

	// called if home page loaded
	if (decodeURI(window.location.pathname) == "/") {
		loadChartDataAndRenderAllCharts(period, startMoment, endMoment);
	}
		
		
	function loadChartDataAndRenderAllCharts(period, startMoment, endMoment) {
			
		$.getJSON( "get_meters", function(meters) {
				
			meters.forEach(function (meter) {
					
				$.getJSON( "get_consumption?" 
						+ "meter_id=" + meter['_id']['$oid'] //meter['id'] for mysql
						+ "&period=" + period 
						+ "&start_date=" + moment(startMoment).format(DATE_FORMAT)
						+ "&end_date=" + moment(endMoment).format(DATE_FORMAT), function(consumption) {
							
							$.getJSON( "get_weather?" 
									+ "meter_id=" + meter['_id']['$oid'] //meter['id'] for mysql
									+ "&period=" + period
									+ "&start_date=" + moment(startMoment).format(DATE_FORMAT)
									+ "&end_date=" + moment(endMoment).format(DATE_FORMAT), function(weather) {
									
									renderChartContainer(meter, consumption, weather);

							});
				});
			});
		});
	}
		

	function redrawChart(meter) {
			
		meterId = meter['_id']['$oid']; //meter['id'] for mysql

		var ranges = getRangesAsMoments(meterId);
		var period = getPeriod(meterId);
			
		$.getJSON( "get_consumption?" 
				+ "meter_id=" + meterId
				+ "&period=" + period 
				+ "&start_date=" + moment(ranges[0]).format(DATE_FORMAT)
				+ "&end_date=" + moment(ranges[1]).format(DATE_FORMAT), function(consumption) {
					
					$.getJSON( "get_weather?" 
							+ "meter_id=" + meter['_id']['$oid'] //meter['id'] for mysql
							+ "&period=" + period
							+ "&start_date=" + moment(ranges[0]).format(DATE_FORMAT)
							+ "&end_date=" + moment(ranges[1]).format(DATE_FORMAT), function(weather) {
							
//								console.log("Load...");
//								console.log("Period: " + period);
//								console.log("Start moment " + moment(startMoment).format(DATE_FORMAT));
//								console.log("End moment " + moment(endMoment).format(DATE_FORMAT));
//								console.log($('#chart_' + meterId));
//								console.log("Reload: meterID" + meterId);
//								console.log(data[0][1]['consumption'])
									
								var chart = $('#chart_' + meterId).highcharts();
								var costsAndConsumption = calculateCostsAndConvertedConsumption(meter, consumption);
								
								weather.forEach(function (item) {
									item[1] = parseFloat((item[1]).toFixed(1));
								});
								
								chart.series[0].setData(costsAndConsumption['units'], true);
								chart.series[1].setData(costsAndConsumption['costs'], true);
								chart.series[2].setData(costsAndConsumption['convUnits'], true);
								chart.series[3].setData(weather, true);

					});
		

				
		});
	}
		
	function renderChartContainer(meter, consumption, weather) {
			
//		console.log("render chart with consumpt: " + consumption);
//		console.log("render chart with meter: " + meter);
			
		var meter_id = meter['_id']['$oid']; //meter['id'] for mysql
		var list = $('.charts-list');
				
		renderChart(meter, consumption, weather);
		addPeriodSelecterHandling(meter);
		renderDateRangePicker(meter);
		addRefreshButtonHandler(meter);
				
	}
	
	
	function addPeriodSelecterHandling(meter) {

		$("#periodSelector_" + meter['_id']['$oid']).selectable({
				
			stop: function() {
				
				var result = $("#select-result").empty();
			        
				$(".ui-selected", this).each(function() {
			    
					redrawChart(meter);
		        
				});
		    }
		});
	}
		
	function renderDateRangePicker(meter) {

		var datePicker = $("#date-range-picker_" + meter['_id']['$oid']);
		var startDate = startMoment.toDate();
		var endDate = endMoment.toDate();
			
//	    console.log("renderDatePicker");

		datePicker.daterangepicker({
		     datepickerOptions : {
		         numberOfMonths : 2,
		         //minDate: 0,
		         maxDate: null,
		     }
		 });
			
		datePicker.daterangepicker("setRange", {start: startDate, end: endDate});
			
		datePicker.on('change', function(event) { 
				
//			console.log("DatePicker redraw");
				redrawChart(meter);
				
		});
	}
	
	// TODO add autoupdate chkbx
	// TODO add refresh btn
	function addRefreshButtonHandler(meter) {
		
		var refreshButton = $("#refresh_button_" + meter['_id']['$oid']);
		
		refreshButton.click(function( event ) {
	        
			event.preventDefault();
	        redrawChart(meter);
	      
		});
	}
	
		
	
	function getRangesAsMoments(meterId) {
			
		var range = $("#date-range-picker_" + meterId).daterangepicker("getRange");
		var startMoment = moment(range.start);
		var endMoment = moment(range.end).add(1, 'days').subtract(1, 'seconds');
			
		return [startMoment, endMoment];
//		ranges.push();
			
	}
		
	function getPeriod(meterId) {
		return $("#periodSelector_" + meterId + " > .ui-selected").attr("id");
	}
		

	function renderChart(meter, consumption, weather) {

		var id = meter['_id']['$oid'];
			
		var costsAndConsumption = calculateCostsAndConvertedConsumption(meter, consumption);

		weather.forEach(function (item) {
			item[1] = parseFloat((item[1]).toFixed(1));
		});
		
		Highcharts.setOptions({
	        global: {
	            useUTC: false
	        }
	    });
			
		$('#chart_' + id).highcharts({
				
	        chart: {
	            type: 'spline',
	            zoomType: 'xy',
	        },
	        rangeSelector: {
	               selected: 1,
	               inputDateFormat: '%Y-%m-%d'
	        },
	        title: {
	            text: meter['name']
	        },
	        subtitle: {
	            text: ''
	        },
	        xAxis: {
	            type: 'datetime',
	            dateTimeLabelFormats: {
	            	millisecond:"%a, %b %e, %H:%M",
	            	second:"%a, %b %e, %H:%M",
	                minute:"%a, %b %e, %H:%M",
	                hour:"%a, %b %e, %H:%M",
	                day:"%a, %b %e, %Y",
	                week:"Week from %a, %b %e, %Y",
	                month:"%B %Y",
	                year:"%Y",
	            },
	            title: {
	                text: 'Date'
	            }
	        },
	        
	        yAxis: [{
	            title: {
	                text: 'Consumption',
	                style: {
	                    color: Highcharts.getOptions().colors[0]
	                }
	            },
	        },
	        { 
	            labels: {
	                format: '{value} °C',
	                style: {
	                    color: Highcharts.getOptions().colors[1]
	                }
	            },
	        	opposite: true,
	            title: {
	                text: 'Temperature',
	                style: {
	                    color: Highcharts.getOptions().colors[1]
	                }
	            }
	        }],
	        
	        tooltip: {
	            headerFormat: '<b>{point.x:%a, %e. %b %Y, %H:%M}</b><br>',
	            pointFormat: '{point.y} {series.name}'
	        },
	        plotOptions: {
	            spline: {
	                marker: {
	                    enabled: true
	                }
	            }
	        },
	        series: [{
	            name: meter.meter_settings['value_units'],
	            data: costsAndConsumption['units'],
	            type: 'column',
	        },
	        {
		        name: '€',
		        data: costsAndConsumption['costs'],
		        type: 'column',		      
	        },
		    {
			        
		        type: 'column',
		        name: meter.meter_settings['converted_value_units'],
		        data: costsAndConsumption['convUnits'],
			      
		      },  
	        {
			            
		        type: 'spline',
		        name: '°C',
		        data: weather,
		        yAxis: 1,
			        
		        marker: {
		         	lineWidth: 2,
		         	lineColor: Highcharts.getOptions().colors[3],
		         	fillColor: 'white'
		        }
			        
				}
	        ]
		});
			
		$("#chart_li_" + id + ".invisible").removeClass("invisible");
			
	}
		
	function calculateCostsAndConvertedConsumption(meter, consumption) {
//		kWh = m³ x Brennwert x Zustandszahl
//		Ihren Gasverbrauch finden Sie auf Ihrer Gasrechnung
//		9,833 Der Brennwert ist ein Maß für die im Gas enthaltene Wärmeenergie und 
//		abhängig von der Qualität des Gases – den Wert erhalten Sie von Ihrem Versorger oder Netzbetreiber
//		0,9627 Die Zustandszahl beschreibt das Verhältnis des Gasvolumens vom Normzustand 
//		zum Betriebszustand – den Wert erhalten Sie von Ihrem Versorger oder Netzbetreiber
		
		price = meter.meter_settings['unit_price'];
		calorificValue = meter.meter_settings['calorific_value'];
		conditionNumber = meter.meter_settings['condition_number'];
		decimalPlaces = meter.meter_settings['decimal_places'];
		
		var costsAndConsumption = new Object();
		
		cons  = [];
		convCons = [];
		costs = [];
		
		var factor = 1.0/(Math.pow(10, decimalPlaces)); 
			
		consumption.forEach(function (item) {
				
			
			var decimalValue = parseFloat((item[1] * factor).toFixed(decimalPlaces));
			var convertedValue = parseFloat((decimalValue * calorificValue * conditionNumber).toFixed(4));
			var cost = parseFloat((convertedValue * price).toFixed(2));
			
			cons.push([item[0], decimalValue]);
			convCons.push([item[0], convertedValue]);
			costs.push([item[0], cost]);
				
		});
		
		costsAndConsumption.units = cons;
		costsAndConsumption.convUnits = convCons;
		costsAndConsumption.costs = costs;
		
		return costsAndConsumption;
			
	}
	
	

	
	/***  METER SETTINGS ***/
	$('[id*=settings-button]').click(function() {	
		runEffect($(this).attr('id'));
	});	
	
	function runEffect(buttonId) {
	
		console.log(buttonId);
		var meterSettingsContainer = $('#' + buttonId.replace('button', 'container'));
		meterSettingsContainer.toggle('blind', {}, 500);
		
//		if (meterSettingsContainer.hasClass('invisible-settings-container')) {
//		
//			meterSettingsContainer.show('blind', {}, 500, meterSettingsCallback);
//		
//		} else {
//			
//			meterSettingsContainer.addClass('invisible-settings-container');
//	
//		}
	}
	
	function meterSettingsCallback() {
		
	}
	
	function convertUTCDateToLocalDate(date) {
	    var newDate = new Date(date.getTime()+date.getTimezoneOffset()*60*1000);

	    var offset = date.getTimezoneOffset() / 60;
	    var hours = date.getHours();

	    newDate.setHours(hours - offset);

	    return newDate;   
	}
	
	/* refresh imeges in settings view */
	if ($("#last_meter_capture").is(':visible')) {
		setInterval(function(){
			var img = $("#last_meter_capture");
			var src = img.attr("src").split('?')[0];
		    img.attr("src", src + "?"+new Date().getTime());
		},10000);
	}
	
	if ($("#last_knn_capture").is(':visible')) {
		setInterval(function(){
			var img = $("#last_knn_capture");
			var src = img.attr("src").split('?')[0];
		    img.attr("src", src + "?"+new Date().getTime());
		},10000);
	}
	
	// Settings Tabs
	$( "#settings-tabs" ).tabs();
	loadSettingsTab($( "#settings-tabs-1" ), "/db_settings");
	loadSettingsTab($( "#settings-tabs-2" ), "/ci_settings");
	
	
	function loadSettingsTab(tab, url) {
		tab.load( url , function() {
			saveSettingsButtonHandler(tab);
		});
	}
	
	function saveSettingsButtonHandler(tab) {
		var form = tab.find("form");
		var url = form.attr("action");
		var btn = form.find(".save-button");
		btn.click(function (e) {
			
			e.preventDefault();
			$.ajax({
			      type: 'POST',
			      url: url,
			      data: form.serialize(),
			      success: function(response) {
			    	  tab.html(response);
			    	  saveSettingsButtonHandler(tab);
			      },
			      error: function() {
			    	  alert("ERROR");
			      }
			    });
		});
	}
	

});