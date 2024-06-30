frappe.pages['detail-sales-report-'].on_page_load = (wrapper) =>{
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Detail Sales Report For Management',
		single_column: true
	});
    $('.page-body').css('background', '#FFFFFF');
    new erpnext.DetailSalesReport(page);
};

erpnext.DetailSalesReport = class DetailSalesReport {
    constructor(page) {
        this.page = page;
        this.make_form();
        this.make_menu();
    }
    make_menu = () =>{
        this.page.add_menu_item("Export", ()=>{
            let {from_date, to_date, outlet, switch_invoice} = this.form.get_values();
            if (!from_date) {
                this.form.get_field('preview').html('');
                return;
            }
            // frappe.call('bbb.bbb.page.detail_sales_report_.detail_sales_report_.generate_excel_data', {
            //     filters: {
            //         from_date: from_date,
            //         to_date: to_date,
            //         outlet: outlet,
            //         switch_invoice: switch_invoice
            //     },
            //     // freeze: true
            // }).then(r => {
            //     let url = r.message;
            //     window.open(url, '_blank');
            //     // window.location.href = diff;
            //     // setTimeout(function (){
            //     //     window.location.href = diff;
            //     // },2000)
            //
            // });

            var url = `/api/method/bbb.bbb.page.detail_sales_report_.detail_sales_report_.generate_excel_data`;
            url = url + `?from_date=${from_date}&to_date=${to_date || ''}&outlet=${outlet || ''}&switch_invoice=${switch_invoice}`;
            // window.open(url, '_blank');
            window.location.href = url;

        });

        // this.page.add_action_icon('', ()=>{
        //     let {from_date, to_date, outlet, switch_invoice} = this.form.get_values();
        //     if (!from_date) {
        //         this.form.get_field('preview').html('');
        //         return;
        //     }
        //     frappe.call('bbb.bbb.page.detail_sales_report_.detail_sales_report_.generate_table_data', {
        //         filters: {
        //             from_date: from_date,
        //             to_date: to_date,
        //             outlet: outlet,
        //             switch_invoice: switch_invoice
        //         },
        //         freeze: true
        //     }).then(r => {
        //         let diff = r.message;
        //         this.render(switch_invoice, diff);
        //     });
        // });
    }

    // download_group_file: function (frm) {
    //     if (has_ga_file(frm)) {
    //         var url = `/api/method/generate_analysis.generate_analysis.doctype.generate_analysis.generate_analysis.download_group_file`;
    //         url = url + `?ga_name=${frm.doc.name}`;
    //         window.open(url, '_blank');
    //     }
    //     else{
    //         frappe.msgprint("There is no generate analysis file on Generate Analysis Brands");
    //     }
    // },
    make_form = () => {
        this.form = new frappe.ui.FieldGroup({
            fields: [
                {

                    fieldname: 'from_date',
                    label: __('From Date'),
                    fieldtype: 'Date',
                    default: frappe.datetime.get_today(),
                    change: () => this.fetch_and_render(),
                    reqd: 1,
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'to_date',
                    label: __('To Date'),
                    fieldtype: 'Date',
                    default: frappe.datetime.get_today(),
                    change: () => this.fetch_and_render(),
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'outlet',
                    label: __('Outlet'),
                    fieldtype: 'Link',
                    change: () => this.fetch_and_render(),
                    options: 'POS Profile',
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'switch_invoice',
                    label: __('Switch Invoice'),
                    fieldtype: 'Select',
                    options: [
                        { "value": "POS Invoice", "label": __("POS Invoice") },
                        { "value": "Sales Invoice", "label": __("Sales Invoice"), "disabled": "disabled"},
                    ],
                    default: 'POS Invoice',
                    change: () => this.fetch_and_render(),
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'company',
                    label: __('Company'),
                    fieldtype: 'Link',
                    options: 'Company',
                    default: frappe.defaults.get_user_default("Company") ,
                    change: () => this.fetch_and_render(),
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'preview'
                }
            ],
            body: this.page.body
        });
        this.form.make();
    }

    fetch_and_render = () => {
        let {from_date, to_date, outlet, switch_invoice,company} = this.form.get_values();
        if (!from_date) {
            this.form.get_field('preview').html('');
            return;
        }
        this.form.get_field('preview').html(`
        	<div class="text-muted margin-top">
        		${__("Fetching...")}
        	</div>
        `);
        frappe.call('bbb.bbb.page.detail_sales_report_.detail_sales_report_.generate_table_data', {
            filters: {
                from_date: from_date,
                to_date: to_date,
                outlet: outlet,
                switch_invoice: switch_invoice,
                company:company
            },
            freeze: true
        }).then(r => {
            let diff = r.message;
            this.render(switch_invoice, diff);
        });
    }

    render = (switch_invoice, diff) => {
        let table_header = this.table_header();
        let table_body = this.table_body(diff);
        this.form.get_field('preview').html(`<table class="table table-bordered" id="export_excel">${table_header}${table_body}</table>`);
    }

    table_header = () =>{
        let table_header ='<thead>\n' +
            '    <tr>\n' +
            '      <th scope="col" >SL</th>\n' +
            '      <th scope="col">Invoice No/Customer</th>\n' +
            '      <th scope="col" colspan="6">Description</th>\n' +
            '      <th scope="col">Sales Person</th>\n' +
            '      <th scope="col">Store Name</th>\n' +
            '      <th scope="col">Special Discount</th>\n' +
            '      <th scope="col">Round</th>\n' +
            '      <th scope="col">VAT</th>\n' +
            '      <th scope="col">Total Amount</th>\n' +
            '      <th scope="col">Exchange</th>\n' +
            '      <th scope="col">Profit/Loss</th>\n' +
            '      <th scope="col">Total</th>\n' +
            '    </tr>\n' +
            '  </thead>\n';
        return table_header;
    }
    table_body = (diff) =>{
        var html = "<tbody>";
        for (var key in diff) {
            html+=diff[key].join(" ");
        }
        html+="</tbody>";
        return html
    }
};