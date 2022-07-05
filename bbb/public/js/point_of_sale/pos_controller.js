erpnext.PointOfSale.Controller = class {
    constructor(wrapper) {
        this.wrapper = $(wrapper).find('.layout-main-section');
        this.page = wrapper.page;
        this.check_opening_entry();
        this.item_list = [];
        $(".page-head").css("display", "none");
        $(".page-body").css("margin-top", "20px");
        this.cached_data = undefined;
        this.get_cache_data(this);
        this.base_rounded_total = undefined;
        this.initial_paid_amount = undefined;
    }

    fetch_opening_entry() {
        return frappe.call("erpnext.selling.page.point_of_sale.point_of_sale.check_opening_entry", {"user": frappe.session.user});
    }

    check_opening_entry() {
        this.fetch_opening_entry().then((r) => {
            if (r.message.length) {
                // assuming only one opening voucher is available for the current user
                this.prepare_app_defaults(r.message[0]);
            } else {
                this.create_opening_voucher();
            }
        });
    }

    create_opening_voucher() {
        const me = this;
        const table_fields = [
            {
                fieldname: "mode_of_payment", fieldtype: "Link",
                in_list_view: 1, label: "Mode of Payment",
                options: "Mode of Payment", reqd: 1
            },
            {
                fieldname: "opening_amount", fieldtype: "Currency",
                in_list_view: 1, label: "Opening Amount",
                options: "company:company_currency",
                change: function () {
                    dialog.fields_dict.balance_details.df.data.some(d => {
                        if (d.idx == this.doc.idx) {
                            d.opening_amount = this.value;
                            dialog.fields_dict.balance_details.grid.refresh();
                            return true;
                        }
                    });
                }
            }
        ];
        const fetch_pos_payment_methods = () => {
            const pos_profile = dialog.fields_dict.pos_profile.get_value();
            if (!pos_profile) return;
            frappe.db.get_doc("POS Profile", pos_profile).then(({payments}) => {
                dialog.fields_dict.balance_details.df.data = [];
                payments.forEach(pay => {
                    const {mode_of_payment} = pay;
                    dialog.fields_dict.balance_details.df.data.push({mode_of_payment, opening_amount: '0'});
                });
                dialog.fields_dict.balance_details.grid.refresh();
            });
        }
        const dialog = new frappe.ui.Dialog({
            title: __('Create POS Opening Entry'),
            static: true,
            fields: [
                {
                    fieldtype: 'Link', label: __('Company'), default: frappe.defaults.get_default('company'),
                    options: 'Company', fieldname: 'company', reqd: 1
                },
                {
                    fieldtype: 'Link', label: __('POS Profile'),
                    options: 'POS Profile', fieldname: 'pos_profile', reqd: 1,
                    get_query: () => pos_profile_query,
                    onchange: () => fetch_pos_payment_methods()
                },
                {
                    fieldname: "balance_details",
                    fieldtype: "Table",
                    label: "Opening Balance Details",
                    cannot_add_rows: false,
                    in_place_edit: true,
                    reqd: 1,
                    data: [],
                    fields: table_fields
                }
            ],
            primary_action: async function ({company, pos_profile, balance_details}) {
                if (!balance_details.length) {
                    frappe.show_alert({
                        message: __("Please add Mode of payments and opening balance details."),
                        indicator: 'red'
                    })
                    return frappe.utils.play_sound("error");
                }

                // filter balance details for empty rows
                balance_details = balance_details.filter(d => d.mode_of_payment);

                const method = "erpnext.selling.page.point_of_sale.point_of_sale.create_opening_voucher";
                const res = await frappe.call({method, args: {pos_profile, company, balance_details}, freeze: true});
                !res.exc && me.prepare_app_defaults(res.message);
                dialog.hide();
            },
            primary_action_label: __('Submit')
        });
        dialog.show();
        const pos_profile_query = {
            query: 'erpnext.accounts.doctype.pos_profile.pos_profile.pos_profile_query',
            filters: {company: dialog.fields_dict.company.get_value()}
        };
    }

    async prepare_app_defaults(data) {
        this.pos_opening = data.name;
        this.company = data.company;
        this.pos_profile = data.pos_profile;
        this.pos_opening_time = data.period_start_date;
        this.item_stock_map = {};
        this.settings = {};

        frappe.db.get_value('Stock Settings', undefined, 'allow_negative_stock').then(({message}) => {
            this.allow_negative_stock = flt(message.allow_negative_stock) || false;
        });

        frappe.db.get_doc("POS Profile", this.pos_profile).then((profile) => {
            Object.assign(this.settings, profile);
            this.settings.customer_groups = profile.customer_groups.map(group => group.customer_group);
            this.make_app();
        });
    }

    set_opening_entry_status() {
        this.page.set_title_sub(
            `<span class="indicator orange">
				<a class="text-muted" href="#Form/POS%20Opening%20Entry/${this.pos_opening}">
					Opened at ${moment(this.pos_opening_time).format("Do MMMM, h:mma")}
				</a>
			</span>`);
    }

    make_app() {
        this.prepare_dom();
        this.prepare_components();
        this.prepare_menu();
        this.make_new_invoice();
    }

    prepare_dom() {
        this.wrapper.append(
            `<div class="point-of-sale-app"></div>`
        );

        this.$components_wrapper = this.wrapper.find('.point-of-sale-app');
    }

    prepare_components() {
        this.init_item_selector();
        this.init_item_details();
        this.init_item_cart();
        this.init_payments();
        this.init_recent_order_list();
        this.init_order_summary();
    }

    prepare_menu() {
        this.page.clear_menu();
        let me = this
        $('#open_form_view').bind('click', function (e) {
            e.preventDefault();
            me.open_form_view();
        });
        $('#check_item_stock').bind('click', function (e) {
            e.preventDefault();
            me.check_item_stock();
        });
        $('#reset_cart').bind('click', function (e) {
            location.reload();
        });
        $('#toggle_recent_order').bind('click', function (e) {
            e.preventDefault();
            me.toggle_recent_order();
        });
        $('#save_draft_invoice').bind('click', function (e) {
            e.preventDefault();
            me.save_draft_invoice();
        });
        $('#close_pos').bind('click', function (e) {
            e.preventDefault();
            me.close_pos();
        });
        $('.recent_order_back_button').bind('click', function (e) {
            e.preventDefault();
            me.toggle_recent_order();
        });
        // this.page.add_menu_item(__("Open Form View"), this.open_form_view.bind(this), false, 'Ctrl+F');
        //
        // this.page.find('.toggle_recent_order').bind(this.toggle_recent_order.bind(this), false, 'Ctrl+O');
        //
        // this.page.add_menu_item(__("Save as Draft"), this.save_draft_invoice.bind(this), false, 'Ctrl+S');
        //
        // this.page.add_menu_item(__('Close the POS'), this.close_pos.bind(this), false, 'Shift+Ctrl+C');
    }

    open_form_view() {
        frappe.model.sync(this.frm.doc);
        frappe.set_route("Form", this.frm.doc.doctype, this.frm.doc.name);
    }

    check_item_stock() {
        function get_items_template(dialog, data){
            var html = `<div class="card mb-4">
                {% if data %}
                    <div class="dashboard-list-item" style="padding: 12px 15px;">
                        <div class="row col-md-12">
                            <div class="col-sm-3 text-muted" style="margin-top: 8px;">
                                Warehouse
                            </div>
                            <div class="col-sm-7 text-muted" style="margin-top: 8px;">
                                Item Name
                            </div>
                            <div class="col-sm-2 text-muted" style="margin-top: 8px;">
                                Stock Status
                            </div>
                        </div>
                    </div>
                    {% for d in data %}
                        <div class="dashboard-list-item" style="padding: 7px 15px;">
                            <div class="row col-md-12">
                                <div class="col-sm-3" style="margin-top: 8px;">
                                    <a data-type="warehouse" data-name="{{ d.warehouse }}">
                                        {{ d.warehouse }}</a>
                                    </div>
                                    <div class="col-sm-7" style="margin-top: 8px; ">
                                        <a data-type="item" data-name="{{ d.item_name }}">
                                            {{ d.item_name }}</a>
                                        </div>
                                    <div class="col-sm-2 text-center" style="margin-top: 8px;">
                                        {% if d.actual_qty > 5 %}
                                            <span style="color: green">+5</span>
                                        {% else %}
                                            <span style="color: red">-5</span>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <div class="mt-2 mb-2 text-center">
                            <span class="text-md-center">Item Not Found!</span>			
                        </div>
                    {% endif %}
                </div>`;

            var table_data = frappe.render_template(html, {data: data});
            d.fields_dict.items.$wrapper.html(table_data);
        }

        function get_items(item){
            frappe.call({
                method: 'bbb.bbb.page.item_stock.item_stock.get_item_stock_data',
                args: {
                    search_text: item
                },
                callback: function(r) {
                    if (!r.exc) {
                        // code snippet
                        // console.log(r);
                        if(r.message.length !== 0){
                            // console.log("=====>>>", r.message)
                            get_items_template(d, r.message)
                        }
                        else{
                            get_items_template(d, null)
                        }
                    }
                }
            });
        }

        var d = new frappe.ui.Dialog({
            title: "Item Stock Status",
            fields: [
                {
                    fieldtype: "Data",
                    fieldname: "item",
                    label: __("Item"),
                    reqd: 1,
                    onchange: function (e) {
                        // cur_dialog.fields_dict.item_code.value
                        get_items(this.value)
                    }
                },
                {
                  fieldtype: "Column Break"
                },
                {
                    fieldtype: "Section Break"
                },
                {
                    'fieldname': 'items',
                    'fieldtype': 'HTML'
                },
            ],
        });
        d.show();
        d.$wrapper.find('.modal-dialog').css("max-width", "800px");
    }

    toggle_recent_order() {
        const show = this.recent_order_list.$component.is(':hidden');
        this.toggle_recent_order_list(show);
    }

    save_draft_invoice() {
        if (!this.$components_wrapper.is(":visible")) return;
        const frm = this.frm;

        this.get_naming_series(this);
        if (this.frm.doc.items.length == 0) {
            frappe.show_alert({
                message: __("You must add atleast one item to save it as draft."),
                indicator: 'red'
            });
            frappe.utils.play_sound("error");
            return;
        }

        this.frm.save(undefined, undefined, undefined, () => {
            frappe.show_alert({
                message: __("There was an error saving the document."),
                indicator: 'red'
            });
            frappe.utils.play_sound("error");
        }).then(() => {
            frappe.run_serially([
                () => frappe.dom.freeze(),
                () => this.make_new_invoice(),
                () => frappe.dom.unfreeze(),
            ]);
        });
    }

    close_pos() {
        if (!this.$components_wrapper.is(":visible")) return;

        let voucher = frappe.model.get_new_doc('POS Closing Entry');
        voucher.pos_profile = this.frm.doc.pos_profile;
        voucher.user = frappe.session.user;
        voucher.company = this.frm.doc.company;
        voucher.pos_opening_entry = this.pos_opening;
        voucher.period_end_date = frappe.datetime.now_datetime();
        voucher.posting_date = frappe.datetime.now_date();
        frappe.set_route('Form', 'POS Closing Entry', voucher.name);
    }

    init_item_selector() {
        this.item_selector = new erpnext.PointOfSale.ItemSelector({
            wrapper: this.$components_wrapper,
            pos_profile: this.pos_profile,
            settings: this.settings,
            events: {
                item_selected: args => this.on_cart_update(args),
                set_cart_item: args => this.item_list.push(args),
                get_frm: () => this.frm || {},
            }
        })
    }

    init_item_cart() {
        this.cart = new erpnext.PointOfSale.ItemCart({
            wrapper: this.$components_wrapper,
            settings: this.settings,
            events: {
                get_frm: () => this.frm,

                cart_item_clicked: (item) => {
                    const item_row = this.get_item_from_frm(item);
                    this.item_details.toggle_item_details_section(item_row);
                },

                numpad_event: (value, action) => this.update_item_field(value, action),

                checkout: () => this.payment.checkout(),

                edit_cart: () => this.payment.edit_cart(),

                customer_details_updated: (details) => {
                    this.customer_details = details;
                    // will add/remove LP payment method
                    this.payment.render_loyalty_points_payment_mode();
                },
                get_cart_items: () => this.item_list,
                set_cart_item: args => this.item_list.push(args),
                on_cart_update: args => this.on_cart_update(args),
                item_selected: args => this.on_cart_update(args),
                set_cache_data: args => this.set_cache_data(args),
                get_cache_data: () => this.cached_data,
                open_form_view: () => this.open_form_view(),
                toggle_recent_order: () => this.toggle_recent_order(),
                save_draft_invoice: () => this.save_draft_invoice(),
                close_pos: () => this.close_pos(),
                update_cached_item_data: (args) => this.update_cached_item_data(args),
                update_rounded_total: (item_row) => this.update_rounded_total(item_row),
                get_5_basis_rounded: (number) => this.get_5_basis_rounded(number),
                set_5_basis_rounded_total: (number) => this.set_5_basis_rounded_total(number),
                get_5_basis_rounded_total: () => this.base_rounded_total,
                update_paid_amount: () => this.update_paid_amount,
                get_initial_paid_amount: () => this.initial_paid_amount,
                set_initial_paid_amount: (paid_amount) => this.set_initial_paid_amount(paid_amount),
            }
        })
    }

    init_item_details() {
        this.item_details = new erpnext.PointOfSale.ItemDetails({
            wrapper: this.$components_wrapper,
            settings: this.settings,
            events: {
                get_frm: () => this.frm,

                toggle_item_selector: (minimize) => {
                    // this.item_selector.resize_selector(minimize); // hide for item detail
                    this.cart.toggle_numpad(minimize);
                },

                form_updated: (item, field, value) => {
                    const item_row = frappe.model.get_doc(item.doctype, item.name);
                    if (item_row && item_row[field] != value) {
                        const args = {
                            field,
                            value,
                            item: this.item_details.current_item
                        };
                        return this.on_cart_update(args);
                    }

                    return Promise.resolve();
                },

                highlight_cart_item: (item) => {
                    const cart_item = this.cart.get_cart_item(item);
                    this.cart.toggle_item_highlight(cart_item);
                },

                item_field_focused: (fieldname) => {
                    this.cart.toggle_numpad_field_edit(fieldname);
                },
                set_value_in_current_cart_item: (selector, value) => {
                    this.cart.update_selector_value_in_cart_item(selector, value, this.item_details.current_item);
                },
                clone_new_batch_item_in_frm: (batch_serial_map, item) => {
                    // called if serial nos are 'auto_selected' and if those serial nos belongs to multiple batches
                    // for each unique batch new item row is added in the form & cart
                    Object.keys(batch_serial_map).forEach(batch => {
                        const item_to_clone = this.frm.doc.items.find(i => i.name == item.name);
                        const new_row = this.frm.add_child("items", {...item_to_clone});
                        // update new serialno and batch
                        new_row.batch_no = batch;
                        new_row.serial_no = batch_serial_map[batch].join(`\n`);
                        new_row.qty = batch_serial_map[batch].length;
                        this.frm.doc.items.forEach(row => {
                            if (item.item_code === row.item_code) {
                                this.update_cart_html(row);
                            }
                        });
                    })
                },
                remove_item_from_cart: () => this.remove_item_from_cart(),
                get_item_stock_map: () => this.item_stock_map,
                close_item_details: () => {
                    this.item_details.toggle_item_details_section(null);
                    this.cart.prev_action = null;
                    this.cart.toggle_item_highlight();
                },
                get_available_stock: (item_code, warehouse) => this.get_available_stock(item_code, warehouse)
            }
        });
    }

    init_payments() {
        this.payment = new erpnext.PointOfSale.Payment({
            wrapper: this.$components_wrapper,
            events: {
                get_frm: () => this.frm || {},

                get_customer_details: () => this.customer_details || {},
                get_5_basis_rounded: (number) => this.get_5_basis_rounded(number),

                toggle_other_sections: (show) => {
                    if (show) {
                        this.item_details.$component.is(':visible') ? this.item_details.$component.css('display', 'none') : '';
                        this.item_selector.$component.css('display', 'none');
                    } else {
                        this.item_selector.$component.css('display', 'flex');
                    }
                },

                submit_invoice: () => {
                    let grand_total = this.$components_wrapper.find('.payment_grand_total_value').attr('grand_total_val')
                    let paid_amount = this.$components_wrapper.find('.payment_amount_value').attr('paid_amount_val')
                    if((grand_total-paid_amount) > 0){
                        frappe.dom.unfreeze();
                        frappe.show_alert({
                            message: __('Partial paid not allow'),
                            indicator: 'red'
                        });
                        frappe.utils.play_sound("error");
                    }else {
                        frappe.run_serially([
                            () => this.get_naming_series(this),
                            () => this.process_submit()
                        ]);
                    }
                },
                set_5_basis_rounded_total: (grand_total) => this.set_5_basis_rounded_total(grand_total),
                get_5_basis_rounded_total: () => this.base_rounded_total,
                get_initial_paid_amount: () => this.initial_paid_amount,
                set_initial_paid_amount: (paid_amount) => this.set_initial_paid_amount(paid_amount),
            }
        });
    }

    process_submit() {
        this.frm.savesubmit()
            .then((r) => {
                this.toggle_components(false);
                this.order_summary.toggle_component(true);
                this.order_summary.load_summary_of(this.frm.doc, true);
                frappe.show_alert({
                    indicator: 'green',
                    message: __('POS invoice {0} created successfully', [r.doc.name])
                });
                this.print_receipt(this.frm);
                frappe.ui.toolbar.clear_cache();

            })
    }

    get_naming_series(me) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'POS Profile',
                'filters': {'name': this.pos_profile},
                'fieldname': [
                    '_naming_series',
                ]
            },
            callback: function (r) {
                let random_number = Math.floor((Math.random() * 10000) + 1);
                me.frm.doc.naming_series = r.message._naming_series + random_number;
                me.frm.refresh(me.frm.doc.name);
            }
        });
    }

    init_recent_order_list() {
        this.recent_order_list = new erpnext.PointOfSale.PastOrderList({
            wrapper: this.$components_wrapper,
            events: {
                open_invoice_data: (name) => {
                    frappe.db.get_doc('POS Invoice', name).then((doc) => {
                        this.order_summary.load_summary_of(doc);
                    });
                },
                reset_summary: () => this.order_summary.toggle_summary_placeholder(true),
                insert_invoice_print_log: () => this.insert_invoice_print_log(),

            }
        })
    }

    init_order_summary() {
        this.order_summary = new erpnext.PointOfSale.PastOrderSummary({
            wrapper: this.$components_wrapper,
            events: {
                get_frm: () => this.frm,

                process_return: (name) => {
                    this.recent_order_list.toggle_component(false);
                    frappe.db.get_doc('POS Invoice', name).then((doc) => {
                        frappe.run_serially([
                            () => this.make_return_invoice(doc),
                            () => this.cart.load_invoice(),
                            () => this.item_selector.toggle_component(true)
                        ]);
                    });
                },
                edit_order: (name) => {
                    this.recent_order_list.toggle_component(false);
                    frappe.run_serially([
                        () => this.frm.refresh(name),
                        () => this.frm.call('reset_mode_of_payments'),
                        () => this.cart.load_invoice(),
                        () => this.item_selector.toggle_component(true)
                    ]);
                },
                delete_order: (name) => {
                    frappe.model.delete_doc(this.frm.doc.doctype, name, () => {
                        this.recent_order_list.refresh_list();
                    });
                },
                new_order: () => {
                    frappe.run_serially([
                        () => frappe.dom.freeze(),
                        () => this.make_new_invoice(),
                        () => this.item_selector.toggle_component(true),
                        () => frappe.dom.unfreeze(),
                    ]);
                }
            }
        })
    }

    toggle_recent_order_list(show) {
        this.toggle_components(!show);
        this.recent_order_list.toggle_component(show);
        this.order_summary.toggle_component(show);
    }

    toggle_components(show) {
        this.cart.toggle_component(show);
        this.item_selector.toggle_component(show);

        // do not show item details or payment if recent order is toggled off
        !show ? (this.item_details.toggle_component(false) || this.payment.toggle_component(false)) : '';
    }

    make_new_invoice() {
        return frappe.run_serially([
            () => frappe.dom.freeze(),
            () => this.make_sales_invoice_frm(),
            () => this.set_pricing_rule(),
            () => this.set_pos_profile_data(),
            () => this.set_pos_profile_status(),
            () => this.cart.load_invoice(),
            () => frappe.dom.unfreeze()
        ]);
    }
    set_pricing_rule(){
        frappe.model.set_value(this.frm.doc.doctype, this.frm.doc.name, 'ignore_pricing_rule', 1);
    }
    make_sales_invoice_frm() {
        const doctype = 'POS Invoice';

        return new Promise(resolve => {
            if (this.frm) {
                this.frm = this.get_new_frm(this.frm);
                this.frm.doc.items = [];
                this.frm.doc.is_pos = 1
                // this.get_cached_data_if_exist(this, this.frm)
                resolve();
            } else {
                frappe.model.with_doctype(doctype, () => {
                    this.frm = this.get_new_frm();
                    this.frm.doc.items = [];
                    this.frm.doc.is_pos = 1
                    // this.get_cached_data_if_exist(this, this.frm)
                    resolve();
                });
            }
        });
    }

    get_cached_data_if_exist(me, frm) {
        const cached_data = me.get_cache_data(me);
        // console.log(cached_data)

        if (cached_data) {
            const items = cached_data.pos_items
            frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', cached_data.pos_customer);
            frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'served_by', cached_data.served_by);
            if (cached_data.pos_ignore_pricing_rule === 'Yes') {
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'ignore_pricing_rule', 1);
            } else if (cached_data.pos_ignore_pricing_rule === 'No') {
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'ignore_pricing_rule', 0);
            }
            // frm.refresh_fields(['customer', 'served_by', 'ignore_pricing_rule']);
            if (items) {
                items.forEach(item_dict => {
                    const values = Object.values(item_dict)[0];
                    var qty = values.qty;
                    const new_item = {
                        'item_code': values.item_code,
                        'batch_no': values.batch_no,
                        'rate': values.rate,
                        'qty': values.qty,
                        'serial_no': values.serial_no
                    };
                    frm.add_child('items', new_item);
                });
            }
            frm.reload_doc();
        }
        console.log(this);
    }

    get_new_frm(_frm) {
        const doctype = 'POS Invoice';
        const page = $('<div>');
        const frm = _frm || new frappe.ui.form.Form(doctype, page, false);
        const name = frappe.model.make_new_doc_and_get_name(doctype, true);
        frm.refresh(name);

        return frm;
    }

    async make_return_invoice(doc) {
        frappe.dom.freeze();
        this.frm = this.get_new_frm(this.frm);
        this.frm.doc.items = [];
        const res = await frappe.call({
            method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.make_sales_return",
            args: {
                'source_name': doc.name,
                'target_doc': this.frm.doc
            }
        });
        frappe.model.sync(res.message);
        await this.set_pos_profile_data();
        frappe.dom.unfreeze();
    }

    set_pos_profile_data() {
        if (this.company && !this.frm.doc.company) this.frm.doc.company = this.company;
        if (this.pos_profile && !this.frm.doc.pos_profile) this.frm.doc.pos_profile = this.pos_profile;
        if (!this.frm.doc.company) return;

        return this.frm.trigger("set_pos_data");
    }

    set_pos_profile_status() {
        this.page.set_indicator(this.pos_profile, "blue");
    }

    async update_cached_item_data(args) {
        // console.log('args ', args)
        frappe.dom.freeze();
        let item_row = undefined;
        try {
            let {field, value, item} = args;
            item_row = this.get_item_from_frm(item);
            const item_row_exists = !$.isEmptyObject(item_row);
            const {item_code, batch_no, serial_no, uom, rate, mrp, title, update_rules} = item;
            // if (this.frm.doc.customer) {
            // 	this.set_cache_data({"pos_items": [item_code, batch_no, serial_no, uom, rate, mrp, title]})
            // }
            // if (this.frm.doc.customer) {
            // 	this.set_cache_data({"pos_items": {'item_code':item_code, 'batch_no': batch_no, 'serial_no': serial_no, 'rate': rate, 'qty':1, 'uom': uom, 'mrp':mrp, 'title':title, 'name': title }})
            // }
            const from_selector = field === 'qty' && value === "+1";
            if (from_selector)
                value = flt(item_row.qty) + flt(value);

            if (item_row_exists) {
                if (field === 'qty')
                    value = flt(value);

                if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
                    const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
                    await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
                }

                if (this.is_current_item_being_edited(item_row) || from_selector) {
                    await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
                    this.update_cart_html(item_row);
                }

            } else {
                if (!this.frm.doc.customer)
                    return this.raise_customer_selection_alert();
                const {item_code, batch_no, serial_no, rate} = item;

                if (!item_code)
                    return;

                const new_item = {item_code, batch_no, rate, [field]: value};
                if (serial_no) {
                    await this.check_serial_no_availablilty(item_code, this.frm.doc.set_warehouse, serial_no);
                    new_item['serial_no'] = serial_no;
                }

                if (field === 'serial_no')
                    new_item['qty'] = value.split(`\n`).length || 0;

                item_row = this.frm.add_child('items', new_item);

                if (field === 'qty' && value !== 0 && !this.allow_negative_stock)
                    await this.check_stock_availability(item_row, value, this.frm.doc.set_warehouse);

                await this.trigger_new_item_events(item_row);

                this.update_cart_html(item_row);

                if (this.item_details.$component.is(':visible'))
                    this.edit_item_details_of(item_row);

                if (this.check_serial_batch_selection_needed(item_row))
                    this.edit_item_details_of(item_row);
            }

        } catch (error) {
            console.log(error);
        } finally {
            frappe.dom.unfreeze();
            return item_row;
        }
    }

    // async on_cart_update(args) {
    // 	console.log('args ', args)
    // 	frappe.dom.freeze();
    // 	let item_row = undefined;
    // 	try {
    // 		let { field, value, item } = args;
    // 		item_row = this.get_item_from_frm(item);
    // 		const item_row_exists = !$.isEmptyObject(item_row);
    // 		// if (this.frm.doc.customer) {
    // 		// 	this.set_cache_data({"pos_items": {'item_code':item_code, 'batch_no': batch_no, 'serial_no': serial_no, 'rate': rate, 'qty':1, 'uom': uom, 'mrp':mrp, 'title':title, 'name': title }})
    // 		// }
    // 		const from_selector = field === 'qty' && value === "+1";
    // 		if (from_selector)
    // 			value = flt(item_row.qty) + flt(value);
    //
    // 		if (item_row_exists) {
    // 			if (field === 'qty')
    // 				value = flt(value);
    //
    // 			if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
    // 				const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
    // 				await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
    // 			}
    //
    // 			if (this.is_current_item_being_edited(item_row) || from_selector) {
    // 				await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
    // 				this.update_cart_html(item_row);
    // 			}
    //
    // 			this.insert_search_product_log(item_code, item_row.title)
    //
    // 		} else {
    // 			if (!this.frm.doc.customer)
    // 				return this.raise_customer_selection_alert();
    // 			const { item_code, batch_no, serial_no, rate } = item;
    //
    // 			if (!item_code)
    // 				return;
    //
    // 			const new_item = { item_code, batch_no, rate, [field]: value };
    // 			if (serial_no) {
    // 				await this.check_serial_no_availablilty(item_code, this.frm.doc.set_warehouse, serial_no);
    // 				new_item['serial_no'] = serial_no;
    // 			}
    //
    // 			if (field === 'serial_no')
    // 				new_item['qty'] = value.split(`\n`).length || 0;
    //
    // 			item_row = this.frm.add_child('items', new_item);
    //
    // 			if (field === 'qty' && value !== 0 && !this.allow_negative_stock)
    // 				await this.check_stock_availability(item_row, value, this.frm.doc.set_warehouse);
    //
    // 			await this.trigger_new_item_events(item_row);
    //
    // 			this.update_cart_html(item_row);
    //
    // 			if (this.item_details.$component.is(':visible'))
    // 				this.edit_item_details_of(item_row);
    //
    // 			if (this.check_serial_batch_selection_needed(item_row))
    // 				this.edit_item_details_of(item_row);
    //
    // 			this.insert_search_product_log(item_code, item_row.title)
    // 		}
    //
    // 	} catch (error) {
    // 		console.log(error);
    // 	} finally {
    // 		frappe.dom.unfreeze();
    // 		return item_row;
    // 	}
    // }

    async on_cart_update(args) {
        frappe.dom.freeze();
        let me = this;
        let item_row = undefined;
        try {
            let {field, value, item, item_quantity} = args;
            const {item_code, batch_no, serial_no, uom, rate, mrp, title, start_date, end_date, discount_amount, update_rules} = item;
            // if (this.frm.doc.customer) {
            // 	this.set_cache_data({"pos_items": [item_code, batch_no, serial_no, uom, rate, mrp, title]})
            // }
            item_row = this.get_item_from_frm(item);
            const item_row_exists = !$.isEmptyObject(item_row);

            const from_selector = field === 'qty' && value === "+1";
            if (from_selector)
                value = flt(item_row.qty) + flt(value);

            if (item_row_exists) {
                // if (update_rules === false) {
                // 	let objIndex = this.item_list.findIndex((obj => obj.item_code === item_code));
                // 	this.item_list[objIndex].item_quantity = this.item_list[objIndex].item_quantity + 1;
                // }

                if (field === 'qty')
                    value = flt(value);

                if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
                    const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
                    await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
                }

                if (this.is_current_item_being_edited(item_row) || from_selector) {
                    await frappe.model.set_value(item_row.doctype, item_row.name, field, value);


                    this.update_cart_html(item_row);
                    this.update_paid_amount()
                    // this.update_rounded_total(item_row)
                }
                await this.insert_search_product_log(item_code)

            } else {
                if (!this.frm.doc.customer)
                    return this.raise_customer_selection_alert();


                if (!this.frm.doc.served_by)
                    return this.raise_served_by_selection_alert();

                // const { item_code, batch_no, serial_no, rate } = item;

                if (!item_code)
                    return;

                const new_item = {item_code, batch_no, [field]: value, discount_amount, 'rate': (mrp-discount_amount)};

                if (serial_no) {
                    await this.check_serial_no_availablilty(item_code, this.frm.doc.set_warehouse, serial_no);
                    new_item['serial_no'] = serial_no;
                }

                if (field === 'serial_no')
                    new_item['qty'] = value.split(`\n`).length || 0;

                if (parseInt(item_quantity) > 1) {
                    new_item['qty'] = parseInt(item_quantity)
                }
                item_row = this.frm.add_child('items', new_item);

                if (field === 'qty' && value !== 0 && !this.allow_negative_stock)
                    await this.check_stock_availability(item_row, value, this.frm.doc.set_warehouse);

                await this.trigger_new_item_events(item_row);

                var today = new Date();
                if(start_date !== undefined && end_date !== undefined && discount_amount !== undefined && today >= start_date && today <= end_date && this.frm.doc.ignore_pricing_rule == 0){
                    await frappe.model.set_value("POS Invoice Item", item_row.child_docname, 'rate', (mrp-discount_amount));
                }
                this.update_cart_html(item_row)
                this.update_paid_amount()
                // this.update_rounded_total(item_row)
                // this.frm.doc.paid_amount = this.base_rounded_total;
                this.insert_search_product_log(item_code);
            }

        } catch (error) {
            console.log(error);
        } finally {
            frappe.dom.unfreeze();
            return item_row;
        }
    }
    update_paid_amount(){
        let payments = this.frm.doc.payments
        frappe.model.set_value(this.frm.doctype, this.frm.docname, 'paid_amount', this.base_rounded_total);
        frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_paid_amount', this.base_rounded_total);
        payments[0].amount = this.base_rounded_total
        payments[0].base_amount = this.base_rounded_total
        frappe.model
        .set_value(payments[0].doctype, payments[0].name, 'amount', this.base_rounded_total)
        .then(() => this.payment.update_totals_section(this.frm.doc))

        let base_rounded_total = this.get_5_basis_rounded_total();
        this.set_initial_paid_amount(base_rounded_total);
    }

    async update_rounded_total(item_row = undefined) {
        if (item_row === undefined) {
            return [];
        }
        let doc = this.frm.doc
        let grand_total = doc.grand_total
        let payments = doc.payments
        let rounded_data = await this.get_5_basis_rounded(grand_total)
        if (rounded_data) {
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'grand_total', rounded_data.rounded_total);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'rounded_total', rounded_data.rounded_total);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'rounding_adjustment', rounded_data.rounding_adjustment);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_rounded_total', rounded_data.rounded_total);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_rounding_adjustment', rounded_data.rounding_adjustment);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'paid_amount', rounded_data.rounded_total);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_paid_amount', rounded_data.rounded_total);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'outstanding_amount', 0);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'change_amount', 0);
            await frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_change_amount', 0);
            payments[0].amount = rounded_data.rounded_total;
            payments[0].base_amount = rounded_data.rounded_total;

            // await this.frm.script_manager.trigger('grand_total', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('rounded_total', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('rounding_adjustment', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('paid_amount', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('rounding_adjustment', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('rounding_adjustment', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('rounding_adjustment', item_row.doctype, item_row.name);
            // await this.frm.script_manager.trigger('qty', item_row.doctype, item_row.name);
            await this.frm.refresh(doc.name);
            // await this.update_cart_html(item_row);
        }
        /*frappe.call({
            method: 'bbb.bbb.controllers.utils.pos_invoice_rounded_total',
            args: {
                num: grand_total,
            },
            // freeze the screen until the request is completed
            freeze: true,
            callback: (r) => {
                // on success

                // frappe.dom.unfreeze();
                // let data = r.message
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'grand_total', r.message.rounded_total);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'rounded_total', r.message.rounded_total);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'rounding_adjustment', r.message.rounding_adjustment);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_rounded_total', r.message.rounded_total);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_rounding_adjustment', r.message.rounding_adjustment);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'paid_amount', r.message.rounded_total);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'base_paid_amount', r.message.rounded_total);
                frappe.model.set_value(this.frm.doctype, this.frm.docname, 'outstanding_amount', 0);
				payments[0].amount = r.message.rounded_total
				payments[0].base_amount = r.message.rounded_total

                this.update_cart_html(item_row);
                // console.log(this.wrapper.find('.pay-amount')[0]);
                // this.wrapper.find('.pay-amount').each(function (){
                //     console.log(this);
                // })
                this.frm.refresh(this.frm.doc.name);
                // frappe.dom.unfreeze();

            },
        })*/
    }

    insert_search_product_log(item_code) {
        // console.log(this.frm.doc);
        // console.log(item_code, item_name);

        frappe.db.insert({
            "doctype": "Product Search Log",
            "date": frappe.datetime.get_today(),
            "customer_name": this.frm.doc.customer_name,
            "customer": this.frm.doc.customer,
            "email": this.frm.doc.contact_email,
            "location": this.frm.doc.pos_profile,
            "served_by": this.frm.doc.served_by,
            "company": this.frm.doc.company,
            "product": item_code

        }).then(function (doc) {
            // console.log(doc);
        });
    }

    raise_customer_selection_alert() {
        frappe.dom.unfreeze();
        frappe.show_alert({
            message: __('You must select a customer before adding an item.'),
            indicator: 'orange'
        });
        frappe.utils.play_sound("error");
    }

    raise_served_by_selection_alert() {
        frappe.dom.unfreeze();
        frappe.show_alert({
            message: __('You must select served by before adding an item.'),
            indicator: 'red'
        });
        frappe.utils.play_sound("error");
    }

    get_item_from_frm({name, item_code, batch_no, uom, rate, mrp, title, update_rules}) {

        let item_row = null;
        if (name) {
            item_row = this.frm.doc.items.find(i => i.name == name);
        } else {
            // if item is clicked twice from item selector
            // then "item_code, batch_no, uom, rate" will help in getting the exact item
            // to increase the qty by one
            const has_batch_no = batch_no;
            item_row = this.frm.doc.items.find(
                i => i.item_code === item_code
                    && (!has_batch_no || (has_batch_no && i.batch_no === batch_no))
                    && (i.uom === uom)
                // && (i.rate == rate)
                // && (i.mrp == mrp)
                // && (i.title == title)
            );

        }
        return item_row || {};
    }

    edit_item_details_of(item_row) {
        this.item_details.toggle_item_details_section(item_row);
    }

    is_current_item_being_edited(item_row) {
        return item_row.name == this.item_details.current_item.name;
    }

    update_cart_html(item_row, remove_item) {
        this.cart.update_item_html(item_row, remove_item);
        this.cart.update_totals_section(this.frm);
    }

    check_serial_batch_selection_needed(item_row) {
        // right now item details is shown for every type of item.
        // if item details is not shown for every item then this fn will be needed
        const serialized = item_row.has_serial_no;
        const batched = item_row.has_batch_no;
        const no_serial_selected = !item_row.serial_no;
        const no_batch_selected = !item_row.batch_no;

        if ((serialized && no_serial_selected) || (batched && no_batch_selected) ||
            (serialized && batched && (no_batch_selected || no_serial_selected))) {
            return true;
        }
        return false;
    }

    async trigger_new_item_events(item_row) {
        await this.frm.script_manager.trigger('item_code', item_row.doctype, item_row.name);
        await this.frm.script_manager.trigger('qty', item_row.doctype, item_row.name);
    }

    async check_stock_availability(item_row, qty_needed, warehouse) {
        const available_qty = (await this.get_available_stock(item_row.item_code, warehouse)).message;

        frappe.dom.unfreeze();
        const bold_item_code = item_row.item_code.bold();
        const bold_warehouse = warehouse.bold();
        const bold_available_qty = available_qty.toString().bold()
        if (!(available_qty > 0)) {
            frappe.model.clear_doc(item_row.doctype, item_row.name);
            frappe.throw({
                title: __("Not Available"),
                message: __('Item Code: {0} is not available under warehouse {1}.', [bold_item_code, bold_warehouse])
            })
        } else if (available_qty < qty_needed) {
            frappe.show_alert({
                message: __('Stock quantity not enough for Item Code: {0} under warehouse {1}. Available quantity {2}.', [bold_item_code, bold_warehouse, bold_available_qty]),
                indicator: 'orange'
            });
            frappe.utils.play_sound("error");
        }
        frappe.dom.freeze();
    }

    async check_serial_no_availablilty(item_code, warehouse, serial_no) {
        const method = "erpnext.stock.doctype.serial_no.serial_no.get_pos_reserved_serial_nos";
        const args = {filters: {item_code, warehouse}}
        const res = await frappe.call({method, args});

        if (res.message.includes(serial_no)) {
            frappe.throw({
                title: __("Not Available"),
                message: __('Serial No: {0} has already been transacted into another POS Invoice.', [serial_no.bold()])
            });
        }
    }

    get_available_stock(item_code, warehouse) {
        const me = this;
        return frappe.call({
            method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
            args: {
                'item_code': item_code,
                'warehouse': warehouse,
            },
            callback(res) {
                if (!me.item_stock_map[item_code])
                    me.item_stock_map[item_code] = {}
                me.item_stock_map[item_code][warehouse] = res.message;
            }
        });
    }

    update_item_field(value, field_or_action) {
        if (field_or_action === 'checkout') {
            this.item_details.toggle_item_details_section(null);
        } else if (field_or_action === 'remove') {
            this.remove_item_from_cart();
        } else {
            const field_control = this.item_details[`${field_or_action}_control`];
            if (!field_control) return;
            field_control.set_focus();
            value != "" && field_control.set_value(value);
        }
    }

    remove_item_from_cart() {
        frappe.dom.freeze();
        const {doctype, name, current_item} = this.item_details;

        frappe.model.set_value(doctype, name, 'qty', 0)
            .then(() => {
                frappe.model.clear_doc(doctype, name);
                this.update_cart_html(current_item, true);
                this.item_details.toggle_item_details_section(null);
                frappe.dom.unfreeze();
            })
            .catch(e => console.log(e));
    }

    insert_invoice_print_log() {
        // inserting invoice printing log
        frappe.db.insert({
            "doctype": "Printing Log",
            "date": frappe.datetime.get_today(),
            "customer_name": this.frm.doc.customer_name,
            "customer": this.frm.doc.customer,
            "email": this.frm.doc.contact_email,
            "location": this.frm.doc.pos_profile,
            "mobile_number": this.frm.doc.contact_mobile,
            "invoice_number": this.frm.doc.name,
            "served_by": this.frm.doc.served_by,
            "company": this.frm.doc.company
        }).then(function (doc) {
            // console.log(doc);
        });
    }

    print_receipt() {
        const frm = this.frm

        // inserting the printing log
        this.insert_invoice_print_log()

        frappe.utils.print(
            this.frm.doc.doctype,
            this.frm.doc.name,
            this.frm.pos_print_format,
            this.frm.doc.letter_head,
            this.frm.doc.language || frappe.boot.lang
        );
    }

    set_cache_data(data) {
        frappe.call({
            method: 'bbb.bbb.pos_invoice.set_pos_cached_data',
            args: {
                "invoice_data": data,
            },
            callback: function (r) {
                if (!r.exc) {
                    // console.log(r);
                }
            }
        });
    }

    get_cache_data(me) {
        frappe.call({
            method: 'bbb.bbb.pos_invoice.get_pos_cached_data',
            callback: function (r) {
                if (!r.exc) {
                    me.cached_data = r.message;
                    // console.log(me.cached_data)
                }
            }
        });
    }

    async remove_single_item_from_cached(me){
        frappe.call({
            method: 'bbb.bbb.pos_invoice.get_pos_cached_data',
            callback: function (r) {
                if (!r.exc) {
                    me.cached_data = r.message;
                    // console.log(me.cached_data)
                }
            }
        });
    }

    async set_5_basis_rounded_total(number) {
        // rounding : M rounds to 5 basis ( 12.49 will be 10 and 12.5 will  be 15)
        let data = undefined
        if (number == undefined || number == null) {
            this.base_rounded_total = 0
        } else {
            let float_number = parseFloat(number);
            let int_number = parseInt(float_number);
            let divisible_number = (Math.floor(int_number / 5)) * 5;
            let adjustment = float_number - divisible_number;
            let rounded_total = 0;
            let rounded_adjustment = 0
            if (adjustment < 2.50) {
                rounded_total = divisible_number
                // rounded_adjustment = -(adjustment)
            } else if (adjustment > 2.49) {
                rounded_total = divisible_number + 5
                // rounded_adjustment = rounded_total - float_number
            }
            this.base_rounded_total = rounded_total;
        }
    }

    get_5_basis_rounded(number) {
        // rounding : M rounds to 5 basis ( 12.49 will be 10 and 12.5 will  be 15)
        let data = undefined
        if (number == undefined || number == null) {
            data = {
                'rounded_total': 0,
                'rounded_adjustment': 0
            }
            return 0
        } else {
            let float_number = parseFloat(number);
            let int_number = parseInt(float_number);
            let divisible_number = (Math.floor(int_number / 5)) * 5;
            let adjustment = float_number - divisible_number;
            let rounding_total = 0;
            let rounded_adjustment = 0
            if (adjustment < 2.50) {
                rounding_total = divisible_number
                rounded_adjustment = -(adjustment)
            } else if (adjustment > 2.49) {
                rounding_total = divisible_number + 5
                rounded_adjustment = rounding_total - float_number
            }
            data = {
                'rounded_total': rounding_total,
                'rounding_adjustment': rounded_adjustment.toFixed(2)
            }
            return rounding_total
        }

    }
    set_initial_paid_amount(paid_amount){
        this.initial_paid_amount = paid_amount;
    }
};