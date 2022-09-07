erpnext.PointOfSale.ItemCart = class {
    constructor({wrapper, events, settings}) {
        this.wrapper = wrapper;
        this.events = events;
        this.customer_info = undefined;
        this.served_by_info = undefined;
        this.ignore_discount = undefined;
        this.ignore_pricing_rule = "No";
        this.hide_images = settings.hide_images;
        this.allowed_customer_groups = settings.customer_groups;
        this.allow_rate_change = settings.allow_rate_change;
        this.allow_discount_change = settings.allow_discount_change;
        this.init_component();
    }

    init_component() {
        this.prepare_dom();
        this.init_child_components();
        this.bind_events();
        this.attach_shortcuts();
    }

    prepare_dom() {
        this.wrapper.append(
            `<section class="customer-cart-container"></section>`
        )

        this.$component = this.wrapper.find('.customer-cart-container');

    }

    init_child_components() {
        this.init_customer_selector();
        this.init_cart_components();
    }

    init_customer_selector() {
        this.$component.append(
            `<div class="customer-header-section"></div>`
        );
        this.$customer_header_section = this.$component.find('.customer-header-section');
        this.$customer_header_section.append(
            `<div class="customer-section"></div>`
        );
        this.$customer_header_section.append(
            `<div class="served-by-section"></div>`
        );
        this.$customer_header_section.append(
            `<div class="pricing-discount-section"></div>`
        );
        this.$customer_header_section.append(
            `<div class="pos-profile-section"></div>`
        );
        this.$customer_header_section.append(
            `<div class="menu-section"></div>`
        );


        this.$customer_section = this.$customer_header_section.find('.customer-section');
        this.$served_by_section = this.$customer_header_section.find('.served-by-section');
        this.$pricing_rule_discount_section = this.$customer_header_section.find('.pricing-discount-section');
        this.$menu_section = this.$customer_header_section.find('.menu-section');
        this.$pos_profile_section = this.$customer_header_section.find('.pos-profile-section');

        this.make_customer_selector();
        this.make_served_by_selector();
        this.make_discount_price_selector();
        this.make_menu_dropdown();
    }

    reset_customer_selector() {
        const frm = this.events.get_frm();
        if(frm.doc.is_return === 1) return;
        // if($('.checkout-btn').is(":visible")) return;
        frm.set_value('customer', '');
        this.make_customer_selector();
        this.customer_field.set_focus();
    }

    reset_served_by_selector() {
        const frm = this.events.get_frm();
        if(frm.doc.is_return === 1) return;
        // if($('.checkout-btn').is(":visible")) return;

        frm.set_value('served_by', '');
        this.make_served_by_selector();
        this.served_by_field.set_focus();
    }
    reset_ignore_discount_selector() {
        const frm = this.events.get_frm();
        if(frm.doc.is_return === 1) return;
        // if($('.checkout-btn').is(":visible")) return;
        frm.set_value('ignore_pricing_rule', 0);
        this.make_discount_price_selector();
        this.price_rule_ignore_discount_field.set_focus();
    }

    init_cart_components() {
        this.$component.append(
            `<div class="cart-container">
				<div class="abs-cart-container">
<!--					<div class="cart-label">Item Cart</div>-->
					<div class="cart-header">
						<div class="name-header">Product</div>
						<div class="mrp-header">MRP</div>
						<div class="discount-header">Disc</div>
						<div class="after-discount-header">After Disc</div>
						<div class="qty-header">Qty</div>
<!--						<div class="qty-header">Damaged Cost</div>-->
						<div class="rate-amount-header">Amount</div>
					</div>
					<div class="cart-items-section"></div>
					<div class="cart-totals-section"></div>
					<div class="numpad-section"></div>
				</div>
			</div>`
        );
        this.$cart_container = this.$component.find('.cart-container');

        this.make_cart_totals_section();
        this.make_cart_items_section();
        this.make_cart_numpad();
    }

    make_cart_items_section() {
        this.$cart_header = this.$component.find('.cart-header');
        this.$cart_items_wrapper = this.$component.find('.cart-items-section');

        this.make_no_items_placeholder();
    }

    make_no_items_placeholder() {
        this.$cart_header.css('display', 'none');
        this.$cart_items_wrapper.html(
            `<div class="no-item-wrapper">No items in cart</div>`
        );
    }

    get_discount_icon() {
        return (
            `<svg class="discount-icon" width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" fill="none" xmlns="http://www.w3.org/2000/svg">
				<path d="M19 15.6213C19 15.2235 19.158 14.842 19.4393 14.5607L20.9393 13.0607C21.5251 12.4749 21.5251 11.5251 20.9393 10.9393L19.4393 9.43934C19.158 9.15804 19 8.7765 19 8.37868V6.5C19 5.67157 18.3284 5 17.5 5H15.6213C15.2235 5 14.842 4.84196 14.5607 4.56066L13.0607 3.06066C12.4749 2.47487 11.5251 2.47487 10.9393 3.06066L9.43934 4.56066C9.15804 4.84196 8.7765 5 8.37868 5H6.5C5.67157 5 5 5.67157 5 6.5V8.37868C5 8.7765 4.84196 9.15804 4.56066 9.43934L3.06066 10.9393C2.47487 11.5251 2.47487 12.4749 3.06066 13.0607L4.56066 14.5607C4.84196 14.842 5 15.2235 5 15.6213V17.5C5 18.3284 5.67157 19 6.5 19H8.37868C8.7765 19 9.15804 19.158 9.43934 19.4393L10.9393 20.9393C11.5251 21.5251 12.4749 21.5251 13.0607 20.9393L14.5607 19.4393C14.842 19.158 15.2235 19 15.6213 19H17.5C18.3284 19 19 18.3284 19 17.5V15.6213Z" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M15 9L9 15" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M10.5 9.5C10.5 10.0523 10.0523 10.5 9.5 10.5C8.94772 10.5 8.5 10.0523 8.5 9.5C8.5 8.94772 8.94772 8.5 9.5 8.5C10.0523 8.5 10.5 8.94772 10.5 9.5Z" fill="white" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M15.5 14.5C15.5 15.0523 15.0523 15.5 14.5 15.5C13.9477 15.5 13.5 15.0523 13.5 14.5C13.5 13.9477 13.9477 13.5 14.5 13.5C15.0523 13.5 15.5 13.9477 15.5 14.5Z" fill="white" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>`
        );
    }

    make_cart_totals_section() {
        this.$totals_section = this.$component.find('.cart-totals-section');

        this.$totals_section.append(
            `<div class="total-section">
                <div class="total-label" >Total</div>
                <div class="mrp-label" >0</div>
                <div class="disc-label" >0</div>
                <div class="after-disc-label" >0</div>
                <div class="qty-label" >0</div>
                <div class="final-amount-total-label">0</div>
            </div>
            <div class="additional-discount-section">
                 <div class="add-discount-wrapper" can_click="enabled">
                    ${this.get_discount_icon()} Add Discount
                </div>
                <div class="add-discount-amount-wrapper" style="display:none" can_click="enabled">
                     Add Discount Amount
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                	<div class="net-total-container">
                        <div class="net-total-label">Net Total</div>
                        <div class="net-total-value">0.00</div>
                    </div>
                    <div class="taxes-container"></div>
                    <div class="special-discount-container">
                        <div>Special Discount</div>
                        <div>0.00</div>
                    </div>
               </div>
                <div class="col-md-6">
                    <div class="grand-total-container">
                        <div>Grand Total</div>
                        <div>0.00</div>
                    </div>
                    <div class="rounding-adjustment-container">
                        <div>Rounding Adjustment</div>
                        <div>0.00</div>
                    </div>
                     <div class="rounded-total-container">
                        <div>Rounded Total</div>
                        <div>0.00</div>
                    </div>
                </div>
            </div>
			<div class="checkout-btn">Checkout</div>
			<div class="edit-cart-btn">Edit Cart</div>`
        );
        $('.total-section').css('visibility', 'hidden');
        this.$add_discount_elem = this.$component.find(".add-discount-wrapper");
        this.$add_discount_amount_elem = this.$component.find(".add-discount-amount-wrapper");
    }

    make_cart_numpad() {
        this.$numpad_section = this.$component.find('.numpad-section');

        this.number_pad = new erpnext.PointOfSale.NumberPad({
            wrapper: this.$numpad_section,
            events: {
                numpad_event: this.on_numpad_event.bind(this)
            },
            cols: 5,
            keys: [
                [1, 2, 3, 'Quantity'],
                [4, 5, 6, 'Discount'],
                [7, 8, 9, 'Rate'],
                ['-', 0, 'Delete', 'Remove']
            ],
            css_classes: [
                ['', '', '', 'col-span-2'],
                ['', '', '', 'col-span-2'],
                ['', '', '', 'col-span-2'],
                ['', '', '', 'col-span-2 remove-btn']
            ],
            fieldnames_map: {'Quantity': 'qty', 'Discount': 'discount_percentage'}
        })

        this.$numpad_section.prepend(
            `<div class="numpad-totals">
				<span class="numpad-net-total"></span>
				<span class="numpad-grand-total"></span>
			</div>`
        )

        this.$numpad_section.append(
            `<div class="numpad-btn checkout-btn" data-button-value="checkout">Checkout</div>`
        )
    }

    bind_events() {
        const me = this;
        this.$customer_section.on('click', '.reset-customer-btn', function () {
            me.reset_customer_selector();
        });

        this.$served_by_section.on('click', '.reset-served-by-btn', function () {
            me.reset_served_by_selector();
        });
        this.$pricing_rule_discount_section.on('click', '.reset-ignore_pricing-rule-btn', function () {
            me.reset_ignore_discount_selector();
        });

        this.$customer_section.on('click', '.close-details-btn', function () {
            // me.toggle_customer_info(false);
        });

        this.$customer_section.on('click', '.customer-display', function (e) {
            // if ($(e.target).closest('.reset-customer-btn').length) return;
            //
            // const show = me.$cart_container.is(':visible');
            // me.toggle_customer_info(show);
        });

        this.$cart_items_wrapper.on('click', '.cart-item-wrapper', function () {
            const $cart_item = $(this);

            me.toggle_item_highlight(this);

            const payment_section_hidden = !me.$totals_section.find('.edit-cart-btn').is(':visible');
            if (!payment_section_hidden) {
                // payment section is visible
                // edit cart first and then open item details section
                me.$totals_section.find(".edit-cart-btn").click();
            }

            const item_row_name = unescape($cart_item.attr('data-row-name'));
            me.events.cart_item_clicked({name: item_row_name});
            this.numpad_value = '';
        });

        this.$component.on('click', '.checkout-btn', function () {
            if ($(this).attr('style').indexOf('--blue-500') == -1) return;
            const frm = me.events.get_frm();
            let rounded_total = frm.doc.rounded_total;
            let payments = frm.doc.payments;
            payments[0].amount = rounded_total;
            payments[0].base_amount =rounded_total;
            frappe.model.set_value(frm.doctype, frm.docname, 'paid_amount', rounded_total);
            $(".add-discount-wrapper").attr('can_click','disabled');
            $(".add-discount-amount-wrapper").attr('can_click','disabled');
            me.wrapper.find('.customer-cart-container').css('grid-column', 'span 5 / span 5');
            me.events.checkout();
            me.toggle_checkout_btn(false);
            //rabi
            if(!frm.doc.additional_discount_percentage || frm.doc.additional_discount_percentage === 0){
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage', 0);
                me.$add_discount_elem.css({
                    'border': '1px dashed var(--gray-500)',
                    'padding': 'var(--padding-sm) var(--padding-md)'
                });
                me.$add_discount_elem.html(`${me.get_discount_icon()} Add Discount`);
                me.discount_field = undefined;
            }
            if(!frm.doc.discount_amount || frm.doc.discount_amount === 0) {
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_amount', 0);
                me.$add_discount_amount_elem.css({
                    'border': '1px dashed var(--gray-500)',
                    'padding': 'var(--padding-sm) var(--padding-md)'
                });
                me.$add_discount_amount_elem.html(`${me.get_discount_icon()} Add Discount`);
                me.discount_amount_field = undefined;
            }
            if(frm.doc.discount_amount || frm.doc.discount_percentage){
                // me.hide_discount_control(frm.doc.discount_percentage);
                this.$add_discount_elem.css({
                    'border': '1px dashed var(--dark-green-500)',
                    'padding': 'var(--padding-sm) var(--padding-md)'
                });
                this.$add_discount_elem.html(
                    `<div class="edit-discount-btn">
                        ${this.get_discount_icon()} ${String(frm.doc.discount_percentage ? frm.doc.discount_percentage : 0).bold()}% discount applied
                    </div>`
                );
                // me.hide_discount_amount_control(frm.doc.discount_amount);

                this.$add_discount_amount_elem.css({
                    'border': '1px dashed var(--dark-green-500)',
                    'padding': 'var(--padding-sm) var(--padding-md)'
                });
                this.$add_discount_amount_elem.html(
                    `<div class="edit-discount-amount-btn">
                        ${this.get_discount_icon()} ${String(frm.doc.discount_amount).bold()}&nbsp;TK discount applied
                    </div>`
                );
            }

            //
            // me.allow_discount_change && me.$add_discount_elem.removeClass("d-none");
            // me.allow_discount_change && me.$add_discount_amount_elem.removeClass("d-none");

            $('.reset-customer-btn').css('display', 'none');
            $('.reset-served-by-btn').css('display', 'none');
            $('.reset-ignore_pricing-rule-btn').css('display', 'none');


        });

        this.$totals_section.on('click', '.edit-cart-btn', () => {
            $(".add-discount-wrapper").attr('can_click','enabled');
            $(".add-discount-amount-wrapper").attr('can_click','enabled');
            me.wrapper.find('.customer-cart-container').css('grid-column', 'span 7 / span 7');
            this.events.edit_cart();
            this.toggle_checkout_btn(true);
            const frm = me.events.get_frm();
            if(frm.doc.is_return === 0) {
                $('.reset-customer-btn').css('display', 'flex');
                $('.reset-served-by-btn').css('display', 'flex');
                // $('.reset-ignore_pricing-rule-btn').css('display', 'flex');
            }else{
                $('.reset-customer-btn').css('display', 'none');
                $('.reset-served-by-btn').css('display', 'none');
                $('.reset-ignore_pricing-rule-btn').css('display', 'none');
            }
        });

        this.$component.on('click', '.add-discount-wrapper', () => {
            const can_edit_discount = this.$add_discount_elem.find('.edit-discount-btn').length;
            const can_click = $(".add-discount-wrapper").attr('can_click');

            if(can_click === 'enabled'){
                if (!this.discount_field || can_edit_discount){
                    this.show_discount_amount_control();
                    this.show_discount_control();
                }
            }
        });
        this.$component.on('click', '.add-discount-amount-wrapper', () => {
            const can_edit_discount = this.$add_discount_amount_elem.find('.edit-discount-amount-btn').length;
            const can_click = $(".add-discount-amount-wrapper").attr('can_click');
            if(can_click === 'enabled'){
                if (!this.discount_field || can_edit_discount){
                    this.show_discount_control();
                    this.show_discount_amount_control();
                }
            }

        });

        frappe.ui.form.on("POS Invoice", "paid_amount", frm => {
            // called when discount is applied
            this.update_totals_section(frm);
        });
    }

    attach_shortcuts() {
        for (let row of this.number_pad.keys) {
            for (let btn of row) {
                if (typeof btn !== 'string') continue; // do not make shortcuts for numbers

                let shortcut_key = `ctrl+${frappe.scrub(String(btn))[0]}`;
                if (btn === 'Delete') shortcut_key = 'ctrl+backspace';
                if (btn === 'Remove') shortcut_key = 'shift+ctrl+backspace';
                if (btn === '.') shortcut_key = 'ctrl+>';

                // to account for fieldname map
                const fieldname = this.number_pad.fieldnames[btn] ? this.number_pad.fieldnames[btn] :
                    typeof btn === 'string' ? frappe.scrub(btn) : btn;

                let shortcut_label = shortcut_key.split('+').map(frappe.utils.to_title_case).join('+');
                shortcut_label = frappe.utils.is_mac() ? shortcut_label.replace('Ctrl', '⌘') : shortcut_label;
                this.$numpad_section.find(`.numpad-btn[data-button-value="${fieldname}"]`).attr("title", shortcut_label);

                frappe.ui.keys.on(`${shortcut_key}`, () => {
                    const cart_is_visible = this.$component.is(":visible");
                    if (cart_is_visible && this.item_is_selected && this.$numpad_section.is(":visible")) {
                        this.$numpad_section.find(`.numpad-btn[data-button-value="${fieldname}"]`).click();
                    }
                })
            }
        }
        const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
        this.$component.find(".checkout-btn").attr("title", `${ctrl_label}+Enter`);
        frappe.ui.keys.add_shortcut({
            shortcut: "ctrl+enter",
            action: () => this.$component.find(".checkout-btn").click(),
            condition: () => this.$component.is(":visible") && !this.$totals_section.find('.edit-cart-btn').is(':visible') && this.wrapper.find('.customer-cart-container').css('grid-column', 'span 5 / span 5'),
            description: __("Checkout Order / Submit Order / New Order"),
            ignore_inputs: true,
            page: cur_page.page.page
        });
        this.$component.find(".edit-cart-btn").attr("title", `${ctrl_label}+E`);
        frappe.ui.keys.on("ctrl+e", () => {
            const item_cart_visible = this.$component.is(":visible");
            const checkout_btn_invisible = !this.$totals_section.find('.checkout-btn').is('visible');
            if (item_cart_visible && checkout_btn_invisible) {
                this.wrapper.find('.customer-cart-container').css('grid-column', 'span 7 / span 7')
                this.$component.find(".edit-cart-btn").click();
            }
        });
        this.$component.find(".add-discount-wrapper").attr("title", `${ctrl_label}+D`);
        frappe.ui.keys.add_shortcut({
            shortcut: "ctrl+d",
            action: () => this.$component.find(".add-discount-wrapper").click(),
            condition: () => this.$add_discount_elem.is(":visible") && this.$add_discount_amount_elem.is(':visible'),
            description: __("Add Order Discount"),
            ignore_inputs: true,
            page: cur_page.page.page
        });
        frappe.ui.keys.on("escape", () => {
            const item_cart_visible = this.$component.is(":visible");
            if (item_cart_visible && this.discount_field && this.discount_field.parent.is(":visible")) {
                this.discount_field.set_value(0);
            }
            if (item_cart_visible && this.discount_amount_field && this.discount_field.parent.is(":visible")) {
                this.discount_field.set_value(0);
            }
        });
    }

    toggle_item_highlight(item) {
        const $cart_item = $(item);
        const item_is_highlighted = $cart_item.attr("style") == 'background-color: var(--blue-100);';
        if (!item || item_is_highlighted) {
            this.item_is_selected = false;
            this.$cart_container.find('.cart-item-wrapper').css("background-color", "");
        } else {
            $cart_item.css("background-color", "var(--blue-100)");
            this.item_is_selected = true;
            this.$cart_container.find('.cart-item-wrapper').not(item).css("background-color", "");
        }
    }

    make_customer_selector() {
        this.$customer_section.html(`
			<div class="customer-field"></div>
		`);
        const me = this;
        const query = {query: 'erpnext.controllers.queries.customer_query'};
        const allowed_customer_group = this.allowed_customer_groups || [];
        if (allowed_customer_group.length) {
            query.filters = {
                customer_group: ['in', allowed_customer_group]
            }
        }
        this.customer_field = frappe.ui.form.make_control({
            df: {
                label: __('Customer'),
                fieldtype: 'Link',
                options: 'Customer',
                placeholder: __('Search by customer name, phone, email.'),
                get_query: () => query,
                onchange: function () {
                    if (this.value) {
                        const frm = me.events.get_frm();
                        frappe.dom.freeze();
                        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', this.value);
                        frm.script_manager.trigger('customer', frm.doc.doctype, frm.doc.name).then(() => {
                            frappe.run_serially([
                                () => me.fetch_customer_details(this.value),
                                () => me.events.customer_details_updated(me.customer_info),
                                () => me.update_customer_section(),
                                () => me.update_totals_section(),
                                // () => me.events.set_cache_data({'pos_customer': this.value}),
                                // () => me.check_out_validation(true),
                                () => frappe.dom.unfreeze()
                            ]);
                        })
                    }
                },
            },
            parent: this.$customer_section.find('.customer-field'),
            render_input: true,
        });
        this.customer_field.toggle_label(false);
    }

    make_served_by_selector() {
        this.$served_by_section.html(`
			<div class="served-by-field"></div>
		`);
        const me = this;
        const query = {query: 'bbb.bbb.controllers.queries.served_by_query'};

        this.served_by_field = frappe.ui.form.make_control({
            df: {
                label: __('Served By'),
                fieldtype: 'Link',
                options: 'Served By',
                placeholder: __('Search by name, location'),
                get_query: () => query,
                onchange: function () {
                    if (this.value) {
                        frappe.dom.freeze();
                        const frm = me.events.get_frm();
                        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'served_by', this.value);
                        frm.script_manager.trigger('served_by', frm.doc.doctype, frm.doc.name);
                        frappe.run_serially([
                            // () => me.check_out_validation(true),
                            () => me.served_by_info = {'served_by': this.value},
                            // () => me.events.set_cache_data({'pos_served_by': this.value}),
                            () => me.update_served_by_section(),
                            () => frappe.dom.unfreeze()
                        ]);
                    }
                },
            },
            parent: this.$served_by_section.find('.served-by-field'),
            render_input: true,
        });
        this.served_by_field.toggle_label(false);
    }

    make_pos_profile() {
        const frm = this.events.get_frm();
        const html = `
        <div class="label"><span class="indicator-pill whitespace-nowrap blue"><span></span id="pos-profile-label">${frm.doc.pos_profile}</span></div>
    `
        this.$pos_profile_section.html(`
            <div class="pos-profile-field">${html}</div>
        `);
    }
    make_discount_price_selector() {
        const me = this;
        const html = `
        <div class="ignore-pricing-rule-field">
            <div class="frappe-control input-max-width" data-fieldtype="Select">
                <div class="form-group"><div class="clearfix">
                    <label class="control-label hide" style="padding-right: 0px;">Ignore Discount</label>
                </div>
                <div class="control-input-wrapper">
                    <div class="control-input flex align-center">
                        <select type="text" id="ignore_pricing_rule" autocomplete="off" class="input-with-feedback form-control ellipsis" maxlength="140" data-fieldtype="Select" placeholder="Ignore Discount">
                            <option></option>
                            <option value="Yes">Yes</option>
                            <option value="No">No</option>
                       </select>
                    <div class="select-icon "><svg class="icon  icon-sm" style=""><use class="" href="#icon-select"></use></svg>
                </div>
                <div class="placeholder ellipsis text-extra-muted "><span>Ignore Discount</span></div>
            </div>
            <div class="control-value like-disabled-input" style="display: none;"></div>
            <p class="help-box small text-muted"></p>
        </div>
        `
        this.$pricing_rule_discount_section.html(`
			<div class="ignore-pricing-rule-field">${html}</div>
		`);
        $('#ignore_pricing_rule').on('change', function (){
            frappe.run_serially([
                // () => me.ignore_pricing_rule = this.value,
                () => me.update_pricing_rule_discount_section(this.value),
                // () => me.events.set_cache_data({'pos_ignore_pricing_rule': this.value}),
                () => me.ignore_pricing_discount(me, this.value),
                () => frappe.dom.unfreeze(),
            ]);
        })
        // this.price_rule_ignore_discount_field = frappe.ui.form.make_control({
        //     df: {
        //         label: __('Ignore Discount'),
        //         fieldtype: 'Select',
        //         options: ["", "Yes", "No"],
        //         placeholder: __('Ignore Discount'),
        //         default: 'No',
        //         onchange: function () {
        //             console.log(this.value)
        //             if (this.value) {
        //                 frappe.dom.freeze();
        //                 console.log("called ..")
        //                 const frm = me.events.get_frm();
        //                 frappe.run_serially([
        //                     // () => me.ignore_pricing_rule = this.value,
        //                     () => me.update_pricing_rule_discount_section(this.value),
        //                     // () => me.events.set_cache_data({'pos_ignore_pricing_rule': this.value}),
        //                     () => me.ignore_pricing_discount(me, this.value),
        //                     () => frappe.dom.unfreeze(),
        //                 ]);
        //
        //             }
        //         },
        //     },
        //     parent: this.$pricing_rule_discount_section.find('.ignore-pricing-rule-field'),
        //     render_input: true,
        // });
        // this.price_rule_ignore_discount_field.toggle_label(false);
    }


    make_menu_dropdown() {
        // this.events.toggle_recent_order();
        this.$menu_section.html(`
               <div class="menu-dropdown-field">
                    <div class="menu-btn-group">
                        <button type="button" class="btn btn-default icon-btn" data-toggle="dropdown" aria-expanded="false" title=""
                                data-original-title="Menu"><span>         <span class="menu-btn-group-label" data-label="">          <svg
                                class="icon icon-sm">           <use xlink:href="#icon-dot-horizontal">           </use>          </svg>         </span>        </span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-right" role="menu">
                            <li>
                                <a class="grey-link dropdown-item" href="#" id="check_item_stock">
                                    <span class="menu-item-label" data-label="Check Item Stock"><span class="alt-underline">C</span>heck Item Stock</span>
                                </a>
                            </li>
                            <li>
                                <a class="grey-link dropdown-item" href="#" id="add_damaged_product">
                                    <span class="menu-item-label" data-label=""><span class="alt-underline">A</span>dd Damaged Product</span>
                                </a>
                            </li>
                            <li>
                                <a class="grey-link dropdown-item" href="#" id="reset_cart">
                    
                                    <span class="menu-item-label" data-label="Reset Cart"><span class="alt-underline">R</span>eset Cart</span>
                                </a>
                            </li>
                            <li>
                                <a class="grey-link dropdown-item toggle_recent_order-1" href="#" id="toggle_recent_order">
                    
                                    <span class="menu-item-label" data-label="Toggle Sidebar"><span class="alt-underline">T</span>oggle Recent Orders</span>
                                </a>
                            </li>
                            <li>
                                <a class="grey-link dropdown-item" href="#" id="save_draft_invoice">
                    
                                    <span class="menu-item-label" data-label="Toggle Sidebar"><span class="alt-underline">S</span>ave as Draft</span>
                                </a>
                            </li>
                            <li>
                                <a class="grey-link dropdown-item" href="#" id="close_pos">
                    
                                    <span class="menu-item-label" data-label="Toggle Sidebar"><span class="alt-underline">C</span>lose the POS</span>
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
		`);
        const me = this;

        // this.page.add_menu_item(__("Open Form View"), this.open_form_view.bind(this), false, 'Ctrl+F');
        //
        // this.page.add_menu_item(__("Toggle Recent Orders"), this.toggle_recent_order.bind(this), false, 'Ctrl+O');
        //
        // this.page.add_menu_item(__("Save as Draft"), this.save_draft_invoice.bind(this), false, 'Ctrl+S');
        //
        // this.page.add_menu_item(__('Close the POS'), this.close_pos.bind(this), false, 'Shift+Ctrl+C');

        // this.page.add_menu_item(__("Stock"), function() {
        //     console.log("Stock")
        // })
    }

    fetch_discount_details(ignore_pricing_rule) {
        return new Promise((resolve) => {
            if(ignore_pricing_rule === 1){
                this.ignore_pricing_rule = "Yes"
            }else{
                this.ignore_pricing_rule = "No"
            }
            resolve();
        });
    }

    fetch_served_by_details(served_by) {
        if (served_by) {
            return new Promise((resolve) => {
                frappe.db.get_value('Served By', served_by, ["served_by_name"]).then(({message}) => {
                    this.served_by_info = {...message, served_by};
                    resolve();
                });
            });
        } else {
            return new Promise((resolve) => {
                this.served_by_info = {}
                resolve();
            });
        }
    }

    fetch_customer_details(customer) {
        if (customer) {
            return new Promise((resolve) => {
                frappe.db.get_value('Customer', customer, ["email_id", "mobile_no", "image", "loyalty_program", "customer_name"]).then(({message}) => {
                    const {loyalty_program} = message;
                    // if loyalty program then fetch loyalty points too
                    if (loyalty_program) {
                        frappe.call({
                            method: "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_loyalty_program_details_with_points",
                            args: {customer, loyalty_program, "silent": true},
                            callback: (r) => {
                                const {loyalty_points, conversion_factor} = r.message;
                                if (!r.exc) {
                                    this.customer_info = {...message, customer, loyalty_points, conversion_factor};

                                    resolve();
                                }
                            }
                        });
                    } else {
                        this.customer_info = {...message, customer};
                        resolve();
                    }
                });
            });
        } else {
            return new Promise((resolve) => {
                this.customer_info = {}
                resolve();
            });
        }
    }

    show_discount_control() {
        this.$add_discount_elem.css({'padding': '0px', 'border': 'none'});
        this.$add_discount_elem.html(
            `<div class="add-discount-field"></div>`
        );
        const me = this;
        const frm = me.events.get_frm();
        let discount = frm.doc.additional_discount_percentage;

        this.discount_field = frappe.ui.form.make_control({
            df: {
                label: __('Discount'),
                fieldtype: 'Data',
                placeholder: (discount ? discount + '%' : __('Enter discount percentage.')),
                input_class: 'input-xs',
                onchange: function () {
                frappe.run_serially([
                        ()=> me.update_additional_discount(me, this, frm, 'additional_discount_percentage'),
                    ])

                    const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? frm.doc.grand_total : frm.doc.rounded_total;
                    me.events.set_5_basis_rounded_total(grand_total)
                    // console.log(me.events.base_rounded_total);
                    // console.log($('.payment_amount_value').html(format_currency(me.events.base_rounded_total, frm.doc.currency)));
                },

            },
            parent: this.$add_discount_elem.find('.add-discount-field'),
            render_input: true,
        });
        this.discount_field.toggle_label(false);
        this.discount_field.set_focus();
    }

    show_discount_amount_control() {
        this.$add_discount_amount_elem.css({'padding': '0px', 'border': 'none'});
        this.$add_discount_amount_elem.html(
            `<div class="add-discount-amount-field"></div>`
        );
        const me = this;
        const frm = me.events.get_frm();
        let discount = frm.doc.discount_amount;

        this.discount_amount_field = frappe.ui.form.make_control({
            df: {
                label: __('Discount Amount'),
                fieldtype: 'Data',
                placeholder: (discount ? discount : __('Enter discount amount.')),
                input_class: 'input-xs',
                onchange: function () {
                frappe.run_serially([
                        ()=> me.update_additional_discount(me, this, frm, 'discount_amount'),
                    ])
                //
                //     const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? frm.doc.grand_total : frm.doc.rounded_total;
                //     me.events.set_5_basis_rounded_total(grand_total)
                //     console.log(me.events.base_rounded_total);
                //     console.log($('.payment_amount_value').html(format_currency(me.events.base_rounded_total, frm.doc.currency)));
                },

            },
            parent: this.$add_discount_amount_elem.find('.add-discount-amount-field'),
            render_input: true,
        });
        this.discount_amount_field.toggle_label(false);
        this.discount_amount_field.set_focus();
    }

    update_additional_discount(me, discount_section, frm, field_name){
        if(field_name == 'additional_discount_percentage'){
            if (flt(discount_section.value) != 0) {
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, field_name, flt(discount_section.value));
                me.hide_discount_control(discount_section.value);
                setTimeout(function (){
                    me.hide_discount_amount_control(frm.doc.discount_amount);
                }, 500)
            } else {
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, field_name, 0);
                me.$add_discount_elem.css({
                    'border': '1px dashed var(--gray-500)',
                    'padding': 'var(--padding-sm) var(--padding-md)'
                });
                me.$add_discount_elem.html(`${me.get_discount_icon()} Add Discount`);
                me.discount_field = undefined;
            }
        }else{
            if (discount_section !==0) {
                this.$add_discount_elem.css({'padding': '0px', 'border': 'none'});
                this.$add_discount_elem.html(
                    `<div class="add-discount-field"></div>`
                );
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, field_name, parseFloat(discount_section.value));
                me.hide_discount_amount_control(discount_section.value);
            } else {
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, field_name, 0);
                me.$add_discount_amount_elem.css({
                    'border': '1px dashed var(--gray-500)',
                    'padding': 'var(--padding-sm) var(--padding-md)'
                });
                me.$add_discount_amount_elem.html(`${me.get_discount_icon()} Add Discount`);
                me.discount_amount_field = undefined;
            }
        }

    }

    hide_discount_control(discount) {
        if (!discount) {
            this.$add_discount_elem.css({'padding': '0px', 'border': 'none'});
            this.$add_discount_elem.html(
                `<div class="add-discount-field"></div>`
            );
        } else {
            this.$add_discount_elem.css({
                'border': '1px dashed var(--dark-green-500)',
                'padding': 'var(--padding-sm) var(--padding-md)'
            });
            this.$add_discount_elem.html(
                `<div class="edit-discount-btn">
					${this.get_discount_icon()} ${String(discount).bold()}% discount applied
				</div>`
            );
        }
    }
    hide_discount_amount_control(discount) {
        if (!discount) {
            this.$add_discount_amount_elem.css({'padding': '0px', 'border': 'none'});
            this.$add_discount_amount_elem.html(
                `<div class="add-discount-amount-field"></div>`
            );
        } else {
            this.$add_discount_amount_elem.css({
                'border': '1px dashed var(--dark-green-500)',
                'padding': 'var(--padding-sm) var(--padding-md)'
            });
            this.$add_discount_amount_elem.html(
                `<div class="edit-discount-amount-btn">
					${this.get_discount_icon()} ${String(discount).bold()}&nbsp;TK discount applied
				</div>`
            );
        }
    }

    update_pricing_rule_discount_section(ignore_pricing_rule=undefined) {
        const me = this;
        if(ignore_pricing_rule == undefined){
            ignore_pricing_rule = this.ignore_pricing_rule;
        }
        this.$pricing_rule_discount_section.html(
            `<div class="pricing-discount-details">
                <div class="pricing-discount-display">
                    <div class="pricing-discount-desc">
                        <div class="pricing-discount-name">${ignore_pricing_rule}</div>
                    </div>
                    <div class="reset-ignore_pricing-rule-btn" reset-ignore-pricing-rule-attr="" data-pricing-discount="${escape(ignore_pricing_rule)}">
                        <svg width="32" height="32" viewBox="0 0 14 14" fill="none">
                            <path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
                        </svg>
                    </div>
                </div>
            </div>`
        );
    }

    update_served_by_section() {
        const frm = this.events.get_frm();
        let style=''
        if(frm.doc.is_return){
            style = "display: none;";
        }

        const {served_by} = this.served_by_info || {};
        if (served_by) {
            let served_by_name = served_by.split('-')[0]
            this.$served_by_section.html(
                `<div class="served-by-details">
					<div class="served-by-display">
						<div class="served-by-name-desc">
							<div class="served-by-name">${served_by_name}</div>
						</div>
						<div class="reset-served-by-btn" reset-served-attr="" data-served-by="${escape(served_by)}" style="${style}">
							<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
								<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
							</svg>
						</div>
					</div>
				</div>`
            );
        } else {
            this.reset_served_by_selector();
        }

    }

    update_customer_section() {
        const frm = this.events.get_frm();
        let style=''
        if(frm.doc.is_return){
            style = "display: none;";
        }
        const {customer, customer_name, email_id = '', mobile_no = '', image} = this.customer_info || {};
        if (customer) {
            this.$customer_section.html(
                `<div class="customer-details">
					<div class="customer-display">
						<div class="customer-name-desc">
							<div class="customer-name">${customer_name}</div>
						</div>
						<div class="reset-customer-btn" reset-customer-attr="" data-customer="${escape(customer)}" style="${style}">
							<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
								<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
							</svg>
						</div>
					</div>
				</div>`
            );
        } else {
            // reset customer selector
            this.reset_customer_selector();
        }

        function get_customer_description() {
            if (!email_id && !mobile_no) {
                return `<div class="customer-desc">Click to add email / phone</div>`;
            } else if (email_id && !mobile_no) {
                return `<div class="customer-desc">${email_id}</div>`;
            } else if (mobile_no && !email_id) {
                return `<div class="customer-desc">${mobile_no}</div>`;
            } else {
                return `<div class="customer-desc">${email_id} - ${mobile_no}</div>`;
            }
        }

    }

    get_customer_image() {
        const {customer, image} = this.customer_info || {};
        if (image) {
            return `<div class="customer-image"><img src="${image}" alt="${image}""></div>`;
        } else {
            return `<div class="customer-image customer-abbr">${frappe.get_abbr(customer)}</div>`;
        }
    }

    update_totals_section(frm) {
        if (!frm) frm = this.events.get_frm();

        this.render_net_total(frm.doc.net_total);
        const grand_total = frm.doc.grand_total;
        //this.events.set_5_basis_rounded_total(frm.doc.grand_total);
        //let base_rounded_total = this.events.get_5_basis_rounded_total();
        //this.events.set_initial_paid_amount(frm.doc.rounded_total);
        this.render_grand_total(grand_total);
        // this.render_rounded_total(base_rounded_total);
        this.render_taxes(frm.doc.taxes)
        this.update_item_cart_total_section(frm)
        this.render_rounded_total(frm.doc)

    }

    render_net_total(value) {
        const currency = this.events.get_frm().doc.currency;
        this.$totals_section.find('.net-total-container').html(
            `<div>Net Total</div><div>${format_currency(value, currency)}</div>`
        )

        this.$numpad_section.find('.numpad-net-total').html(
            `<div>Net Total: <span>${format_currency(value, currency)}</span></div>`
        );
    }

    render_grand_total(value) {
        const currency = this.events.get_frm().doc.currency;
        this.$totals_section.find('.grand-total-container').html(
            `<div>Grand Total</div><div>${format_currency(value, currency)}</div>`
        )

        this.$numpad_section.find('.numpad-grand-total').html(
            `<div>Grand Total: <span>${format_currency(value, currency)}</span></div>`
        );
    }
    // rabi
    render_rounded_total(doc) {
        const currency = this.events.get_frm().doc.currency;
        let adjustment = doc.rounded_total - doc.grand_total;
        this.$totals_section.find('.rounded-total-container').html(
            `<div>Rounded Total</div><div>${format_currency(doc.rounded_total, currency)}</div>`
        )
        this.$totals_section.find('.rounding-adjustment-container').html(
            `<div>Rounding Adjustment</div><div>${format_currency(adjustment, currency)}</div>`
        )
        this.$totals_section.find('.special-discount-container').html(
            `<div>Special Discount</div><div>${format_currency(doc.discount_amount, currency)}</div>`
        )
    }

    render_taxes(taxes) {
        if (taxes.length) {
            const currency = this.events.get_frm().doc.currency;
            const taxes_html = taxes.map(t => {
                const description = /[0-9]+/.test(t.description) ? t.description : `${t.description} @ ${t.rate}%`;
                return `<div class="tax-row">
					<div class="tax-label">${description}</div>
					<div class="tax-value">${format_currency(t.tax_amount_after_discount_amount, currency)}</div>
				</div>`;
            }).join('');
            this.$totals_section.find('.taxes-container').css('display', 'flex').html(taxes_html);
        } else {
            this.$totals_section.find('.taxes-container').css('display', 'none').html('');
        }
    }

    get_cart_item({name}) {
        const item_selector = `.cart-item-wrapper[data-row-name="${escape(name)}"]`;
        return this.$cart_items_wrapper.find(item_selector);
    }

    get_item_from_frm(item) {
        const doc = this.events.get_frm().doc;
        return doc.items.find(i => i.name == item.name);
    }

    update_item_html(item, remove_item) {
        const $item = this.get_cart_item(item);

        if (remove_item) {
            $item && $item.next().remove() && $item.remove();
        } else {
            const item_row = this.get_item_from_frm(item);

            this.render_cart_item(item_row, $item);
        }

        const no_of_cart_items = this.$cart_items_wrapper.find('.cart-item-wrapper').length;
        this.highlight_checkout_btn(no_of_cart_items > 0);
        if(no_of_cart_items > 0){
            $('.reset-ignore_pricing-rule-btn').css('display', 'none');
            // $('.reset-customer-btn').css('display', 'none');
        }else if(no_of_cart_items < 1){
            $('.reset-ignore_pricing-rule-btn').css('display', 'flex');
            // $('.reset-customer-btn').css('display', 'flex');
        }

        this.update_empty_cart_section(no_of_cart_items);
        this.update_5_basis_rounded()

        // console.log(frm);

    }

    update_5_basis_rounded(){
        // rounded_total : M rounds to 5 basis ( 12.49 will be 10 and 12.5 will  be 15) rabi
        const frm = this.events.get_frm()
        let grand_total = frm.doc.grand_total;
        let rounded_total = this.events.get_5_basis_rounded(frm.doc.grand_total)
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'rounding_adjustment', rounded_total - grand_total)
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'rounded_total', rounded_total)
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'base_rounded_total', null)
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'base_paid_amount', null)
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'base_change_amount', null)
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'base_rounding_adjustment', null)
    }
    render_cart_item(item_data, $item_to_update) {
        const frm = this.events.get_frm()
        let items = frm.doc.items
        const currency = frm.doc.currency;
        const me = this;


        if (!$item_to_update.length) {
            this.$cart_items_wrapper.append(
                `<div class="cart-item-wrapper" data-row-name="${escape(item_data.name)}"></div>
				<div class="seperator"></div>`
            )
            $item_to_update = this.get_cart_item(item_data);
        }

        $item_to_update.html(
            `<div class="item-name-desc">
                <div class="item-image-name-dec">
			        <div class="item-image" docname="${item_data.name}">
						<img
							onerror="cur_pos.cart.handle_broken_image(this)"
							src="/files/cross-icon.png" alt=""">
					</div>
			        <div class="item-name" >
					    <span>${frappe.ellipsis(item_data.item_name, 500)}</span>
				    </div>
                </div>
                ${get_rate_discount_html()}
			</div>`
        )

        set_dynamic_rate_header_width();

        function set_dynamic_rate_header_width() {
            const rate_cols = Array.from(me.$cart_items_wrapper.find(".item-row-amount"));
            me.$cart_header.find(".rate-amount-header").css("width", "");
            me.$cart_items_wrapper.find(".item-row-amount").css("width", "");
            let max_width = rate_cols.reduce((max_width, elm) => {
                if ($(elm).width() > max_width)
                    max_width = $(elm).width();
                return max_width;
            }, 0);

            max_width += 1;
            if (max_width == 1) max_width = "";

            me.$cart_header.find(".rate-amount-header").css("width", max_width);
            me.$cart_items_wrapper.find(".item-row-amount").css("width", max_width);
        }

        function get_rate_discount_html() {
            // if (item_data.rate && item_data.amount && item_data.rate !== item_data.amount) {
            // 	return `
            // 		<div class="item-qty-rate">
            // 			<div class="item-qty"><span>${item_data.qty || 0}</span></div>
            // 			<div class="item-row-amount">
            // 				<div class="item-rate">${format_currency(item_data.amount, currency)}</div>
            // 				<div class="item-amount">${format_currency(item_data.rate, currency)}</div>
            // 			</div>
            // 		</div>`
            // } else {


            // frappe.db.get_value('Item', item_data.item_code, 'standard_rate')
            // 	.then(r => {
            // 		// item_mrp = r.message.standard_rate;
            // 	})
            return `
					<div class="item-row-mrp"><span>${item_data.price_list_rate || 0}</span></div>
					<div class="item-row-disc"><span>${(item_data.price_list_rate - item_data.rate) || 0}</span></div>
					<div class="item-row-rate"><span>${item_data.rate || 0}</span></div>
					<div class="item-row-qty"><!--<span>${item_data.qty || 0}</span>-->
					<input class="form-control item_qty" type="text" value="${item_data.qty || 0}" item_code="${item_data.item_code}" docname="${item_data.name}" style="width: 50px;text-align: center;" free_item="${item_data.free_item_rules || 'undefined'}">
					</div>
					
					<!--<div class="item-row-damaged-cost">
					<input class="form-control damaged-cost" type="text" value="${item_data.qty || 0}" item_code="${item_data.item_code}" docname="${item_data.name}" style="width: 50px;text-align: center;">
					</div> -->
					<div class="item-row-amount"><span>${item_data.amount || 0}</span></div>`
            // }
        }

        function get_description_html() {
            if (item_data.description) {
                if (item_data.description.indexOf('<div>') != -1) {
                    try {
                        item_data.description = $(item_data.description).text();
                    } catch (error) {
                        item_data.description = item_data.description.replace(/<div>/g, ' ').replace(/<\/div>/g, ' ').replace(/ +/g, ' ');
                    }
                }
                item_data.description = frappe.ellipsis(item_data.description, 45);
                return `<div class="item-desc">${item_data.description}</div>`;
            }
            return ``;
        }

        function get_item_image_html() {
            const {image, item_name} = item_data;
            if (!me.hide_images && image) {
                return `
					<div class="item-image">
						<img
							onerror="cur_pos.cart.handle_broken_image(this)"
							src="${image}" alt="${frappe.get_abbr(item_name)}"">
					</div>`;
            } else {
                return `<div class="item-image item-abbr">${frappe.get_abbr(item_name)}</div>`;
            }
        }

        $(".item_qty").on('change', function (){

            let item_qty = $(this).val();

            if(item_qty){
                if(/^-?\d+$/.test(item_qty) === true){

                    let docname = $(this).attr('docname');
                    let item_code = $(this).attr('item_code');
                    let free_item = $(this).attr('free_item');
                    if(free_item !== 'undefined'){
                        frappe.dom.unfreeze();
                        frappe.show_alert({
                            message: __('Item qty should be 1 for applied promotion'),
                            indicator: 'orange'
                        });
                        frappe.utils.play_sound("error");
                        $(this).val(1)
                        return
                    }
                    frappe.model.set_value("POS Invoice Item", docname, 'qty', item_qty)
                        .then(function (){
                            if(frm.doc.is_return){
                                frappe.call({
                                    method: "bbb.bbb.controllers.utils.apply_item_pricing_rule",
                                    args: {"return_against": frm.doc.return_against, 'item_code': item_code},
                                    callback: (r) => {
                                        frappe.model.set_value("POS Invoice Item", docname, 'margin_type', r.message.margin_type)
                                        frappe.model.set_value("POS Invoice Item", docname, 'discount_percentage', r.message.discount_percentage)
                                        // console.log(frm.doc.items)
                                    }
                                })
                            }
                        })

                }else{
                    const message = __('Item quantity must be a number');
                    frappe.show_alert({
                        indicator: 'red',
                        message: message
                    });

                    $(this).val(item_qty)
                }
            }
        });
        $(".item-image").on('click', function (){
            if($('.edit-cart-btn').is(":visible") === true) return;
            //rabi
            frappe.dom.freeze();
            let docname = $(this).attr('docname');
            // console.log(docname);
            let doctype = "POS Invoice Item"
            let item = frappe.model.get_doc(doctype, docname);
            const $item = me.get_cart_item(item);
            // frappe.model.set_value(doctype, docname, 'qty', 0)
            frappe.run_serially([
                () => frappe.model.set_value(doctype, docname, 'rate', 0),
                () => frappe.model.clear_doc(doctype, docname),
                () => $item && $item.next().remove() && $item.remove(),
                () => me.events.check_free_item_pricing_rules(),
                // () => frappe.model.clear_doc(doctype, docname),
                () => me.toggle_ignore_pricing_rule_button(),
                () => frappe.dom.unfreeze()
            ])
        });
    }
    toggle_ignore_pricing_rule_button(){
        const no_of_cart_items = this.$cart_items_wrapper.find('.cart-item-wrapper').length;
        if(no_of_cart_items>0){
            $('.reset-ignore_pricing-rule-btn').css('display', 'none');
            // $('.reset-customer-btn').css('display', 'none');
        }else if(no_of_cart_items < 1){
            $('.reset-ignore_pricing-rule-btn').css('display', 'flex');
            // $('.reset-customer-btn').css('display', 'flex');
        }
    }
    handle_broken_image($img) {
        const item_abbr = $($img).attr('alt');
        $($img).parent().replaceWith(`<div class="item-image item-abbr">${item_abbr}</div>`);
    }

    update_selector_value_in_cart_item(selector, value, item) {
        const $item_to_update = this.get_cart_item(item);
        $item_to_update.attr(`data-${selector}`, escape(value));
    }

    toggle_checkout_btn(show_checkout) {
        if (show_checkout) {
            this.$totals_section.find('.checkout-btn').css('display', 'flex');
            this.$totals_section.find('.edit-cart-btn').css('display', 'none');
            this.$add_discount_elem.find('input').removeAttr('disabled')
            this.$add_discount_amount_elem.find('input').removeAttr('disabled')
        } else {
            this.$totals_section.find('.checkout-btn').css('display', 'none');
            this.$totals_section.find('.edit-cart-btn').css('display', 'flex');
        }
    }

    highlight_checkout_btn(toggle) {
        if (toggle) {
            this.$add_discount_elem.css('display', 'flex');
            this.$add_discount_amount_elem.css('display', 'flex');
            this.$cart_container.find('.checkout-btn').css({
                'background-color': 'var(--blue-500)'
            });
        } else {
            this.$add_discount_elem.css('display', 'none');
            this.$add_discount_amount_elem.css('display', 'none');
            this.$cart_container.find('.checkout-btn').css({
                'background-color': 'var(--blue-200)'
            });

        }
    }

    update_empty_cart_section(no_of_cart_items) {
        const $no_item_element = this.$cart_items_wrapper.find('.no-item-wrapper');

        // if cart has items and no item is present
        no_of_cart_items > 0 && $no_item_element && $no_item_element.remove() && this.$cart_header.css('display', 'flex');

        no_of_cart_items === 0 && !$no_item_element.length && this.make_no_items_placeholder();
    }

    on_numpad_event($btn) {
        const current_action = $btn.attr('data-button-value');
        const action_is_field_edit = ['qty', 'discount_percentage', 'rate'].includes(current_action);
        const action_is_allowed = action_is_field_edit ? (
            (current_action == 'rate' && this.allow_rate_change) ||
            (current_action == 'discount_percentage' && this.allow_discount_change) ||
            (current_action == 'qty')) : true;

        const action_is_pressed_twice = this.prev_action === current_action;
        const first_click_event = !this.prev_action;
        const field_to_edit_changed = this.prev_action && this.prev_action != current_action;

        if (action_is_field_edit) {
            if (!action_is_allowed) {
                const label = current_action == 'rate' ? 'Rate'.bold() : 'Discount'.bold();
                const message = __('Editing {0} is not allowed as per POS Profile settings', [label]);
                frappe.show_alert({
                    indicator: 'red',
                    message: message
                });
                frappe.utils.play_sound("error");
                return;
            }

            if (first_click_event || field_to_edit_changed) {
                this.prev_action = current_action;
            } else if (action_is_pressed_twice) {
                this.prev_action = undefined;
            }
            this.numpad_value = '';

        } else if (current_action === 'checkout') {
            this.prev_action = undefined;
            this.toggle_item_highlight();
            this.events.numpad_event(undefined, current_action);
            return;
        } else if (current_action === 'remove') {
            this.prev_action = undefined;
            this.toggle_item_highlight();
            this.events.numpad_event(undefined, current_action);
            return;
        } else {
            this.numpad_value = current_action === 'delete' ? this.numpad_value.slice(0, -1) : this.numpad_value + current_action;
            this.numpad_value = this.numpad_value || 0;
        }

        const first_click_event_is_not_field_edit = !action_is_field_edit && first_click_event;

        if (first_click_event_is_not_field_edit) {
            frappe.show_alert({
                indicator: 'red',
                message: __('Please select a field to edit from numpad')
            });
            frappe.utils.play_sound("error");
            return;
        }

        if (flt(this.numpad_value) > 100 && this.prev_action === 'discount_percentage') {
            frappe.show_alert({
                message: __('Discount cannot be greater than 100%'),
                indicator: 'orange'
            });
            frappe.utils.play_sound("error");
            this.numpad_value = current_action;
        }

        this.highlight_numpad_btn($btn, current_action);
        this.events.numpad_event(this.numpad_value, this.prev_action);
    }

    highlight_numpad_btn($btn, curr_action) {
        const curr_action_is_highlighted = $btn.hasClass('highlighted-numpad-btn');
        const curr_action_is_action = ['qty', 'discount_percentage', 'rate', 'done'].includes(curr_action);

        if (!curr_action_is_highlighted) {
            $btn.addClass('highlighted-numpad-btn');
        }
        if (this.prev_action === curr_action && curr_action_is_highlighted) {
            // if Qty is pressed twice
            $btn.removeClass('highlighted-numpad-btn');
        }
        if (this.prev_action && this.prev_action !== curr_action && curr_action_is_action) {
            // Order: Qty -> Rate then remove Qty highlight
            const prev_btn = $(`[data-button-value='${this.prev_action}']`);
            prev_btn.removeClass('highlighted-numpad-btn');
        }
        if (!curr_action_is_action || curr_action === 'done') {
            // if numbers are clicked
            setTimeout(() => {
                $btn.removeClass('highlighted-numpad-btn');
            }, 200);
        }
    }

    toggle_numpad(show) {
        if (show) {
            this.$totals_section.css('display', 'none');
            this.$numpad_section.css('display', 'flex');
        } else {
            this.$totals_section.css('display', 'flex');
            this.$numpad_section.css('display', 'none');
        }
        this.reset_numpad();
    }

    reset_numpad() {
        this.numpad_value = '';
        this.prev_action = undefined;
        this.$numpad_section.find('.highlighted-numpad-btn').removeClass('highlighted-numpad-btn');
    }

    toggle_numpad_field_edit(fieldname) {
        if (['qty', 'discount_percentage', 'rate'].includes(fieldname)) {
            this.$numpad_section.find(`[data-button-value="${fieldname}"]`).click();
        }
    }

    toggle_customer_info(show) {
        if (show) {
            const {customer} = this.customer_info || {};

            this.$cart_container.css('display', 'none');
            this.$customer_section.css({
                'height': '100%',
                'padding-top': '0px'
            });
            this.$customer_section.find('.customer-details').html(
                `<div class="header">
					<div class="label">Contact Details</div>
					<div class="close-details-btn">
						<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
							<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
						</svg>
					</div>
				</div>
				<div class="customer-display">
					${this.get_customer_image()}
					<div class="customer-name-desc">
						<div class="customer-name">${customer}</div>
						<div class="customer-desc"></div>
					</div>
				</div>
				<div class="customer-fields-container">
					<div class="email_id-field"></div>
					<div class="mobile_no-field"></div>
					<div class="loyalty_program-field"></div>
					<div class="loyalty_points-field"></div>
				</div>
				<div class="transactions-label">Recent Transactions</div>`
            );
            // transactions need to be in diff div from sticky elem for scrolling
            this.$customer_section.append(`<div class="customer-transactions"></div>`);

            this.render_customer_fields();
            this.fetch_customer_transactions();

        } else {
            this.$cart_container.css('display', 'flex');
            this.$customer_section.css({
                'height': '',
                'padding-top': ''
            });

            this.update_customer_section();
        }
    }

    render_customer_fields() {
        const $customer_form = this.$customer_section.find('.customer-fields-container');

        const dfs = [{
            fieldname: 'email_id',
            label: __('Email'),
            fieldtype: 'Data',
            options: 'email',
            placeholder: __("Enter customer's email")
        }, {
            fieldname: 'mobile_no',
            label: __('Phone Number'),
            fieldtype: 'Data',
            placeholder: __("Enter customer's phone number")
        }, {
            fieldname: 'loyalty_program',
            label: __('Loyalty Program'),
            fieldtype: 'Link',
            options: 'Loyalty Program',
            placeholder: __("Select Loyalty Program")
        }, {
            fieldname: 'loyalty_points',
            label: __('Loyalty Points'),
            fieldtype: 'Data',
            read_only: 1
        }];

        const me = this;
        dfs.forEach(df => {
            this[`customer_${df.fieldname}_field`] = frappe.ui.form.make_control({
                df: {
                    ...df,
                    onchange: handle_customer_field_change,
                },
                parent: $customer_form.find(`.${df.fieldname}-field`),
                render_input: true,
            });
            this[`customer_${df.fieldname}_field`].set_value(this.customer_info[df.fieldname]);
        })

        function handle_customer_field_change() {
            const current_value = me.customer_info[this.df.fieldname];
            const current_customer = me.customer_info.customer;

            if (this.value && current_value != this.value && this.df.fieldname != 'loyalty_points') {
                frappe.call({
                    method: 'erpnext.selling.page.point_of_sale.point_of_sale.set_customer_info',
                    args: {
                        fieldname: this.df.fieldname,
                        customer: current_customer,
                        value: this.value
                    },
                    callback: (r) => {
                        if (!r.exc) {
                            me.customer_info[this.df.fieldname] = this.value;
                            frappe.show_alert({
                                message: __("Customer contact updated successfully."),
                                indicator: 'green'
                            });
                            frappe.utils.play_sound("submit");
                        }
                    }
                });
            }
        }
    }

    fetch_customer_transactions() {
        frappe.db.get_list('POS Invoice', {
            filters: {customer: this.customer_info.customer, docstatus: 1},
            fields: ['name', 'grand_total', 'status', 'posting_date', 'posting_time', 'currency'],
            limit: 20
        }).then((res) => {
            const transaction_container = this.$customer_section.find('.customer-transactions');

            if (!res.length) {
                transaction_container.html(
                    `<div class="no-transactions-placeholder">No recent transactions found</div>`
                )
                return;
            }
            ;

            const elapsed_time = moment(res[0].posting_date + " " + res[0].posting_time).fromNow();
            this.$customer_section.find('.customer-desc').html(`Last transacted ${elapsed_time}`);

            res.forEach(invoice => {
                const posting_datetime = moment(invoice.posting_date + " " + invoice.posting_time).format("Do MMMM, h:mma");
                let indicator_color = {
                    'Paid': 'green',
                    'Draft': 'red',
                    'Return': 'gray',
                    'Consolidated': 'blue'
                };

                transaction_container.append(
                    `<div class="invoice-wrapper" data-invoice-name="${escape(invoice.name)}">
						<div class="invoice-name-date">
							<div class="invoice-name">${invoice.name}</div>
							<div class="invoice-date">${posting_datetime}</div>
						</div>
						<div class="invoice-total-status">
							<div class="invoice-total">
								${format_currency(invoice.grand_total, invoice.currency, 0) || 0}
							</div>
							<div class="invoice-status">
								<span class="indicator-pill whitespace-nowrap ${indicator_color[invoice.status]}">
									<span>${invoice.status}</span>
								</span>
							</div>
						</div>
					</div>
					<div class="seperator"></div>`
                )
            });
        });
    }

    attach_refresh_field_event(frm) {
        $(frm.wrapper).off('refresh-fields');
        $(frm.wrapper).on('refresh-fields', () => {
            if (frm.doc.items.length) {
                frm.doc.items.forEach(item => {
                    this.update_item_html(item);
                });
            }
            this.update_totals_section(frm);
        });
    }
    update_cached_data(cached_data){
        const frm = this.events.get_frm();
        const pos_ignore_pricing_rule = cached_data['pos_ignore_pricing_rule'] ? cached_data['pos_ignore_pricing_rule'] : "No"
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', cached_data['pos_customer']);
        frm.script_manager.trigger('customer', frm.doc.doctype, frm.doc.name).then(() => {
                frappe.run_serially([
                () => this.fetch_customer_details(cached_data['pos_customer']),
                () => this.events.customer_details_updated(this.customer_info),
                () => this.update_customer_section(),
                () => this.update_totals_section(),
            ]);
        })
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'served_by', cached_data['pos_served_by']);
        frm.script_manager.trigger('served_by', frm.doc.doctype, frm.doc.name).then(() => {
            frappe.run_serially([
                () => this.served_by_info = {'served_by': cached_data['pos_served_by']},
                () => this.update_served_by_section(),
            ]);
        });
        frappe.run_serially([
            () => this.ignore_pricing_rule = pos_ignore_pricing_rule,
            () => this.update_pricing_rule_discount_section(),
            // () => this.ignore_pricing_discount(this, pos_ignore_pricing_rule),
        ]);
    }
    get_cache_data(){
		frappe.call({
			method: 'bbb.bbb.pos_invoice.get_pos_cached_data',
			callback: function(r) {
				if (!r.exc) {
					// console.log(r.message);
					return r.message;
				}
			}
		});
	}
    load_invoice() {
        const me = this;
        const frm = this.events.get_frm();
        frm.events.item_list = [];
        this.attach_refresh_field_event(frm);
        // const cached_data = this.events.get_cache_data();
        // if(cached_data){
        //     this.update_cached_data(cached_data)
        // }
        // else {
        this.fetch_served_by_details(frm.doc.served_by).then(() => {
            this.update_served_by_section();
        });
        this.fetch_discount_details(frm.doc.ignore_pricing_rule).then(() => {
            this.update_pricing_rule_discount_section();
        });
        this.fetch_customer_details(frm.doc.customer).then(() => {
            this.events.customer_details_updated(this.customer_info);
            this.update_customer_section();
        });
        // }
        this.$cart_items_wrapper.html('');
        // pos return
        // if(frm.doc.is_return){
        //     const item_data = frm.doc.items;
        //     frm.doc.items = [];
        //     frm.refresh_field('ignore_pricing_rule');
        //     item_data.forEach(item => {
        //         frappe.db.get_value('Item', {'item_code': item.item_code}, ['start_date', 'end_date', 'discount_amount']).then(res=>{
        //             let new_item = {'item_code':item.item_code, 'batch_no': item.batch_no, 'rate':item.item_code, 'item_actual_qty': item.qty, 'mrp': item.price_list_rate, 'title': item.item_name, 'discount_amount': res.message.discount_amount, 'start_date': new Date(res.message.start_date), 'end_date': new Date(res.message.end_date), update_rules: 0}
        //             var args = {
        //             'field': "qty",
        //             'item': new_item,
        //             'value': item.qty
        //             }
        //             me.events.on_cart_update(args);
        //         })
        //     });
        // }else{
        //     if (frm.doc.items.length) {
        //         frm.doc.items.forEach(item => {
        //             this.update_item_html(item);
        //         });
        //     } else {
        //         this.make_no_items_placeholder();
        //         this.highlight_checkout_btn(false);
        //     }
        // }

        if (frm.doc.items.length) {
            frm.doc.items.forEach(item => {
                this.update_item_html(item);
            });
        } else {
            this.make_no_items_placeholder();
            this.highlight_checkout_btn(false);
        }
         me.update_totals_section(frm);


        // setTimeout(function (){
        //     if (frm.doc.items.length) {
        //         frm.doc.items.forEach(item => {
        //             if(item.pricing_rules && item.discount_percentage <= 0){
        //                 frappe.call({
        //                     method: "bbb.bbb.controllers.utils.get_pricing_rule_discount",
        //                     args: {"name": item.pricing_rules},
        //                     callback: (r) => {
        //                         frappe.model.set_value(item.doctype, item.name, 'discount_percentage', r.message.discount_percentage)
        //                         me.update_item_html(item);
        //                     }
        //                 })
        //             }else{
        //                 me.update_item_html(item);
        //             }
        //         })
        //     } else {
        //         me.make_no_items_placeholder();
        //         me.highlight_checkout_btn(false);
        //     }
        //
        //     me.update_totals_section(frm);
        // }, 5000);



        if (frm.doc.docstatus === 1) {
            this.$totals_section.find('.checkout-btn').css('display', 'none');
            this.$totals_section.find('.edit-cart-btn').css('display', 'none');
        } else {
            this.$totals_section.find('.checkout-btn').css('display', 'flex');
            this.$totals_section.find('.edit-cart-btn').css('display', 'none');
        }
        this.make_pos_profile();
        this.toggle_component(true);
        // if(cached_data){
        //     const items = cached_data.pos_items ? cached_data.pos_items : {}
        //     frm.doc.items = [];
        //     frm.refresh_field('items');
        //     frm.reload_doc();
        //     items.forEach(item_dict => {
        //         const values = Object.values(item_dict)[0];
        //         var qty = values.qty;
        //         var args = {
        //         'field': "qty",
        //         'item': values,
        //         'value': "+" + qty
        //         }
        //         this.events.update_cached_item_data(args);
        //     });
        // }
    }

    toggle_component(show) {
        show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
    }

    load_pricing_rules(){
        const frm = this.events.get_frm();
        if(!frm.doc.pricing_rules.length){
            frappe.call({
                method: "bbb.bbb.controllers.utils.get_and_apply_item_pricing_rules",
                args: {"return_against": frm.doc.return_against},
                callback: (r) => {
                    let pricing_rules = r.message
                    pricing_rules.forEach(pricing_rule => {
                        let pricing_rule_detail = {'item_code': pricing_rule.item_code, 'pricing_rule': pricing_rule.pricing_rule}
                        frm.add_child('pricing_rules', pricing_rule_detail);
                    });
                }
            });
        }
    }


    // ignore_pricing_discount(me) {
	// 		// var me = this;
	// 		var item_list = [];
    //
	// 		$.each(me.frm.doc["items"] || [], function(i, d) {
	// 			if (d.item_code && !d.is_free_item) {
	// 				item_list.push({
	// 					"doctype": d.doctype,
	// 					"name": d.name,
	// 					"item_code": d.item_code,
	// 					"pricing_rules": d.pricing_rules,
	// 					"parenttype": d.parenttype,
	// 					"parent": d.parent,
	// 					"price_list_rate": d.price_list_rate
	// 				})
	// 			}
	// 		});
	// 		return this.frm.call({
	// 			method: "erpnext.accounts.doctype.pricing_rule.pricing_rule.remove_pricing_rules",
	// 			args: { item_list: item_list },
	// 			callback: function(r) {
	// 				if (!r.exc && r.message) {
	// 					r.message.forEach(row_item => {
	// 						me.remove_pricing_rule(row_item);
	// 					});
	// 					me._set_values_for_item_list(r.message);
	// 					me.calculate_taxes_and_totals();
	// 					if(me.frm.doc.apply_discount_on) me.frm.trigger("apply_discount_on");
	// 				}
	// 			}
	// 		});
	//
	// }

    async ignore_pricing_discount(me, value) {
        // const cached_data = me.events.get_cache_data();
        // const items = cached_data['pos_items']
        me.$cart_items_wrapper.empty();
        var frm = me.events.get_frm();
        var item_list = me.events.get_cart_items();
        let update_rules = true
        if (value === 'Yes') {
            frm.doc.ignore_pricing_rule = 1;
            update_rules = true
            // frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'ignore_pricing_rule', 0);
        } else if (value === 'No') {
            frm.doc.ignore_pricing_rule = 0
            update_rules = false
            // frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'ignore_pricing_rule', 1);
        }
        const item_data = frm.doc.items;
        frm.doc.items = [];
        frm.refresh_field('ignore_pricing_rule');
        await item_data.forEach(item => {
            frappe.db.get_value('Item', {'item_code': item.item_code}, ['start_date', 'end_date', 'discount_amount']).then(res=>{
                let new_item = {'item_code':item.item_code, 'batch_no': item.batch_no, 'rate':item.item_code, 'qty': item.qty, 'mrp': item.price_list_rate, 'title': item.item_name, 'discount_amount': res.message.discount_amount, 'start_date': new Date(res.message.start_date), 'end_date': new Date(res.message.end_date), update_rules: update_rules}
                var args = {
                'field': "qty",
                'item': new_item,
                'value': "+" + item.qty
                }
                this.events.on_cart_update(args);
            })
        });
        frm.reload_doc();
        // console.log(frm.doc)
    }

    check_out_validation(show) {
        if (!show) {
            this.$totals_section.find('.checkout-btn').css('display', 'none');
            this.$totals_section.find('.edit-cart-btn').css('display', 'none');
        } else {
            this.$totals_section.find('.checkout-btn').css('display', 'flex');
            this.$totals_section.find('.edit-cart-btn').css('display', 'none');
        }
    }

    // toggle_selector(enabled) {
    //     this.$customer_section.find('.customer-section').setAttribute('disabled');
    // }

    async update_item_cart_total_section(frm){
        const item_section = $('.cart-item-wrapper').is(':visible');
        if(item_section == true){
            const items = frm.doc.items;
            let total_mrp = 0;
            let total_disc = 0;
            let total_after_disc = 0;
            let total_qty = frm.doc.total_qty;
            let total_amount = frm.doc.total;
            items.forEach(item => {
                total_mrp += parseFloat(item.price_list_rate);
                total_after_disc += parseFloat(item.rate);
                total_disc += (parseFloat(item.price_list_rate) - parseFloat(item.rate));
            });
            $('.mrp-label').html(total_mrp);
            $('.disc-label').html(total_disc);
            $('.after-disc-label').html(total_after_disc.toFixed(0));
            $('.qty-label').html(total_qty);
            $('.final-amount-total-label').html(total_amount.toFixed(0));

            $('.total-section').css('visibility', 'visible');
            //
            // $('.mrp-label').html(format_currency(total_mrp, frm.doc.currency));
            // $('.disc-label').html(format_currency(total_disc, frm.doc.currency));
            // $('.after-disc-label').html(format_currency(total_after_disc.toFixed(0), frm.doc.currency));
            // $('.qty-label').html(total_qty);
            // $('.final-amount-total-label').html(format_currency(total_amount.toFixed(0), frm.doc.currency));
        }else{
            $('.total-section').css('visibility', 'hidden');
        }

    }

    update_item_qty(){
        const me = this;
        const frm = me.events.get_frm()
        let items = frm.doc.items;
        // console.log(items);
        if(items.length){
            items.forEach(item => {
                var item_qty = item.qty;
                frappe.model.set_value("POS Invoice Item", item.name, 'qty', 0)
                    .then(function (){
                        // console.log(item_qty)
                        frappe.model.set_value("POS Invoice Item", item.name, 'qty', item_qty)
                            .then(function (){
                                if(frm.doc.is_return){
                                    frappe.call({
                                        method: "bbb.bbb.controllers.utils.apply_item_pricing_rule",
                                        args: {"return_against": frm.doc.return_against, 'item_code': item.item_code},
                                        callback: (r) => {
                                            frappe.model.set_value("POS Invoice Item", item.name, 'margin_type', r.message.margin_type)
                                            frappe.model.set_value("POS Invoice Item", item.name, 'discount_percentage', r.message.discount_percentage)
                                        }
                                    })
                                }
                            })
                    })

            });

        }

    }


    update_item_qty_(){
        const me = this;
        const frm = me.events.get_frm()
        let items = frm.doc.items;
        if(frm.doc.is_return && items.length){
            frappe.call({
                method: "bbb.bbb.controllers.utils.apply_all_items_pricing_rules",
                args: {"return_against": frm.doc.return_against},
                callback: (r) => {
                    items.forEach(item => {
                        var item_code = item.item_code
                        var item_qty = item.qty;
                        frappe.model.set_value("POS Invoice Item", item.name, 'qty', 0)
                            .then(function () {
                                frappe.model.set_value("POS Invoice Item", item.name, 'qty', item_qty)
                                    .then(function () {
                                        let data = (r.message)[item_code];
                                        console.log(data, item.item_code, item.item_name)
                                            frappe.model.set_value("POS Invoice Item", item.name, 'margin_type', data.margin_type)
                                            frappe.model.set_value("POS Invoice Item", item.name, 'discount_percentage', data.discount_percentage)

                                    })
                            })
                    })
                }
            })
        }
    }

}