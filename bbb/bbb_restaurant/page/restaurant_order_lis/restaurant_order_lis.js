frappe.pages['restaurant-order-lis'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Restaurant Order List'),
		single_column: true
	});
	$('.page-body').css('background', '#FFFFFF');
	$('.main-section').css('background', '#FFFFFF');

	const restaurant = new frappe.Restaurant(page);

	frappe.realtime.on("list_update", (data) => {
		let doctype = data.doctype;
		if(doctype === 'POS Invoice'){
			frappe.utils.play_sound("submit");
			restaurant.update_item_or_status(data)

		}
	});
}

frappe.Restaurant = class RestaturantOrderList {

		update_item_or_status = (data) =>{
			const me = this
			var items_td = $(`[docname=${data.docname}]`)[0];
			var items = items_td.innerHTML
			if(items !== undefined){
				frappe.db.get_value(data.doctype, data.docname, ['docstatus', 'restaurant_order_item_html']).then((r) => {
					let values = r.message;
					if(values.docstatus === 0){
						let child_items = diff[key].child_items || ""
						child_items = child_items.split("<hr>")
						let html=''
						if(child_items.length === 2){
							html+= `<div class="old_item" style="font-weight: : 600"> ${child_items[0] || ''} </div><hr><div class="new_item font-weight-bold text-danger"> ${child_items[1] || ''} </div>`
						}else if (child_items.length === 1){
							html+= '<div class="old_item" style="font-weight: : 600">' + child_items[0] || '' + '</div>'
						}else{
							html+= '<div class="old_item" style="font-weight: : 600">' + child_items || '' + '</div>'
						}
						items_td.innerHTML = html
					}
				})
			}

		}

		constructor(page) {
			this.page = page;
			this.make_form();
			this.fetch_and_render()
			page.set_secondary_action('Refresh', () => this.fetch_and_render(), 'refresh');
		}

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
                    fieldname: 'pos_profile',
                    label: __('Outlet'),
                    fieldtype: 'Link',
                    change: () => this.fetch_and_render(),
                    options: 'POS Profile',
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'invoice',
                    label: __('Invoice'),
                    fieldtype: 'Link',
                    options: 'POS Invoice',
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
			let {from_date, to_date, pos_profile, invoice,company} = this.form.get_values();
			frappe.call('bbb.bbb_restaurant.methods.utils.get_restaurant_order_list_update', {
				filters: {
					from_date: from_date,
					to_date: to_date,
					pos_profile: pos_profile,
					invoice: invoice,
					company: company,
				},
				freeze: true
			}).then(r => {
				let diff = r.message;
				this.render(diff);

				$('.edit_invoice').on('click', function(e){
					e.preventDefault();
					let name = $(this).attr('name')
					// frappe.set_route(`/app/bbb-restaurant?name=${name}&type=view`, '_blank')
					window.open(`/app/bbb-restaurant?name=${name}&type=edit`, '_blank')
				});


				$('.view_invoice').on('click', function(e){
					e.preventDefault();
					let name = $(this).attr('name')
					// frappe.set_route("app", "bbb-restaurant", {'doctype': 'POS Invoice', 'docname': name});
					// frappe.set_route(`/app/bbb-restaurant?name=${name}&type=edit`, '_blank')
					window.open(`/app/bbb-restaurant?name=${name}&type=view`, '_blank')
				})
			});
		}	
		render = (diff) => {
			let table_header = this.table_header();
			let table_body = this.table_body(diff);
			this.form.get_field('preview').html(`<table class="table table-bordered" id="export_excel">${table_header}${table_body}</table>`);

		}
		table_header = () =>{
			let table_header ='<thead>\n' +
				'    <tr>\n' +
				'      <th scope="col" width="17%">Voucher</th>\n' +
				'      <th scope="col" width="8%">Table</th>\n' +
				'      <th scope="col" width="50%">Items</th>\n' +
				'      <th scope="col" width="3%">Qty</th>\n' +
				'      <th scope="col" width="8%">Status</th>\n' +
				'      <th scope="col" width="10%">Amount</th>\n' +
				'      <th scope="col" width="5%">Modify</th>\n' +
				'      <th scope="col" width="5%">Final Bill</th>\n' +
				'    </tr>\n' +
				'  </thead>\n';
			return table_header;
		}
		table_body = (diff) =>{
			var html = "<tbody class='restaurant_order'>";
			for (var key in diff) {
				let status_color = diff[key].status === 'Ordered' ? 'text-warning': diff[key].status === 'Processing' ? 'text-primary' : diff[key].status === 'Ready' ? 'text-success' : ''
				let child_items = diff[key].child_items || ""

				html+='<tr class="tr_body">'
				html+= '<td class="name">' + diff[key].name || '' + '</td>'
				html+= '<td class="">' + diff[key].restaurant_table_number || '' + '</td>'
				
				let items = ''
				diff[key].items.forEach(r => {
					console.log(r)
					items += `<p> ${r["item_name"]} --- ${r["qty"]}</p>`
				})
				html+= '<td class="">' + items + '</td>'
				html+= '<td class="">' + diff[key].total_qty || '' + '</td>'
				html+= '<td class="text '+ status_color +'">' + diff[key].status || '' + '</td>'
				html+= '<td class="">' + format_currency(diff[key].rounded_total, 'BDT') || '' + '</td>'
				html+= '<td><button type="button" class="btn btn-primary edit_invoice" name="'+ diff[key].name +'">Edit</button></td>'
				html+= '<td><button type="button" class="btn btn-success view_invoice" name="'+ diff[key].name +'">View</button></td>'
				html+='</tr>'
			}
			html+="</tbody>";
			return html
		}

	};
