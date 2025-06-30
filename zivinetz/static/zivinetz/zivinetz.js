/* batch form */
;(($) => {
  $(document.body).on("click", "[data-batch-action]", function () {
    const input = $('input[name="batch-action"]')
    input.val($(this).data("batch-action"))
    input.parents("form").submit()
  })

  $(document.body).on("click", "input.batch:checkbox", function () {
    const cb = $(this)
    if (cb.prop("value") === "on") {
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
    const cbs = $(".objects tbody input[type=checkbox]")
    if ($(this).prop("checked")) {
      cbs.prop("checked", "checked")
    } else {
      cbs.removeAttr("checked")
    }
  })
})(jQuery)

/* search form */
;(($) => {
  const form = $(".form-search")
  const panel = form.find(".panel")

  if (!panel.length) return

  $(".form-search").on("click", '[data-toggle="form"]', () => {
    panel.toggle()
  })
  // give the layout engine some time to position everything
  // before hiding the panel.
  setTimeout(() => {
    panel.hide()
    panel.css({ opacity: 1 })
  }, 10)
})(jQuery)

/* editLive */
;(($) => {
  $(document.body).on("editLive", (_event, elem) => {
    if (elem.is(":checkbox"))
      /* TODO NOT text input. selects! */
      elem = elem.parent()

    elem.addClass("editlive-updated")
    setTimeout(() => {
      elem.removeClass("editlive-updated")
    }, 2000)
  })
})(jQuery)

/* various tweaks */
;(($) => {
  Foundation.libs.reveal.settings.animation = "fade"

  $(document).foundation()
  $(document).towelFoundation()

  $(document.body).append('<div id="spinner"></div>')
  const spinner = $("#spinner")
  spinner
    .bind("ajaxSend", (_evt, _jqxhr, settings) => {
      if (settings.type === "POST") {
        spinner.html("Saving...").show()
      } else {
        spinner.html("Loading...").show()
      }
    })
    .bind("ajaxComplete", () => {
      spinner.hide()
    })
})(jQuery)
