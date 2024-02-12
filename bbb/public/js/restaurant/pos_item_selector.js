import onScan from 'onscan.js';

erpnext.PointOfSale.ItemSelector = class {
	// eslint-disable-next-line no-unused-vars
	constructor({ frm, wrapper, events, pos_profile, settings }) {
		this.wrapper = wrapper;
		this.events = events;
		this.pos_profile = pos_profile;
		this.hide_images = settings.hide_images;
		this.auto_add_item = settings.auto_add_item_to_cart;

		this.inti_component();
	}

	inti_component() {
		this.prepare_dom();
		this.make_search_bar();
		this.load_items_data();
		this.bind_events();
		this.attach_shortcuts();
	}

	prepare_dom() {
		this.wrapper.append(
			`<section class="items-selector">
				<div class="filter-section">
<!--					<div class="label">${__(this.pos_profile)}</div>-->
<!--					<div class="label"><span class="indicator-pill whitespace-nowrap blue"><span>${this.pos_profile}</span></span></div>-->

					<div class="search-field"></div>
					<div class="item-group-field"></div>
				</div>
				<div class="items-container"></div>
			</section>`
		);

		this.$component = this.wrapper.find('.items-selector');
		this.$items_container = this.$component.find('.items-container');
	}

	async load_items_data() {
		if (!this.item_group) {
			const res = await frappe.db.get_value("Item Group", {lft: 1, is_group: 1}, "name");
			this.parent_item_group = res.message.name;
		}
		if (!this.price_list) {
			const res = await frappe.db.get_value("POS Profile", this.pos_profile, "selling_price_list");
			this.price_list = res.message.selling_price_list;
		}

		this.get_items({}).then(({message}) => {
			this.render_item_list(message.items);
		});
	}

	get_items({start = 0, page_length = 40, search_term=''}) {
		const doc = this.events.get_frm().doc;
		const price_list = (doc && doc.selling_price_list) || this.price_list;
		let { item_group, pos_profile } = this;

		!item_group && (item_group = this.parent_item_group);

		return frappe.call({
			method: "bbb.bbb_restaurant.methods.restaurant.get_items",
			freeze: true,
			args: { start, page_length, price_list, item_group, search_term, pos_profile },
		});
	}


	render_item_list(items) {
		this.$items_container.html('');

		items.forEach(item => {
			const item_html = this.get_item_html(item);
			this.$items_container.append(item_html);
		});
	}

	get_item_html(item) {
		const me = this;
		// eslint-disable-next-line no-unused-vars
		const { item_image, serial_no, batch_no, barcode, actual_qty, mrp, stock_uom, price_list_rate, start_date, end_date, discount_amount, price_rule_tag } = item;
		const indicator_color = actual_qty > 10 ? "green" : actual_qty <= 0 ? "red" : "orange";
		const precision = flt(price_list_rate, 2) % 1 != 0 ? 2 : 0;

		let qty_to_display = actual_qty;

		if (Math.round(qty_to_display) > 999) {
			qty_to_display = Math.round(qty_to_display)/1000;
			qty_to_display = qty_to_display.toFixed(1) + 'K';
		}

		function get_item_image_html() {
			// if (!me.hide_images && item_image) {
			// 	return `<div class="item-qty-pill">
			// 				<span class="indicator-pill whitespace-nowrap ${indicator_color}">${qty_to_display}</span>
			// 			</div>
			// 			<div class="flex items-center justify-center h-32 border-b-grey text-6xl text-grey-100">
			// 				<img
			// 					onerror="cur_pos.item_selector.handle_broken_image(this)"
			// 					class="h-full" src="${item_image}"
			// 					alt="${frappe.get_abbr(item.item_name)}"
			// 					style="object-fit: cover;">
			// 			</div>`;
			// } else {
			// 	return `<div class="item-qty-pill">
			// 				<span class="indicator-pill whitespace-nowrap ${indicator_color}">${qty_to_display}</span>
			// 			</div>
			// 			<div class="item-display abbr">${frappe.get_abbr(item.item_name)}</div>`;
			// }

					return `
							<div class="item-display">
								<div class="item-name">
									${frappe.ellipsis(item.item_name, 500)}
								</div>
							</div>
							<div class="item-qty-pill">
<!--									<span class="indicator-pill whitespace-nowrap ${indicator_color}">${qty_to_display}</span>-->
								<span class="indicator-pill whitespace-nowrap ${indicator_color}" style="height:17px"></span>
							</div>`;

		}
		let tag = null
		if(price_rule_tag){
			tag = price_rule_tag.split(' ').join('INV');
		}

		return (
			`<div class="item-wrapper"
				data-item-code="${escape(item.item_code)}" data-serial-no="${escape(serial_no)}"
				data-batch-no="${escape(batch_no)}" data-uom="${escape(stock_uom)}" data-start-date="${escape(item.start_date)}"
				data-end-date="${escape(item.end_date)}" data-discount-amount="${escape(item.discount_amount)}"
				data-rate="${escape(price_list_rate || 0)}" data-mrp="${escape(price_list_rate || 0)}" data-tag="${escape(tag || '')}"
				title="${item.item_name}">

				${get_item_image_html()}

				<div class="item-detail">
				<!--
					<div class="item-name">
						${frappe.ellipsis(item.item_name, 18)}
					</div>-->
					<div class="item-rate">${format_currency(price_list_rate, item.currency, precision) || 0}</div>
				</div>
			</div>`
		);
	}

	handle_broken_image($img) {
		const item_abbr = $($img).attr('alt');
		$($img).parent().replaceWith(`<div class="item-display abbr">${item_abbr}</div>`);
	}

	make_search_bar() {
		const me = this;
		const doc = me.events.get_frm().doc;
		this.$component.find('.search-field').html('');
		this.$component.find('.item-group-field').html('');

		this.search_field = frappe.ui.form.make_control({
			df: {
				label: __('Search'),
				fieldtype: 'Data',
				placeholder: __('Item Code, Barcode, Name')
			},
			parent: this.$component.find('.search-field'),
			render_input: true,
		});
		this.item_group_field = frappe.ui.form.make_control({
			df: {
				label: __('Item Group'),
				fieldtype: 'Link',
				options: 'Item Group',
				placeholder: __('Item Group'),
				onchange: function() {
					me.item_group = this.value;
					!me.item_group && (me.item_group = me.parent_item_group);
					me.filter_items();
				},
				get_query: function () {
					return {
						query: 'erpnext.selling.page.point_of_sale.point_of_sale.item_group_query',
						filters: {
							pos_profile: doc ? doc.pos_profile : ''
						}
					};
				},
			},
			parent: this.$component.find('.item-group-field'),
			render_input: true,
		});
		this.search_field.toggle_label(false);
		this.item_group_field.toggle_label(false);
	}

	set_search_value(value) {
		$(this.search_field.$input[0]).val(value).trigger("input");

	}

	bind_events() {
		const me = this;
		window.onScan = onScan;

		onScan.decodeKeyEvent = function (oEvent) {
			var iCode = this._getNormalizedKeyNum(oEvent);
			switch (true) {
				case iCode >= 48 && iCode <= 90: // numbers and letters
				case iCode >= 106 && iCode <= 111: // operations on numeric keypad (+, -, etc.)
				case (iCode >= 160 && iCode <= 164) || iCode == 170: // ^ ! # $ *
				case iCode >= 186 && iCode <= 194: // (; = , - . / `)
				case iCode >= 219 && iCode <= 222: // ([ \ ] ')
				case iCode == 32: // spacebar
					if (oEvent.key !== undefined && oEvent.key !== '') {
						return oEvent.key;
					}

					var sDecoded = String.fromCharCode(iCode);
					switch (oEvent.shiftKey) {
						case false: sDecoded = sDecoded.toLowerCase(); break;
						case true: sDecoded = sDecoded.toUpperCase(); break;
					}
					return sDecoded;
				case iCode >= 96 && iCode <= 105: // numbers on numeric keypad
					return 0 + (iCode - 96);
			}
			return '';
		};

		onScan.attachTo(document, {
			onScan: (sScancode) => {
				if (this.search_field && this.$component.is(':visible')) {
					this.search_field.set_focus();
					this.set_search_value(sScancode);
					this.barcode_scanned = true;
				}
			}
		});

		this.$component.on('click', '.item-wrapper', function() {
			const $item = $(this);
			const item_code = unescape($item.attr('data-item-code'));
			let batch_no = unescape($item.attr('data-batch-no'));
			let serial_no = unescape($item.attr('data-serial-no'));
			let uom = unescape($item.attr('data-uom'));
			let mrp = unescape($item.attr('data-mrp'));
			let rate = unescape($item.attr('data-rate'));
			let title = unescape($item.attr('title'));
			let start_date= unescape($item.attr('data-start-date'));
			let end_date = unescape($item.attr('data-end-date'));
			let discount_amount = unescape($item.attr('data-discount-amount'));
			let tag = $item.attr('data-tag');
			// console.log(start_date, end_date, item_discount_amount)
			// escape(undefined) returns "undefined" then unescape returns "undefined"
			batch_no = batch_no === "undefined" ? undefined : batch_no;
			serial_no = serial_no === "undefined" ? undefined : serial_no;
			uom = uom === "undefined" ? undefined : uom;
			rate = rate === "undefined" ? undefined : rate;
			mrp = mrp === "undefined" ? undefined : mrp;
			title = title === "undefined" ? undefined : title;
			start_date = start_date === "undefined" ? undefined : new Date(start_date);
			end_date = end_date === "undefined" ? undefined : new Date(end_date);
			discount_amount = discount_amount === "undefined" ? undefined : discount_amount;
			tag = tag === "undefined" ? undefined : tag;
			me.events.item_selected({
				field: 'qty',
				value: "+1",
				item: { item_code, batch_no, serial_no, uom, rate, mrp, title, start_date, end_date, discount_amount, tag, update_rules: false},
				item_quantity: 1
			});
			me.set_search_value('');
		});

		this.search_field.$input.on('input', (e) => {
			clearTimeout(this.last_search);
			this.last_search = setTimeout(() => {
				const search_term = e.target.value;
				this.filter_items({ search_term });
			}, 300);
		});
	}

	attach_shortcuts() {
		const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
		this.search_field.parent.attr("title", `${ctrl_label}+I`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+i",
			action: () => this.search_field.set_focus(),
			condition: () => this.$component.is(':visible'),
			description: __("Focus on search input"),
			ignore_inputs: true,
			page: cur_page.page.page
		});
		this.item_group_field.parent.attr("title", `${ctrl_label}+G`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+g",
			action: () => this.item_group_field.set_focus(),
			condition: () => this.$component.is(':visible'),
			description: __("Focus on Item Group filter"),
			ignore_inputs: true,
			page: cur_page.page.page
		});

		// for selecting the last filtered item on search
		frappe.ui.keys.on("enter", () => {
			const selector_is_visible = this.$component.is(':visible');
			if (!selector_is_visible || this.search_field.get_value() === "") return;

			if (this.items.length == 1) {
				this.$items_container.find(".item-wrapper").click();
				frappe.utils.play_sound("submit");
				$(this.search_field.$input[0]).val("").trigger("input");
			} else if (this.items.length == 0 && this.barcode_scanned) {
				// only show alert of barcode is scanned and enter is pressed
				frappe.show_alert({
					message: __("No items found. Scan barcode again."),
					indicator: 'orange'
				});
				frappe.utils.play_sound("error");
				this.barcode_scanned = false;
				$(this.search_field.$input[0]).val("").trigger("input");
			}
		});
	}

	filter_items({ search_term='' }={}) {
		if (search_term) {
			search_term = search_term.toLowerCase();

			// memoize
			this.search_index = this.search_index || {};
			if (this.search_index[search_term]) {
				const items = this.search_index[search_term];
				this.items = items;
				this.render_item_list(items);
				this.auto_add_item && this.items.length == 1 && this.add_filtered_item_to_cart();
				return;
			}
		}


		this.get_items({ search_term })
			.then(({ message }) => {
				// eslint-disable-next-line no-unused-vars
				const { items, serial_no, batch_no, barcode } = message;
				if (search_term && !barcode) {
					this.search_index[search_term] = items;
				}
				this.items = items;
				this.render_item_list(items);
				this.auto_add_item && this.items.length == 1 && this.add_filtered_item_to_cart();
			});
	}

	add_filtered_item_to_cart() {
		if(this.barcode_scanned){
			this.$items_container.find(".item-wrapper").click();
			this.barcode_scanned = false
		}
	}

	resize_selector(minimize) {
		minimize ?
			this.$component.find('.filter-section').css('grid-template-columns', 'repeat(1, minmax(0, 1fr))') :
			this.$component.find('.filter-section').css('grid-template-columns', 'repeat(12, minmax(0, 1fr))');

		minimize ?
			this.$component.find('.search-field').css('margin', 'var(--margin-sm) 0px') :
			this.$component.find('.search-field').css('margin', '0px var(--margin-sm)');

		minimize ?
			this.$component.css('grid-column', 'span 4 / span 4') :
			this.$component.css('grid-column', 'span 2 / span 2');

		minimize ?
			this.$items_container.css('grid-template-columns', 'repeat(2, minmax(0, 1fr))') :
			this.$items_container.css('grid-template-columns', 'repeat(1, minmax(0, 1fr))');
	}

	toggle_component(show) {
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}
};
