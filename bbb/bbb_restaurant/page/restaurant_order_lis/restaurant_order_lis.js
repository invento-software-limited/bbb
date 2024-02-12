frappe.pages['restaurant-order-lis'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Restaurant Order List'),
		single_column: true
	});
	$('.page-body').css('background', '#FFFFFF');
	$('.main-section').css('background', '#FFFFFF');
	
	new frappe.Restaurant(page);
}

frappe.Restaurant= class RestaturantOrderList {
	// frappe.pages['detail-sales-report'].on_page_load = (wrapper) =>{

	// 	var page = frappe.ui.make_app_page({
	// 		parent: wrapper,
	// 		title: 'Detail Sales Report',
	// 		single_column: true
	// 	});
	// 	$('.page-body').css('background', '#FFFFFF');
	// 	new erpnext.DetailSalesReport(page);
	// };
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
						fieldtype: 'HTML',
						fieldname: 'preview'
					}
				],
				body: this.page.body
			});
			this.form.make();
		}
	
		fetch_and_render = () => {
			frappe.call('bbb.bbb_restaurant.methods.utils.get_restaurant_order_list', {
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
				'      <th scope="col" width="10%">Table</th>\n' +
				'      <th scope="col" width="36%">Items</th>\n' +
				'      <th scope="col" width="7%">Qty</th>\n' +
				'      <th scope="col" width="10%">Amount</th>\n' +
				'      <th scope="col" width="10%">Modify</th>\n' +
				'      <th scope="col" width="10%">Final Bill</th>\n' +
				'    </tr>\n' +
				'  </thead>\n';
			return table_header;
		}
		table_body = (diff) =>{
			var html = "<tbody>";
			for (var key in diff) {
				// html+=diff[key].join(" ");
				html+='<tr>'
				html+= '<td>' + diff[key].name || '' + '</td>'
				html+= '<td>' + diff[key].restaurant_table_number || '' + '</td>'
				html+= '<td>' + diff[key].child_items || '' + '</td>'
				html+= '<td>' + diff[key].total_qty || '' + '</td>'
				html+= '<td>' + format_currency(diff[key].rounded_total, 'BDT') || '' + '</td>'
				html+= '<td><button type="button" class="btn btn-primary edit_invoice" name="'+ diff[key].name +'">Edit</button></td>'
				html+= '<td><button type="button" class="btn btn-success view_invoice" name="'+ diff[key].name +'">View</button></td>'
				html+='</tr>'
			}
			html+="</tbody>";
			return html
		}

	};
