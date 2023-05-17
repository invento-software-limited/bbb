// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt


frappe.provide("erpnext.timesheet");

erpnext.timesheet.timer = function (frm, row, timestamp = 0) {
  let dialog = new frappe.ui.Dialog({
    title: __(""),
    fields:
      [
        {"fieldtype": "HTML", "fieldname": "timer_html"}
      ],
  });
  dialog.dirty = true
  dialog.display = true
  dialog.get_field("timer_html").$wrapper.append(get_timer_html());

  function get_timer_html() {
    return `
			<div class="stopwatch" style="text-align: center">
				<span class="hours" style="display: inline-block;position: relative;font-size: 4em;font-family: menlo;">00</span>
				<span class="colon" style="display: inline-block;position: relative;font-size: 4em;font-family: menlo;">:</span>
				<span class="minutes" style="display: inline-block;position: relative;font-size: 4em;font-family: menlo;">00</span>
				<span class="colon" style="display: inline-block;position: relative;font-size: 4em;font-family: menlo;">:</span>
				<span class="seconds" style="display: inline-block;position: relative;font-size: 4em;font-family: menlo;">00</span>
			</div>
			<div class="playpause text-center">
				<button class= "btn btn-primary btn-start"> ${__("Start")} </button>
				<button class= "btn btn-primary btn-pause"> ${__("Pause")} </button>
				<button class= "btn btn-primary btn-resume"> ${__("Resume")} </button>
				<button class= "btn btn-success btn-complete"> ${__("Complete")} </button>
			</div>
		`;
  }

  erpnext.timesheet.control_timer(frm, dialog, row, timestamp);
  dialog.show();
};

function convertSecondsToTime(seconds) {
  if (seconds < 60) {
    return `${seconds}sec`;
  }
  seconds = Number(seconds);
  var h = Math.floor(seconds / 3600);
  var m = Math.floor(seconds % 3600 / 60);
  var s = Math.floor(seconds % 3600 % 60);

  var hDisplay = h > 0 ? (h + "h ") : "";
  var mDisplay = m > 0 ? (m + "min ") : "";
  var sDisplay = s > 0 ? (s + "sec") : "";
  return hDisplay + mDisplay + sDisplay

  // if (seconds < 60) {
  //   return `${seconds}sec`;
  // }
  // var hours = Math.floor(seconds / 3600); // Extract hours from minutes
  // var remaining = seconds % 3600; // Calculate remaining seconds
  // var minutes = Math.floor(remaining / 60); // Extract minutes from seconds
  // var remainingSeconds = minutes % 60; // Calculate remaining seconds
  // if (hours > 0) {
  //   return `${hours}h ${minutes}min ${remainingSeconds}sec`;
  // } else {
  //   return `${minutes}min ${remainingSeconds}sec`;
  // }
}

