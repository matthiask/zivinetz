!((e, n) => {
  "object" === typeof exports && "object" === typeof module
    ? (module.exports = n())
    : "function" === typeof define && define.amd
      ? define([], n)
      : "object" === typeof exports
        ? (exports.locale = n())
        : (e.locale = n())
})(this, () =>
  ((e) => {
    const n = {}
    function t(r) {
      if (n[r]) return n[r].exports
      const o = (n[r] = { i: r, l: !1, exports: {} })
      return e[r].call(o.exports, o, o.exports, t), (o.l = !0), o.exports
    }
    return (
      (t.m = e),
      (t.c = n),
      (t.d = (e, n, r) => {
        t.o(e, n) ||
          Object.defineProperty(e, n, {
            configurable: !1,
            enumerable: !0,
            get: r,
          })
      }),
      (t.r = (e) => {
        Object.defineProperty(e, "__esModule", { value: !0 })
      }),
      (t.n = (e) => {
        const n = e && e.__esModule ? () => e.default : () => e
        return t.d(n, "a", n), n
      }),
      (t.o = (e, n) => Object.prototype.hasOwnProperty.call(e, n)),
      (t.p = ""),
      t((t.s = "cDhT"))
    )
  })({
    cDhT: (e, n, t) => {
      t.r(n), t.d(n, "German", () => o)
      const r =
        "undefined" !== typeof window && void 0 !== window.flatpickr
          ? window.flatpickr
          : { l10ns: {} }
      const o = {
        weekdays: {
          shorthand: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
          longhand: [
            "Sonntag",
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
          ],
        },
        months: {
          shorthand: [
            "Jan",
            "Feb",
            "Mär",
            "Apr",
            "Mai",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Okt",
            "Nov",
            "Dez",
          ],
          longhand: [
            "Januar",
            "Februar",
            "März",
            "April",
            "Mai",
            "Juni",
            "Juli",
            "August",
            "September",
            "Oktober",
            "November",
            "Dezember",
          ],
        },
        firstDayOfWeek: 1,
        weekAbbreviation: "KW",
        rangeSeparator: " bis ",
        scrollTitle: "Zum Ändern scrollen",
        toggleTitle: "Zum Umschalten klicken",
      }
      ;(r.l10ns.de = o), (n.default = r.l10ns)
    },
  }),
)
