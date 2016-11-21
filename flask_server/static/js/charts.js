$(function () {
	var period = 'd';
	var startMoment = moment().subtract(1, 'months').startOf('day');
	var endMoment = moment();
	var DATE_FORMAT = "YYYY-MM-DD HH:mm:ss";
	
	if ($('.charts-list').size() > 0) {
		loadChartDataAndRenderAllCharts(period, startMoment, endMoment);
	}
	
	function loadChartDataAndRenderAllCharts(period, startMoment, endMoment) {
		$.getJSON( "get_meters", function(meters) {
			meters.forEach(function (meter) {
				renderChartContainer(meter);
			});
		});
	}
		
	function renderChartContainer(meter) {
		var meter_id = meter['_id']['$oid'];
		var list = $('.charts-list');
		prepareChart(meter);
		addPeriodSelecterHandler(meter);
		renderDateRangePicker(meter);
		addRefreshButtonHandler(meter);
		redrawChart(meter);
	}
	
	function prepareChart(meter) {
		var id = meter['_id']['$oid'];
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
	            //data: costsAndConsumption['units'],
	            type: 'column',
	        },
	        {
		        name: '€',
		        //data: costsAndConsumption['costs'],
		        type: 'column',		      
	        },
		    {
			        
		        type: 'column',
		        name: meter.meter_settings['converted_value_units'],
		        //data: costsAndConsumption['convUnits'],
			      
		      },  
	        {
			            
		        type: 'spline',
		        name: '°C',
		        //data: weather,
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

	function addPeriodSelecterHandler(meter) {
		$("#periodSelector_" + meter['_id']['$oid']).selectable({
			stop: function() {
				var result = $("#select-result").empty();
				$(".ui-selected", this).each(function() {
					redrawChart(meter);
				});
		    }
		});
	}
	
	function redrawChart(meter) {
		
		meterId = meter['_id']['$oid'];

		var ranges = getRangesAsMoments(meterId);
		var period = getPeriod(meterId);
		var chart = $('#chart_' + meterId).highcharts();
			
		$.getJSON( "get_consumption?" 
				+ "meter_id=" + meterId
				+ "&period=" + period 
				+ "&start_date=" + moment(ranges[0]).format(DATE_FORMAT)
				+ "&end_date=" + moment(ranges[1]).format(DATE_FORMAT), function(consumption) {
					
					var costsAndConsumption = calculateCostsAndConvertedConsumption(meter, consumption);
					chart.series[0].setData(costsAndConsumption['units'], true);
					chart.series[1].setData(costsAndConsumption['costs'], true);
					chart.series[2].setData(costsAndConsumption['convUnits'], true);
				
		});
		
		chart.series[3].setData([], true);
		
		$.getJSON( "get_weather?" 
				+ "meter_id=" + meter['_id']['$oid']
				+ "&period=" + period
				+ "&start_date=" + moment(ranges[0]).format(DATE_FORMAT)
				+ "&end_date=" + moment(ranges[1]).format(DATE_FORMAT), function(weather) {
				
					weather.forEach(function (item) {
						item[1] = parseFloat((item[1]).toFixed(1));
					});
					
					chart.series[3].setData(weather, true);

		});
	}
		
	function renderDateRangePicker(meter) {

		var datePicker = $("#date-range-picker_" + meter['_id']['$oid']);
		var startDate = startMoment.toDate();
		var endDate = endMoment.toDate();
		datePicker.daterangepicker({
		     datepickerOptions : {
		         numberOfMonths : 2,
		         //minDate: 0,
		         maxDate: null,
		     }
		 });
			
		datePicker.daterangepicker("setRange", {start: startDate, end: endDate});
		datePicker.on('change', function(event) { 
				redrawChart(meter);
		});
	}
	
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
	}
		
	function getPeriod(meterId) {
		return $("#periodSelector_" + meterId + " > .ui-selected").attr("id");
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
		var cons  = [];
		var convCons = [];
		var costs = [];
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
});