frappe.pages['restaurant-order-lis-1'].on_page_load = function(wrapper) {
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
				frappe.db.get_value(data.doctype, data.docname, 'docstatus').then((r) => {
					let values = r.message;
					if(values.docstatus === 0){
						let old_item = items.split(', ')
						let new_item = ['Bread*1', 'Burger*2', 'Rice*6']
						frappe.call('bbb.bbb_restaurant.methods.utils.get_restaurant_order_new_list', {
							filters: {
								docname: data.docname,
							},
							freeze: true,
						}).then(r => {
							let new_item = r.message.child_items;
							let new_items = me.get_new_item(old_item, new_item)
							items_td.innerHTML = old_item + '\n' + new_items
						});
					}
				})
			}

		}

		get_new_item(old_item, new_item){
			function splitItem(item) {
				let parts = item.split('*');
				return {
					name: parts[0],
					value: parseInt(parts[1])
				};
			}

			// Find the differences
			let differences = [];
			$.each(new_item, function(index, newItem) {
				let newItemInfo = splitItem(newItem);
				let found = false;
				$.each(old_item, function(index, oldItem) {
					let oldItemInfo = splitItem(oldItem);
					if (newItemInfo.name === oldItemInfo.name) {
						if (newItemInfo.value !== oldItemInfo.value) {
							differences.push(oldItem);
						}
						found = true;
						return false; // Exit the loop early since a match is found
					}
				});
				if (!found) {
					differences.push(newItem);
				}
			});
			return differences;
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
										status_td.html("Ready")
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


			var docname = 'ACC-PSINV-2024030439995';
			var items_td = $(`[docname=${docname}]`)[0];
			let items = 'Rice * 2 <br> Burger * 3 <hr class="text-warning"> <span class="text-danger text-bold"> Rice * 1</span>'
			items_td.innerHTML = items
			// var items = $(`[docname=${docname}]`)[0].innerHTML;
			// frappe.call('bbb.bbb_restaurant.methods.utils.get_restaurant_order_new_list', {
			// 	filters: {
			// 		docname: docname,
            // 	},
			// 	freeze: true,
			// }).then(r => {
			// 	let new_item = r.message.child_items;
			//
			// });
		}
		table_header = () =>{
			let table_header ='<thead>\n' +
				'    <tr>\n' +
				'      <th scope="col" width="17%">Voucher</th>\n' +
				'      <th scope="col" width="10%">Table</th>\n' +
				'      <th scope="col" width="33%">Items</th>\n' +
				'      <th scope="col" width="10%">Qty</th>\n' +
				'      <th scope="col" width="10%">Status</th>\n' +
				'      <th scope="col" width="10%">Amount</th>\n' +
				'      <th scope="col" width="10%">Action</th>\n' +
				'    </tr>\n' +
				'  </thead>\n';
			return table_header;
		}
		table_body = (diff) =>{
			var html = "<tbody class='restaurant_order'>";
			for (var key in diff) {
				let status_color = diff[key].status === 'Ordered' ? 'text-warning': diff[key].status === 'Processing' ? 'text-primary' : diff[key].status === 'Ready' ? 'text-success' : ''
				let btn_color = diff[key].status === 'Ordered' ? 'btn-warning': diff[key].status === 'Processing' ? 'btn-primary' : diff[key].status === 'Ready' ? 'btn-success' : '';
				let status = diff[key].status === 'Ordered' ? 'Start Processing': diff[key].status === 'Processing' ? 'Press to complete' : diff[key].status === 'Ready' ? 'Ready' : ''
				html+='<tr class="tr_body">'
				html+= '<td class="name">' + diff[key].name || '' + '</td>'
				html+= '<td class="">' + diff[key].restaurant_table_number || '' + '</td>'
				html+= '<td class="child_items" docname="'+ diff[key].name +'">' + diff[key].child_items || '' + '</td>'
				html+= '<td class="">' + diff[key].total_qty || '' + '</td>'
				html+= '<td class="text '+ status_color +' doc_status">' + diff[key].status || '' + '</td>'
				html+= '<td class="">' + format_currency(diff[key].rounded_total, 'BDT') || '' + '</td>'
				html+= '<td><button type="button" class="btn ' + btn_color + ' start_processsing" status="'+ diff[key].status +'" name="'+ diff[key].name +'">'+status+'</button></td>'
				html+='</tr>'
			}
			html+="</tbody>";
			return html
		}

	};
