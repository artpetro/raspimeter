$(function() {
 
	// Meter Tabs
	$("#meter-tabs").tabs();
	loadSettingsTab($("#meter-tabs-meter-settings"), "/meter_settings");
	loadSettingsTab($("#meter-tabs-meter-image-settings"),
			"/meter_image_settings");
	loadSettingsTab($("#meter-tabs-knn-settings"), "/knn_settings");

	var meterId = $("#meter-tabs").attr("meter_id");

	loadImagesTab($("#meter-tabs-images"), '/images', meterId, 1, -1);
	loadValuesTab($("#meter-tabs-values"), '/values', meterId, 1, -1);
	loadKNNData($("#meter-tabs-knn-data"), '/knn_data', meterId);

	function loadImagesTab(tab, url, meterId, page, flag) {

		tab.load(url + "?meter_id=" + meterId + "&flag=" + flag + "&page="
				+ page, function() {
			
			$("img.lazy").lazyload({
				event : 'scroll load-images'
			});
			
			tab.find(':input[value="' + flag + '"]').prop('checked',true);
			
			filterHandler(tab, url, meterId, page);
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
	
	
	function loadKNNData(tab, url, meterId) {
		tab.load(url + "?meter_id=" + meterId, function() {
			
			 $(this).find("#delete-knn-data").click(function() {
				
				var checkBoxes = tab.find(".knn-data-checkbox:checked");
				var ids = [];
				
				checkBoxes.each(function() {
					ids.push($(this).attr("id"));
				});
				
				$.get("/delete_knn_data", {
						meter_id : meterId,
						ids : JSON.stringify(ids)
					}, function(data) {
						console.log(data);
						loadKNNData(tab, url, meterId);
				}).fail(function() {
				    alert( "ERROR" );
				});
				
			});
		});
	}


	// Settings Tabs
	$("#settings-tabs").tabs();
	loadSettingsTab($("#settings-tabs-1"), "/db_settings");
	loadSettingsTab($("#settings-tabs-2"), "/ci_settings");
	$("#settings-tabs-controls").load('/controls', function() {
		addRestartButtonHandler($("#restart-server-button"), '/restart_server');
		addRestartButtonHandler($("#restart-runner-button"), '/restart_runner');
	});

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
	
	
	function addRestartButtonHandler(btn, url) {
		btn.click(function(e) {
			e.preventDefault();
			$.ajax({
				type : 'GET',
				url : url,
				success : function(response) {
					alert(response);
				},
				error : function() {
					alert("ERROR");
				}
			});
		});
	}
	
	
	function filterHandler(tab, url, meterId, page) {

		var radiobuttons = tab.find('input[type=radio]');

		radiobuttons.click(function() {
			
			var flag = $(this).val();

			loadImagesTab(tab, url, meterId, page, flag);

		});

	}

	
	// Try to recognize all on page
	$('.recognize-all-button').click(
			function(e) {

				e.preventDefault();

				var meterId = $('.products-list').attr('id');
				var page = $(this).attr('id');

				console.log(page);

				$.getJSON(
						"recognize_all?meter_id=" + meterId + "&page=" + page,
						function(data) {

							// TODO loader.gif
							console.log(data);
							window.location.hash = '#';

						});
		});
	
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
		
		var img = container.find('img');
		img.attr('data-original', 'static/images/' + image.name);//.attr('src', 'static/images/' + image.name);
		img.lazyload({
			effect : "fadeIn"
		});
		img.attr('image-name', image.name);

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
		var page = $('.single-product');
		page.removeClass('visible');
		var container = $('.preview-large');
		container.find('h3').text("");
		container.find('img').attr('data-original', '');
		container.find('img').attr('image-name', '');
		var list = $('.single-product .preview-large .meter-value-rectangle .digits-list');
		list.empty();
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