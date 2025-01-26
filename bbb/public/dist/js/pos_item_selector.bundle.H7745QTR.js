(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // ../erpnext/node_modules/onscan.js/onscan.js
  var require_onscan = __commonJS({
    "../erpnext/node_modules/onscan.js/onscan.js"(exports, module) {
      (function(global, factory) {
        typeof exports === "object" && typeof module !== "undefined" ? module.exports = factory() : typeof define === "function" && define.amd ? define(factory()) : global.onScan = factory();
      })(exports, function() {
        var onScan2 = {
          attachTo: function(oDomElement, oOptions) {
            if (oDomElement.scannerDetectionData !== void 0) {
              throw new Error("onScan.js is already initialized for DOM element " + oDomElement);
            }
            var oDefaults = {
              onScan: function(sScanned, iQty) {
              },
              onScanError: function(oDebug) {
              },
              onKeyProcess: function(sChar, oEvent) {
              },
              onKeyDetect: function(iKeyCode, oEvent) {
              },
              onPaste: function(sPasted, oEvent) {
              },
              keyCodeMapper: function(oEvent) {
                return onScan2.decodeKeyEvent(oEvent);
              },
              onScanButtonLongPress: function() {
              },
              scanButtonKeyCode: false,
              scanButtonLongPressTime: 500,
              timeBeforeScanTest: 100,
              avgTimeByChar: 30,
              minLength: 6,
              suffixKeyCodes: [9, 13],
              prefixKeyCodes: [],
              ignoreIfFocusOn: false,
              stopPropagation: false,
              preventDefault: false,
              captureEvents: false,
              reactToKeydown: true,
              reactToPaste: false,
              singleScanQty: 1
            };
            oOptions = this._mergeOptions(oDefaults, oOptions);
            oDomElement.scannerDetectionData = {
              options: oOptions,
              vars: {
                firstCharTime: 0,
                lastCharTime: 0,
                accumulatedString: "",
                testTimer: false,
                longPressTimeStart: 0,
                longPressed: false
              }
            };
            if (oOptions.reactToPaste === true) {
              oDomElement.addEventListener("paste", this._handlePaste, oOptions.captureEvents);
            }
            if (oOptions.scanButtonKeyCode !== false) {
              oDomElement.addEventListener("keyup", this._handleKeyUp, oOptions.captureEvents);
            }
            if (oOptions.reactToKeydown === true || oOptions.scanButtonKeyCode !== false) {
              oDomElement.addEventListener("keydown", this._handleKeyDown, oOptions.captureEvents);
            }
            return this;
          },
          detachFrom: function(oDomElement) {
            if (oDomElement.scannerDetectionData.options.reactToPaste) {
              oDomElement.removeEventListener("paste", this._handlePaste);
            }
            if (oDomElement.scannerDetectionData.options.scanButtonKeyCode !== false) {
              oDomElement.removeEventListener("keyup", this._handleKeyUp);
            }
            oDomElement.removeEventListener("keydown", this._handleKeyDown);
            oDomElement.scannerDetectionData = void 0;
            return;
          },
          getOptions: function(oDomElement) {
            return oDomElement.scannerDetectionData.options;
          },
          setOptions: function(oDomElement, oOptions) {
            switch (oDomElement.scannerDetectionData.options.reactToPaste) {
              case true:
                if (oOptions.reactToPaste === false) {
                  oDomElement.removeEventListener("paste", this._handlePaste);
                }
                break;
              case false:
                if (oOptions.reactToPaste === true) {
                  oDomElement.addEventListener("paste", this._handlePaste);
                }
                break;
            }
            switch (oDomElement.scannerDetectionData.options.scanButtonKeyCode) {
              case false:
                if (oOptions.scanButtonKeyCode !== false) {
                  oDomElement.addEventListener("keyup", this._handleKeyUp);
                }
                break;
              default:
                if (oOptions.scanButtonKeyCode === false) {
                  oDomElement.removeEventListener("keyup", this._handleKeyUp);
                }
                break;
            }
            oDomElement.scannerDetectionData.options = this._mergeOptions(oDomElement.scannerDetectionData.options, oOptions);
            this._reinitialize(oDomElement);
            return this;
          },
          decodeKeyEvent: function(oEvent) {
            var iCode = this._getNormalizedKeyNum(oEvent);
            switch (true) {
              case (iCode >= 48 && iCode <= 90):
              case (iCode >= 106 && iCode <= 111):
                if (oEvent.key !== void 0 && oEvent.key !== "") {
                  return oEvent.key;
                }
                var sDecoded = String.fromCharCode(iCode);
                switch (oEvent.shiftKey) {
                  case false:
                    sDecoded = sDecoded.toLowerCase();
                    break;
                  case true:
                    sDecoded = sDecoded.toUpperCase();
                    break;
                }
                return sDecoded;
              case (iCode >= 96 && iCode <= 105):
                return 0 + (iCode - 96);
            }
            return "";
          },
          simulate: function(oDomElement, mStringOrArray) {
            this._reinitialize(oDomElement);
            if (Array.isArray(mStringOrArray)) {
              mStringOrArray.forEach(function(mKey) {
                var oEventProps = {};
                if ((typeof mKey === "object" || typeof mKey === "function") && mKey !== null) {
                  oEventProps = mKey;
                } else {
                  oEventProps.keyCode = parseInt(mKey);
                }
                var oEvent = new KeyboardEvent("keydown", oEventProps);
                document.dispatchEvent(oEvent);
              });
            } else {
              this._validateScanCode(oDomElement, mStringOrArray);
            }
            return this;
          },
          _reinitialize: function(oDomElement) {
            var oVars = oDomElement.scannerDetectionData.vars;
            oVars.firstCharTime = 0;
            oVars.lastCharTime = 0;
            oVars.accumulatedString = "";
            return;
          },
          _isFocusOnIgnoredElement: function(oDomElement) {
            var ignoreSelectors = oDomElement.scannerDetectionData.options.ignoreIfFocusOn;
            if (!ignoreSelectors) {
              return false;
            }
            var oFocused = document.activeElement;
            if (Array.isArray(ignoreSelectors)) {
              for (var i = 0; i < ignoreSelectors.length; i++) {
                if (oFocused.matches(ignoreSelectors[i]) === true) {
                  return true;
                }
              }
            } else if (oFocused.matches(ignoreSelectors)) {
              return true;
            }
            return false;
          },
          _validateScanCode: function(oDomElement, sScanCode) {
            var oScannerData = oDomElement.scannerDetectionData;
            var oOptions = oScannerData.options;
            var iSingleScanQty = oScannerData.options.singleScanQty;
            var iFirstCharTime = oScannerData.vars.firstCharTime;
            var iLastCharTime = oScannerData.vars.lastCharTime;
            var oScanError = {};
            var oEvent;
            switch (true) {
              case sScanCode.length < oOptions.minLength:
                oScanError = {
                  message: "Receieved code is shorter then minimal length"
                };
                break;
              case iLastCharTime - iFirstCharTime > sScanCode.length * oOptions.avgTimeByChar:
                oScanError = {
                  message: "Receieved code was not entered in time"
                };
                break;
              default:
                oOptions.onScan.call(oDomElement, sScanCode, iSingleScanQty);
                oEvent = new CustomEvent(
                  "scan",
                  {
                    detail: {
                      scanCode: sScanCode,
                      qty: iSingleScanQty
                    }
                  }
                );
                oDomElement.dispatchEvent(oEvent);
                onScan2._reinitialize(oDomElement);
                return true;
            }
            oScanError.scanCode = sScanCode;
            oScanError.scanDuration = iLastCharTime - iFirstCharTime;
            oScanError.avgTimeByChar = oOptions.avgTimeByChar;
            oScanError.minLength = oOptions.minLength;
            oOptions.onScanError.call(oDomElement, oScanError);
            oEvent = new CustomEvent(
              "scanError",
              { detail: oScanError }
            );
            oDomElement.dispatchEvent(oEvent);
            onScan2._reinitialize(oDomElement);
            return false;
          },
          _mergeOptions: function(oDefaults, oOptions) {
            var oExtended = {};
            var prop;
            for (prop in oDefaults) {
              if (Object.prototype.hasOwnProperty.call(oDefaults, prop)) {
                oExtended[prop] = oDefaults[prop];
              }
            }
            for (prop in oOptions) {
              if (Object.prototype.hasOwnProperty.call(oOptions, prop)) {
                oExtended[prop] = oOptions[prop];
              }
            }
            return oExtended;
          },
          _getNormalizedKeyNum: function(e) {
            return e.which || e.keyCode;
          },
          _handleKeyDown: function(e) {
            var iKeyCode = onScan2._getNormalizedKeyNum(e);
            var oOptions = this.scannerDetectionData.options;
            var oVars = this.scannerDetectionData.vars;
            var bScanFinished = false;
            if (oOptions.onKeyDetect.call(this, iKeyCode, e) === false) {
              return;
            }
            if (onScan2._isFocusOnIgnoredElement(this)) {
              return;
            }
            if (oOptions.scanButtonKeyCode !== false && iKeyCode == oOptions.scanButtonKeyCode) {
              if (!oVars.longPressed) {
                oVars.longPressTimer = setTimeout(oOptions.onScanButtonLongPress, oOptions.scanButtonLongPressTime, this);
                oVars.longPressed = true;
              }
              return;
            }
            switch (true) {
              case (oVars.firstCharTime && oOptions.suffixKeyCodes.indexOf(iKeyCode) !== -1):
                e.preventDefault();
                e.stopImmediatePropagation();
                bScanFinished = true;
                break;
              case (!oVars.firstCharTime && oOptions.prefixKeyCodes.indexOf(iKeyCode) !== -1):
                e.preventDefault();
                e.stopImmediatePropagation();
                bScanFinished = false;
                break;
              default:
                var character = oOptions.keyCodeMapper.call(this, e);
                if (character === null) {
                  return;
                }
                oVars.accumulatedString += character;
                if (oOptions.preventDefault) {
                  e.preventDefault();
                }
                if (oOptions.stopPropagation) {
                  e.stopImmediatePropagation();
                }
                bScanFinished = false;
                break;
            }
            if (!oVars.firstCharTime) {
              oVars.firstCharTime = Date.now();
            }
            oVars.lastCharTime = Date.now();
            if (oVars.testTimer) {
              clearTimeout(oVars.testTimer);
            }
            if (bScanFinished) {
              onScan2._validateScanCode(this, oVars.accumulatedString);
              oVars.testTimer = false;
            } else {
              oVars.testTimer = setTimeout(onScan2._validateScanCode, oOptions.timeBeforeScanTest, this, oVars.accumulatedString);
            }
            oOptions.onKeyProcess.call(this, character, e);
            return;
          },
          _handlePaste: function(e) {
            var oOptions = this.scannerDetectionData.options;
            var oVars = this.scannerDetectionData.vars;
            var sPasteString = (event.clipboardData || window.clipboardData).getData("text");
            if (onScan2._isFocusOnIgnoredElement(this)) {
              return;
            }
            e.preventDefault();
            if (oOptions.stopPropagation) {
              e.stopImmediatePropagation();
            }
            oOptions.onPaste.call(this, sPasteString, event);
            oVars.firstCharTime = 0;
            oVars.lastCharTime = 0;
            onScan2._validateScanCode(this, sPasteString);
            return;
          },
          _handleKeyUp: function(e) {
            if (onScan2._isFocusOnIgnoredElement(this)) {
              return;
            }
            var iKeyCode = onScan2._getNormalizedKeyNum(e);
            if (iKeyCode == this.scannerDetectionData.options.scanButtonKeyCode) {
              clearTimeout(this.scannerDetectionData.vars.longPressTimer);
              this.scannerDetectionData.vars.longPressed = false;
            }
            return;
          },
          isScanInProgressFor: function(oDomElement) {
            return oDomElement.scannerDetectionData.vars.firstCharTime > 0;
          },
          isAttachedTo: function(oDomElement) {
            return oDomElement.scannerDetectionData !== void 0;
          }
        };
        return onScan2;
      });
    }
  });

  // ../bbb/bbb/public/js/point_of_sale/pos_item_selector.bundle.js
  var import_onscan = __toESM(require_onscan());
  erpnext.PointOfSale.ItemSelector = class {
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
      this.$component = this.wrapper.find(".items-selector");
      this.$items_container = this.$component.find(".items-container");
    }
    async load_items_data() {
      if (!this.item_group) {
        const res = await frappe.db.get_value("Item Group", { lft: 1, is_group: 1 }, "name");
        this.parent_item_group = res.message.name;
      }
      if (!this.price_list) {
        const res = await frappe.db.get_value("POS Profile", this.pos_profile, "selling_price_list");
        this.price_list = res.message.selling_price_list;
      }
      this.get_items({}).then(({ message }) => {
        this.render_item_list(message.items);
      });
    }
    get_items({ start = 0, page_length = 40, search_term = "" }) {
      const doc = this.events.get_frm().doc;
      const price_list = doc && doc.selling_price_list || this.price_list;
      let { item_group, pos_profile } = this;
      !item_group && (item_group = this.parent_item_group);
      return frappe.call({
        method: "bbb.bbb.point_of_sale.get_items",
        freeze: true,
        args: { start, page_length, price_list, item_group, search_term, pos_profile }
      });
    }
    render_item_list(items) {
      this.$items_container.html("");
      items.forEach((item) => {
        const item_html = this.get_item_html(item);
        this.$items_container.append(item_html);
      });
    }
    get_item_html(item) {
      const me = this;
      const { item_image, serial_no, batch_no, barcode, actual_qty, mrp, stock_uom, price_list_rate, start_date, end_date, discount_amount, price_rule_tag } = item;
      const indicator_color = actual_qty > 10 ? "green" : actual_qty <= 0 ? "red" : "orange";
      const precision = flt(price_list_rate, 2) % 1 != 0 ? 2 : 0;
      let qty_to_display = actual_qty;
      if (Math.round(qty_to_display) > 999) {
        qty_to_display = Math.round(qty_to_display) / 1e3;
        qty_to_display = qty_to_display.toFixed(1) + "K";
      }
      function get_item_image_html() {
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
      let tag = null;
      if (price_rule_tag) {
        tag = price_rule_tag.split(" ").join("INV");
      }
      return `<div class="item-wrapper"
				data-item-code="${escape(item.item_code)}" data-serial-no="${escape(serial_no)}"
				data-batch-no="${escape(batch_no)}" data-uom="${escape(stock_uom)}" data-start-date="${escape(item.start_date)}"
				data-end-date="${escape(item.end_date)}" data-discount-amount="${escape(item.discount_amount)}"
				data-rate="${escape(price_list_rate || 0)}" data-mrp="${escape(price_list_rate || 0)}" data-tag="${escape(tag || "")}"
				title="${item.item_name}">

				${get_item_image_html()}

				<div class="item-detail">
				<!--
					<div class="item-name">
						${frappe.ellipsis(item.item_name, 18)}
					</div>-->
					<div class="item-rate">${format_currency(price_list_rate, item.currency, precision) || 0}</div>
				</div>
			</div>`;
    }
    handle_broken_image($img) {
      const item_abbr = $($img).attr("alt");
      $($img).parent().replaceWith(`<div class="item-display abbr">${item_abbr}</div>`);
    }
    make_search_bar() {
      const me = this;
      const doc = me.events.get_frm().doc;
      this.$component.find(".search-field").html("");
      this.$component.find(".item-group-field").html("");
      this.search_field = frappe.ui.form.make_control({
        df: {
          label: __("Search"),
          fieldtype: "Data",
          placeholder: __("Search by item code, serial number or barcode")
        },
        parent: this.$component.find(".search-field"),
        render_input: true
      });
      this.item_group_field = frappe.ui.form.make_control({
        df: {
          label: __("Item Group"),
          fieldtype: "Link",
          options: "Item Group",
          placeholder: __("Select item group"),
          onchange: function() {
            me.item_group = this.value;
            !me.item_group && (me.item_group = me.parent_item_group);
            me.filter_items();
          },
          get_query: function() {
            return {
              query: "erpnext.selling.page.point_of_sale.point_of_sale.item_group_query",
              filters: {
                pos_profile: doc ? doc.pos_profile : ""
              }
            };
          }
        },
        parent: this.$component.find(".item-group-field"),
        render_input: true
      });
      this.search_field.toggle_label(false);
      this.item_group_field.toggle_label(false);
    }
    set_search_value(value) {
      $(this.search_field.$input[0]).val(value).trigger("input");
    }
    bind_events() {
      const me = this;
      window.onScan = import_onscan.default;
      import_onscan.default.decodeKeyEvent = function(oEvent) {
        var iCode = this._getNormalizedKeyNum(oEvent);
        switch (true) {
          case (iCode >= 48 && iCode <= 90):
          case (iCode >= 106 && iCode <= 111):
          case (iCode >= 160 && iCode <= 164 || iCode == 170):
          case (iCode >= 186 && iCode <= 194):
          case (iCode >= 219 && iCode <= 222):
          case iCode == 32:
            if (oEvent.key !== void 0 && oEvent.key !== "") {
              return oEvent.key;
            }
            var sDecoded = String.fromCharCode(iCode);
            switch (oEvent.shiftKey) {
              case false:
                sDecoded = sDecoded.toLowerCase();
                break;
              case true:
                sDecoded = sDecoded.toUpperCase();
                break;
            }
            return sDecoded;
          case (iCode >= 96 && iCode <= 105):
            return 0 + (iCode - 96);
        }
        return "";
      };
      import_onscan.default.attachTo(document, {
        onScan: (sScancode) => {
          if (this.search_field && this.$component.is(":visible")) {
            this.search_field.set_focus();
            this.set_search_value(sScancode);
            this.barcode_scanned = true;
          }
        }
      });
      this.$component.on("click", ".item-wrapper", function() {
        const $item = $(this);
        const item_code = unescape($item.attr("data-item-code"));
        let batch_no = unescape($item.attr("data-batch-no"));
        let serial_no = unescape($item.attr("data-serial-no"));
        let uom = unescape($item.attr("data-uom"));
        let mrp = unescape($item.attr("data-mrp"));
        let rate = unescape($item.attr("data-rate"));
        let title = unescape($item.attr("title"));
        let start_date = unescape($item.attr("data-start-date"));
        let end_date = unescape($item.attr("data-end-date"));
        let discount_amount = unescape($item.attr("data-discount-amount"));
        let tag = $item.attr("data-tag");
        batch_no = batch_no === "undefined" ? void 0 : batch_no;
        serial_no = serial_no === "undefined" ? void 0 : serial_no;
        uom = uom === "undefined" ? void 0 : uom;
        rate = rate === "undefined" ? void 0 : rate;
        mrp = mrp === "undefined" ? void 0 : mrp;
        title = title === "undefined" ? void 0 : title;
        start_date = start_date === "undefined" ? void 0 : new Date(start_date);
        end_date = end_date === "undefined" ? void 0 : new Date(end_date);
        discount_amount = discount_amount === "undefined" ? void 0 : discount_amount;
        tag = tag === "undefined" ? void 0 : tag;
        me.events.item_selected({
          field: "qty",
          value: "+1",
          item: { item_code, batch_no, serial_no, uom, rate, mrp, title, start_date, end_date, discount_amount, tag, update_rules: false },
          item_quantity: 1
        });
        me.set_search_value("");
      });
      this.search_field.$input.on("input", (e) => {
        clearTimeout(this.last_search);
        this.last_search = setTimeout(() => {
          const search_term = e.target.value;
          this.filter_items({ search_term });
        }, 300);
      });
    }
    attach_shortcuts() {
      const ctrl_label = frappe.utils.is_mac() ? "\u2318" : "Ctrl";
      this.search_field.parent.attr("title", `${ctrl_label}+I`);
      frappe.ui.keys.add_shortcut({
        shortcut: "ctrl+i",
        action: () => this.search_field.set_focus(),
        condition: () => this.$component.is(":visible"),
        description: __("Focus on search input"),
        ignore_inputs: true,
        page: cur_page.page.page
      });
      this.item_group_field.parent.attr("title", `${ctrl_label}+G`);
      frappe.ui.keys.add_shortcut({
        shortcut: "ctrl+g",
        action: () => this.item_group_field.set_focus(),
        condition: () => this.$component.is(":visible"),
        description: __("Focus on Item Group filter"),
        ignore_inputs: true,
        page: cur_page.page.page
      });
      frappe.ui.keys.on("enter", () => {
        const selector_is_visible = this.$component.is(":visible");
        if (!selector_is_visible || this.search_field.get_value() === "")
          return;
        if (this.items.length == 1) {
          this.$items_container.find(".item-wrapper").click();
          frappe.utils.play_sound("submit");
          $(this.search_field.$input[0]).val("").trigger("input");
        } else if (this.items.length == 0 && this.barcode_scanned) {
          frappe.show_alert({
            message: __("No items found. Scan barcode again."),
            indicator: "orange"
          });
          frappe.utils.play_sound("error");
          this.barcode_scanned = false;
          $(this.search_field.$input[0]).val("").trigger("input");
        }
      });
    }
    filter_items({ search_term = "" } = {}) {
      if (search_term) {
        search_term = search_term.toLowerCase();
        this.search_index = this.search_index || {};
        if (this.search_index[search_term]) {
          const items = this.search_index[search_term];
          this.items = items;
          this.render_item_list(items);
          this.auto_add_item && this.items.length == 1 && this.add_filtered_item_to_cart();
          return;
        }
      }
      this.get_items({ search_term }).then(({ message }) => {
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
      if (this.barcode_scanned) {
        this.$items_container.find(".item-wrapper").click();
        this.barcode_scanned = false;
      }
    }
    resize_selector(minimize) {
      minimize ? this.$component.find(".filter-section").css("grid-template-columns", "repeat(1, minmax(0, 1fr))") : this.$component.find(".filter-section").css("grid-template-columns", "repeat(12, minmax(0, 1fr))");
      minimize ? this.$component.find(".search-field").css("margin", "var(--margin-sm) 0px") : this.$component.find(".search-field").css("margin", "0px var(--margin-sm)");
      minimize ? this.$component.css("grid-column", "span 4 / span 4") : this.$component.css("grid-column", "span 2 / span 2");
      minimize ? this.$items_container.css("grid-template-columns", "repeat(2, minmax(0, 1fr))") : this.$items_container.css("grid-template-columns", "repeat(1, minmax(0, 1fr))");
    }
    toggle_component(show) {
      show ? this.$component.css("display", "flex") : this.$component.css("display", "none");
    }
  };
})();
//# sourceMappingURL=pos_item_selector.bundle.H7745QTR.js.map