erpnext.timesheet.control_timer = function (frm, dialog, row, timestamp = 0) {

  var $btn_start = dialog.$wrapper.find(".playpause .btn-start");
  var $btn_pause = dialog.$wrapper.find(".playpause .btn-pause");
  var $btn_resume = dialog.$wrapper.find(".playpause .btn-resume");
  var $btn_complete = dialog.$wrapper.find(".playpause .btn-complete");
  var interval = null;
  var currentIncrement = timestamp;
  var clicked = false;
  var flag = true; // Alert only once}

  if (frm.doc.status === "Paused") {
    setTimeout(() => {
      updateStopwatch(frm.doc.service_time);
    }, 1000)
    $btn_complete.show();
    $btn_start.hide();
    $btn_pause.hide()
    $btn_resume.show();
    currentIncrement = frm.doc.service_time

  } else if (frm.doc.status === "In Progress") {
    let service_time = moment(frappe.datetime.now_datetime()).diff(moment(frm.doc.service_start_time), "seconds");
    currentIncrement = service_time - frm.doc.pause_time
    $btn_complete.show();
    $btn_start.hide();
    $btn_pause.show()
    $btn_resume.hide();
    initialiseTimer();
  } else {
    $btn_pause.hide()
    $btn_resume.hide()
  }

  $btn_start.click(function (e) {
    $btn_start.hide();
    $btn_resume.hide();
    $btn_complete.show();
    $btn_pause.show()
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'status', 'In Progress')
    if (!frm.doc.service_start_time) {
      frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'service_start_time', frappe.datetime.now_datetime())
      let service_timer = {"service_from": frappe.datetime.now_datetime()}
      frm.add_child('service_timer_log', service_timer);
      frm.save();
    }
    initialiseTimer();
  });

  $btn_pause.click(function () {
    clearInterval(interval);
    $btn_start.hide();
    $btn_resume.show();
    $btn_complete.show();
    $btn_pause.hide()

    let service_time = moment(frappe.datetime.now_datetime()).diff(moment(frm.doc.service_start_time), "seconds");
    let total_service_time = service_time - frm.doc.pause_time
    // let total_service_time_format = convertSecondsToTime(service_timer_service_time)
    // frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'total_service_time', total_service_time_format)
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'service_time', total_service_time)
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'pause_start_time', frappe.datetime.now_datetime())
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'status', 'Paused')

    let last_child = frm.doc.service_timer_log[frm.doc.service_timer_log.length - 1]

    let service_timer_service_time = moment(frappe.datetime.now_datetime()).diff(moment(last_child.service_from), "seconds");
    let service_time_format = convertSecondsToTime(service_timer_service_time)
    frappe.model.set_value(last_child.doctype, last_child.name, 'total_service_time', service_time_format)
    frappe.model.set_value(last_child.doctype, last_child.name, 'service_to', frappe.datetime.now_datetime())
    frappe.model.set_value(last_child.doctype, last_child.name, 'pause_from', frappe.datetime.now_datetime())
    frm.save();
    clearInterval(interval);

  });


  $btn_resume.click(function () {
    clearInterval(interval);
    $btn_start.hide();
    $btn_resume.hide();
    $btn_complete.show();
    $btn_pause.show()

    let pause_time = moment(frappe.datetime.now_datetime()).diff(moment(frm.doc.pause_start_time), "seconds");
    let total_pause_time = pause_time + frm.doc.pause_time
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'pause_time', total_pause_time)
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'status', 'In Progress')

    let last_child = frm.doc.service_timer_log[frm.doc.service_timer_log.length - 1]
    let service_timer_pause_time = moment(frappe.datetime.now_datetime()).diff(moment(last_child.pause_from), "seconds");
    let pause_time_format = convertSecondsToTime(service_timer_pause_time)
    frappe.model.set_value(last_child.doctype, last_child.name, 'total_pause_time', pause_time_format)
    frappe.model.set_value(last_child.doctype, last_child.name, 'pause_to', frappe.datetime.now_datetime())
    frm.add_child('service_timer_log', {"service_from": frappe.datetime.now_datetime()});
    frm.save()

    setTimeout(() => {
      initialiseTimer()
    }, 100)

  });

  $btn_complete.click(function () {
    var args = dialog.get_values();
    if (frm.doc.status === "Paused") {
      let pause_time = moment(frappe.datetime.now_datetime()).diff(moment(frm.doc.pause_start_time), "seconds");
      let total_pause_time = pause_time + frm.doc.pause_time
      let service_time = moment(frappe.datetime.now_datetime()).diff(moment(frm.doc.service_start_time), "seconds");
      let total_service_time = service_time - total_pause_time
      let total_service_time_format = convertSecondsToTime(total_service_time)
      frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'total_service_time', total_service_time_format)
      frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'pause_time', total_pause_time)
      frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'service_time', total_service_time)

      let last_child = frm.doc.service_timer_log[frm.doc.service_timer_log.length - 1]
      let service_timer_pause_time = moment(frappe.datetime.now_datetime()).diff(moment(last_child.pause_from), "seconds");
      let pause_time_format = convertSecondsToTime(service_timer_pause_time)
      frappe.model.set_value(last_child.doctype, last_child.name, 'pause_to', frappe.datetime.now_datetime())
      frappe.model.set_value(last_child.doctype, last_child.name, 'total_pause_time', pause_time_format)

    } else {
      let service_time = moment(frappe.datetime.now_datetime()).diff(moment(frm.doc.service_start_time), "seconds");
      let total_service_time = service_time - frm.doc.pause_time
      let total_service_time_format = convertSecondsToTime(total_service_time)
      frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'total_service_time', total_service_time_format)
      frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'service_time', total_service_time)

      let last_child = frm.doc.service_timer_log[frm.doc.service_timer_log.length - 1]
      let service_timer_service_time = moment(frappe.datetime.now_datetime()).diff(moment(last_child.service_from), "seconds");
      let service_time_format = convertSecondsToTime(service_timer_service_time)
      frappe.model.set_value(last_child.doctype, last_child.name, 'service_to', frappe.datetime.now_datetime())
      frappe.model.set_value(last_child.doctype, last_child.name, 'total_pause_time', service_time_format)
    }
    reset();
    frm.savesubmit()
      .then((r) => {
        frappe.show_alert({
          indicator: 'green',
          message: __('Service record {0} submitted successfully', [r.doc.name])
        });
      })
    dialog.hide();
  });

  function initialiseTimer() {
    interval = setInterval(function () {
      var current = setCurrentIncrement();
      updateStopwatch(current);
    }, 1000);
  }

  function updateStopwatch(increment) {
    var hours = Math.floor(increment / 3600);
    var minutes = Math.floor((increment - (hours * 3600)) / 60);
    var seconds = increment - (hours * 3600) - (minutes * 60);

    // If modal is closed by clicking anywhere outside, reset the timer
    if ((!$('.modal-dialog').is(':visible') && frm.doc.status === "In Progress") || (!$('.modal-dialog').is(':visible') && frm.doc.status === "Paused")) {
      //
    } else if ((!$('.modal-dialog').is(':visible') && frm.doc.status === "Submitted") || (!$('.modal-dialog').is(':visible') && frm.doc.status === "Cancelled") || (!$('.modal-dialog').is(':visible') && frm.doc.status === "Pending For Service")) {
      reset();
    }
    if (hours > 99999) {
      reset();
    }
    $(".hours").text(hours < 10 ? ("0" + hours.toString()) : hours.toString());
    $(".minutes").text(minutes < 10 ? ("0" + minutes.toString()) : minutes.toString());
    $(".seconds").text(seconds < 10 ? ("0" + seconds.toString()) : seconds.toString());
  }

  function setCurrentIncrement() {
    currentIncrement += 1
    return currentIncrement;
  }

  function reset() {
    currentIncrement = 0;
    clearInterval(interval);
    $(".hours").text("00");
    $(".minutes").text("00");
    $(".seconds").text("00");
    $btn_complete.hide();
    $btn_start.show();
  }
};


frappe.ui.form.on('Service Record', {
  setup: function (frm) {
    // frappe.require("/assets/erpnext/js/projects/timer.js");
  },
  // validate: (frm)=>{
  //   if(!frm.doc.service_person_1){
  //     frappe.throw(__(''))
  //   }
  // },
  refresh: (frm) => {
    if (frm.doc.docstatus < 1) {
      let button = 'Start Timer';
      if (frm.doc.service_start_time) {
        button = 'Show Timer'
      }
      frm.add_custom_button(__(button), function () {
        if (!frm.doc.service_person_1) {
          frappe.throw(__('Service Person 1 is required'))
        } else {
          erpnext.timesheet.timer(frm);

        }
      }).addClass("btn-primary btn-timer-dialog");

      if (frm.doc.service_start_time) {
        if ((!$('.modal-dialog').is(':visible') && frm.doc.status === "In Progress") || (!$('.modal-dialog').is(':visible') && frm.doc.status === "Paused")) {
          erpnext.timesheet.timer(frm);
        }
      }
    }
  },
  before_submit: (frm) => {
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'status', 'Submitted')
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'service_end_time', frappe.datetime.now_datetime())
  },
  after_cancel: () => {
    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'status', 'Pending For Service')
  },
});


