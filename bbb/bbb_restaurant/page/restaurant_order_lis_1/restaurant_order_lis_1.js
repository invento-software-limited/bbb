frappe.pages['restaurant-order-lis-1'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Restaurant Order List For Kitchen'),
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
			frappe.call('bbb.bbb_restaurant.methods.utils.get_restaurant_order_list', {
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

				$('.start_processsing').on('click', function(e){
					e.preventDefault();
					const me = $(this);
					let name = $(this).attr('name');
					let status = $(this).attr('status');
					if(status  === 'Ordered' || status === 'Processing') {
						frappe.confirm('Are you sure you want to proceed?',
							() => {
								frappe.call('bbb.bbb_restaurant.methods.utils.update_pos_status', {
									filters: {
										docname: name,
									},
									freeze: true,
								}).then(r => {
									// console.log(r.message)
									// console.log(me)
									if (r.message === 'Processing') {
										me.html('Press to complete')
										me.removeClass('btn-warning')
										me.addClass('btn-primary')
										let status_td = me.parent().siblings('td.doc_status')
										status_td.html("Processing")
										status_td.removeClass('text-warning')
										status_td.addClass('text-primary')
									}

									if (r.message === 'Ready') {
										me.html('Ready')
										me.removeClass('btn-primary')
										me.addClass('btn-success')
										let status_td = me.parent().siblings('td.doc_status')
										status_td.html("Ready")
										status_td.removeClass('text-primary')
										status_td.addClass('text-success')
									}
								});

							}, () => {
								// action to perform if No is selected
							})
					}
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
				'      <th scope="col" width="6%">Table</th>\n' +
				'      <th scope="col" width="50%">Items</th>\n' +
				'      <th scope="col" width="7%">Total Qty</th>\n' +
				'      <th scope="col" width="10%">Status</th>\n' +
				'    </tr>\n' +
				'  </thead>\n';
			return table_header;
		}
		table_body = (diff) =>{
			var html = "<tbody class='restaurant_order'>";
			for (var key in diff) {
				if (diff[key].status !== "Ready") {
					let status_color = diff[key].status === 'Ordered' ? 'text-warning': diff[key].status === 'Processing' ? 'text-primary' : diff[key].status === 'Ready' ? 'text-success' : ''
					let btn_color = diff[key].status === 'Ordered' ? 'btn-warning': diff[key].status === 'Processing' ? 'btn-primary' : diff[key].status === 'Ready' ? 'btn-success' : '';
					let status = diff[key].status === 'Ordered' ? 'Process': diff[key].status === 'Processing' ? 'Press to complete' : diff[key].status === 'Ready' ? 'Ready' : ''

					let child_items = diff[key].child_items || ""
					child_items = child_items.split("<hr>")
					console.log(child_items)
					html+='<tr class="tr_body">'
					html+= '<td class="name">' + diff[key].name || '' + '</td>'
					html+= '<td class="">' + diff[key].restaurant_table_number || '' + '</td>'
					if(child_items.length === 2){
						console.log("pp")
						html+= `<td class="child_items" docname="${diff[key].name || ''}"><div class="old_item" style="font-weight: : 600"> ${child_items[0] || ''} </div><hr class="m-2"><div class="new_item font-weight-bold text-danger"> ${child_items[1] || ''} </div></td>`
					}else if (child_items.length === 1){
						console.log("eee")
						html+= '<td class="child_items" docname="'+ diff[key].name +'"><div class="old_item" style="font-weight: : 600">' + child_items[0] || '' + '</div></td>'
					}else{
						console.log("bbbb")
						html+= '<td class="child_items" docname="'+ diff[key].name +'"><div class="old_item" style="font-weight: : 600">' + child_items || '' + '</div></td>'
					}
					html+= '<td class="">' + diff[key].total_qty || '' + '</td>'
					html+= '<td class="text '+ status_color +' doc_status">' + diff[key].status || '' + '</td>'
					html+= '<td><button type="button" class="btn ' + btn_color + ' start_processsing" status="'+ diff[key].status +'" name="'+ diff[key].name +'">'+status+'</button></td>'
					html+='</tr>'
				}
			}
			html+="</tbody>";
			return html
		}

	};
