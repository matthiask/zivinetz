/* batch form */
;(function ($) {
  $(document.body).on("click", "[data-batch-action]", function () {
    var input = $('input[name="batch-action"]')
    input.val($(this).data("batch-action"))
    input.parents("form").submit()
  })

  $(document.body).on("click", "input.batch:checkbox", function () {
    var cb = $(this)
    if (cb.prop("value") == "on") {
      cb.closest("table")
        .find("tbody input.batch:checkbox")
        .prop("checked", cb.prop("checked"))
    } else {
      cb.closest("table")
        .find("thead input.batch:checkbox")
        .prop("checked", false)
    }
  })

  $(".objects thead input[type=checkbox]").bind("change", function () {
    var cbs = $(".objects tbody input[type=checkbox]")
    if ($(this).prop("checked")) {
      cbs.prop("checked", "checked")
    } else {
      cbs.removeAttr("checked")
    }
  })
})(jQuery)

/* search form */
;(function ($) {
  var form = $(".form-search"),
    panel = form.find(".panel")

  if (!panel.length) return

  $(".form-search").on("click", '[data-toggle="form"]', function () {
    panel.toggle()
  })
  // give the layout engine some time to position everything
  // before hiding the panel.
  setTimeout(function () {
    panel.hide()
    panel.css({ opacity: 1 })
  }, 10)
})(jQuery)

/* editLive */
;(function ($) {
  $(document.body).on("editLive", function (event, elem) {
    if (elem.is(":checkbox"))
      /* TODO NOT text input. selects! */
      elem = elem.parent()

    elem.addClass("editlive-updated")
    setTimeout(function () {
      elem.removeClass("editlive-updated")
    }, 2000)
  })
})(jQuery)

/* various tweaks */
;(function ($) {
  Foundation.libs.reveal.settings.animation = "fade"

  $(document).foundation()
  $(document).towelFoundation()

  $(document.body).append('<div id="spinner"></div>')
  var spinner = $("#spinner")
  spinner
    .bind("ajaxSend", function (evt, jqxhr, settings) {
      if (settings.type == "POST") {
        spinner.html("Saving...").show()
      } else {
        spinner.html("Loading...").show()
      }
    })
    .bind("ajaxComplete", function () {
      spinner.hide()
    })
})(jQuery)
