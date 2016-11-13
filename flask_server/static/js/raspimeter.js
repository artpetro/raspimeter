$(function() {
 
	// Meter Tabs
	// Meter Tabs
	$("#meter-tabs").tabs();
	loadSettingsTab($("#meter-tabs-meter-settings"), "/meter_settings");
	loadSettingsTab($("#meter-tabs-meter-image-settings"),
			"/meter_image_settings");
	loadSettingsTab($("#meter-tabs-knn-settings"), "/knn_settings");

	var meterId = $("#meter-tabs").attr("meter_id");

	loadImagesTab($("#meter-tabs-images"), '/images', meterId, 1, -1);
	loadValuesTab($("#meter-tabs-values"), '/values', meterId, 1, -1);
	$("#meter-tabs-knn-data").load('/knn_data' + "?meter_id=" + meterId);

	function loadImagesTab(tab, url, meterId, page, flag) {

		tab.load(url + "?meter_id=" + meterId + "&flag=" + flag + "&page="
				+ page, function() {
			
			$("img.lazy").lazyload({
				event : 'scroll load-images'
			});
			
			filtering();
			images();

			addSingleImageButtonsHandler();
			addPreviewCloseHandler();

			tab.find('.pagination > a').each(function() {
				$(this).attr("href", "#");
			})
			
			tab.find('.pagination > a').click(function(event) {
				event.preventDefault();
				var page = $(event.target).text();
				loadImagesTab(tab, url, meterId, page, flag);
			});
		});
	}

	function loadValuesTab(tab, url, meterId, page, flag) {
		tab.load(url + "?meter_id=" + meterId + "&flag=" + flag + "&page="
				+ page, function() {
			
			tab.find('.pagination > a').each(function() {
				$(this).attr("href", "#");
			})
			
			tab.find('.pagination > a').click(function(event) {
				event.preventDefault();
				var page = $(event.target).text();
				loadValuesTab(tab, url, meterId, page, flag);
			});
		});
	}


	// Settings Tabs
	$("#settings-tabs").tabs();
	loadSettingsTab($("#settings-tabs-1"), "/db_settings");
	loadSettingsTab($("#settings-tabs-2"), "/ci_settings");

	function loadSettingsTab(tab, url) {
		tab.load(url, function() {
			saveSettingsButtonHandler(tab);
		});
	}

	function saveSettingsButtonHandler(tab) {
		var form = tab.find("form");
		var url = form.attr("action");
		var btn = form.find(".save-button");
		btn.click(function(e) {

			e.preventDefault();
			$.ajax({
				type : 'POST',
				url : url,
				data : form.serialize(),
				success : function(response) {
					tab.html(response);
					saveSettingsButtonHandler(tab);
				},
				error : function() {
					alert("ERROR");
				}
			});
		});
	}

	
	function filtering() {

		var filters = {};
		var checkboxes = $('.all-products input[type=checkbox]');

		checkboxes.click(function() {

			var that = $(this), specName = that.attr('name');

			// When a checkbox is checked we need to write that in the filters
			// object;
			if (that.is(":checked")) {

				// If the filter for this specification isn't created yet - do
				// it.
				if (!(filters[specName] && filters[specName].length)) {
					filters[specName] = [];
				}

				// Push values into the chosen filter array
				filters[specName].push(that.val());

			}

			// When a checkbox is unchecked we need to remove its value from the
			// filters object.
			if (!that.is(":checked")) {

				if (filters[specName] && filters[specName].length
						&& (filters[specName].indexOf(that.val()) != -1)) {

					// Find the checkbox value in the corresponding array inside
					// the filters object.
					var index = filters[specName].indexOf(that.val());

					// Remove it.
					filters[specName].splice(index, 1);

					// If it was the last remaining value for this
					// specification,
					// delete the whole array.
					if (!filters[specName].length) {
						delete filters[specName];
					}

				}
			}

			// Change the url hash;
			createQueryHash(filters);

		});

		// When the "Clear all filters" button is pressed change the hash to '#'
		// (go to the home page)
		$('.clear-filters-button').click(function(e) {
			e.preventDefault();
			window.location.hash = '#';
		});

		// Try to recognize all
		$('.recognize-all-button').click(
				function(e) {

					e.preventDefault();

					var meterId = $('.products-list').attr('id');
					var page = $(this).attr('id');

					console.log(page);

					$.getJSON("recognize_all?meter_id=" + meterId + "&page="
							+ page, function(data) {

						// TODO loader.gif
						console.log(data);
						window.location.hash = '#';

					});
				});

		$(window).on('hashchange', function() {
			render(decodeURI(window.location.hash));
		});
	}
	
	function addPreviewCloseHandler() {
		
		var singleProductPage = $('.single-product');
		
		singleProductPage.on('click', function(e) {

			if (singleProductPage.hasClass('visible')) {

				var clicked = $(e.target);

				if (clicked.hasClass('close') || clicked.hasClass('overlay')) {
					closePreview();
				}
			}
		});
	}

	function addSingleImageButtonsHandler() {
		$('#delete_button').click(function() {
			deleteMeterImageAndMeterValue();
			return false;
		});

		$('#save_button').click(function() {
			trainKNNAndStoreIntoDB();
			return false;
		});
	}

	function images() {

		$('.all-products .products-list').find('li').on('click', function(e) {

			e.preventDefault();

			var imageId = $(this).data('index');

			// window.location.hash = '#' + imageId;

			// fetch single image data
			$.getJSON("get_image?id=" + imageId, function(image) {

				renderSingleMeterValue(image);

			});
		})

	}

	function renderSingleMeterValue(image) {

		var page = $('.single-product');
		var container = $('.preview-large');

		$.getJSON("get_digits?image_name=" + image.name, function(digits) {

			$.getJSON("get_meter?id=" + image.name.split("_")[2], function(
					meter) {

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

					var listItem = '<li><div id="digit-cell-'
							+ index
							+ '" class="digit-cell">'
							+ '<input id="'
							+ index
							+ '" class="digit-input" type="number" maxlength="1" size="1" value="'
							+ digit + '">' + '</div></li>';

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
				$('#digit-cell-' + index).addClass('decimal');
			}
		});

		// WOZU???
		if (flag != 0) {
			enableSaveButton();
		}

		var old_value = 0;

		$('.digit-input').focus(function() {

			old_value = $(this).val();
			$(this).select();

		});

		$('.digit-input').blur(function() {

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

	function trainKNNAndStoreIntoDB() {

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

		$.getJSON("/save_digits?image_name=" + imageName + "&train=" + train
				+ "&responses=" + JSON.stringify(responses), function(resp) {

			console.log(resp);
			$('#save_button').addClass('disabled-button');
			// updatePreview();

		});
	}

	function deleteMeterImageAndMeterValue() {

		// TODO confirm dialog
		var container = $('.preview-large');
		var time = container.find('h3').text();
		var imageName = container.find('img').attr('image-name');

		var perm_delete = $('#permanently_delete').prop('checked');

		$.getJSON("/delete_meter_value?image_name=" + imageName + "&perm="
				+ perm_delete, function(resp) {

			console.log(resp);
			$("li[id*='" + time + "']").remove();
			closePreview();

		});
	}

	function closePreview() {
		// createQueryHash(filters);
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

		var map = {

			'' : function() {

				filters = {};
				checkboxes.prop('checked', false);
				filterImages(filters);

			},

			'#' : function() {

				filters = {};
				checkboxes.prop('checked', false);
				filterImages(filters);

			},

			// Page with filtered products
			'#filter' : function() {

				url = url.split('#filter/')[1].trim();

				try {
					filters = JSON.parse(url);
				} catch (err) {
					window.location.hash = '#';
					return;
				}

				filterImages(filters);

			}
		};

		if (map[temp]) {
			map[temp]();
		}
	}

	function filterImages(filters) {

		// console.log("filter images: ");
		// console.log(filters);

		if (typeof filters['flag'] === "undefined") {

			$('.all-products .products-list > li').show();

		} else {

			$('.all-products .products-list > li').hide();

			$.each(filters['flag'], function(index, value) {

				// console.log($("li[flag='" + value + "']"));

				$("li[flag='" + value + "']").show();

				$(window).resize();//
				$("img.lazy").trigger("load-images");

				// When you initialize lazyload you can tell it which event(s)
				// to trigger on (by default it is set to 'scroll'). I suggest
				// adding a custom event to that list and triggering it whenever
				// it makes sense for you:
				//
				// $('.lazy').lazyload({
				// event: 'scroll whenever-i-want'
				// });
				//
				// // whenever you want to trigger your event (after ajax load,
				// on dom ready, etc...)
				// $(document).trigger('whenever-i-want');
				// This leaves the default scroll functionality in but also
				// allows you to trigger the lazy loading on demand.

			});
		}
	}

	// Shows the error page.
	function renderErrorPage() {
		var page = $('.error');
		page.addClass('visible');
	}

	// Get the filters object, turn it into a string and write it into the hash.
	function createQueryHash(filters) {

		// Here we check if filters isn't empty.
		if (!$.isEmptyObject(filters)) {
			// Stringify the object via JSON.stringify and write it after the
			// '#filter' keyword.
			window.location.hash = '#filter/' + JSON.stringify(filters);
		} else {
			// If it's empty change the hash to '#' (the homepage).
			window.location.hash = '#';
		}
	}

});