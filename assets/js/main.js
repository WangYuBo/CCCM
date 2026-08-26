/* CCCM - 交互与显现 */
(function () {
  "use strict";

  /* 移动端导航：右上角按钮 + 下拉面板 */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav");
  if (toggle && nav) {
    var setNav = function (open) {
      nav.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "关闭菜单" : "打开菜单");
      toggle.textContent = open ? "✕" : "☰";
    };
    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      setNav(!nav.classList.contains("open"));
    });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setNav(false); });
    });
    /* 点击面板外 / 上下滑动 / ESC 均自动收起 */
    document.addEventListener("click", function (e) {
      if (nav.classList.contains("open") && !nav.contains(e.target) && e.target !== toggle) {
        setNav(false);
      }
    });
    window.addEventListener("scroll", function () {
      if (nav.classList.contains("open")) setNav(false);
    }, { passive: true });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setNav(false);
    });
  }

  /* 页脚年份 */
  var year = document.querySelector("[data-year]");
  if (year) year.textContent = String(new Date().getFullYear());

  /* 滚动显现 */
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && items.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- 全局搜索 ---------- */
  var PAGES = [
    { url: "index.html", name: "首页" },
    { url: "about.html", name: "关于我们" },
    { url: "news.html", name: "新闻动态" },
    { url: "events.html", name: "活动" },
    { url: "experts.html", name: "名医智库" },
    { url: "contact.html", name: "联系我们" }
  ];
  var ICON_SVG =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>';

  var headerInner = document.querySelector(".header-inner");
  if (!headerInner) return;

  /* 搜索按钮：桌面端在导航右侧，移动端与菜单按钮并排于右上角 */
  var searchBtn = document.createElement("button");
  searchBtn.type = "button";
  searchBtn.className = "search-btn";
  searchBtn.setAttribute("aria-label", "全站搜索");
  searchBtn.innerHTML = ICON_SVG;
  headerInner.appendChild(searchBtn);

  /* 搜索浮层 */
  var overlay = document.createElement("div");
  overlay.className = "search-overlay";
  overlay.innerHTML =
    '<div class="search-panel" role="dialog" aria-label="全站搜索">' +
    '<div class="search-head">' +
    '<input class="search-input" type="search" placeholder="搜索全站内容，如：焦顺发、AI创新中心、国医名家论坛…" aria-label="搜索关键词">' +
    '<button type="button" class="search-btn" aria-label="关闭搜索">✕</button>' +
    "</div>" +
    '<div class="search-status" hidden></div>' +
    '<div class="search-results"></div>' +
    "</div>";
  document.body.appendChild(overlay);

  var input = overlay.querySelector(".search-input");
  var status = overlay.querySelector(".search-status");
  var results = overlay.querySelector(".search-results");
  var closeBtn = overlay.querySelector(".search-head .search-btn");

  var entries = null;   /* [{page,name,heading,text,href}] */
  var indexing = null;  /* Promise */

  function buildIndex() {
    if (indexing) return indexing;
    indexing = Promise.all(PAGES.map(function (p) {
      return fetch(p.url)
        .then(function (r) { return r.text(); })
        .then(function (html) {
          var doc = new DOMParser().parseFromString(html, "text/html");
          var main = doc.querySelector("main") || doc.body;
          var list = [];
          var heading = doc.title.split("|")[0].trim();
          main.querySelectorAll("h2, h3, h4, p, li, blockquote").forEach(function (el) {
            var text = (el.textContent || "").replace(/\s+/g, " ").trim();
            if (text.length < 2) return;
            if (/^h[234]$/i.test(el.tagName)) heading = text;
            var anchor = el.closest("[id]");
            list.push({
              page: p.url, name: p.name, heading: heading, text: text,
              href: p.url + (anchor ? "#" + anchor.id : "")
            });
          });
          return list;
        })
        .catch(function () { return []; });
    })).then(function (lists) {
      return lists.reduce(function (a, b) { return a.concat(b); }, []);
    });
    return indexing;
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function snippet(text, terms) {
    var lower = text.toLowerCase();
    var pos = -1;
    for (var i = 0; i < terms.length; i++) {
      pos = lower.indexOf(terms[i]);
      if (pos >= 0) break;
    }
    var start = Math.max(0, pos - 40);
    var end = Math.min(text.length, pos + 80);
    var s = (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
    var re = new RegExp("(" + terms.map(function (t) {
      return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }).join("|") + ")", "gi");
    return esc(s).replace(re, "<mark>$1</mark>");
  }

  function search(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    return entries.filter(function (e) {
      return terms.every(function (t) {
        return e.text.toLowerCase().indexOf(t) >= 0 || e.heading.toLowerCase().indexOf(t) >= 0;
      });
    }).sort(function (a, b) {
      var ah = terms.some(function (t) { return a.heading.toLowerCase().indexOf(t) >= 0; });
      var bh = terms.some(function (t) { return b.heading.toLowerCase().indexOf(t) >= 0; });
      return (bh ? 1 : 0) - (ah ? 1 : 0);
    }).slice(0, 24);
  }

  function render(q) {
    var hits = search(q);
    if (hits.length) {
      status.textContent = "共 " + hits.length + " 条结果";
      status.hidden = false;
      results.innerHTML = hits.map(function (h) {
        return '<a class="search-result" href="' + h.href + '">' +
          '<span class="sr-page">' + h.name + "</span>" +
          '<div class="sr-title">' + esc(h.heading) + "</div>" +
          '<div class="sr-text">' + snippet(h.text, q.toLowerCase().split(/\s+/).filter(Boolean)) + "</div>" +
          "</a>";
      }).join("");
    } else {
      status.hidden = true;
      results.innerHTML = '<div class="search-empty">未找到与「' + esc(q) + "」相关的内容</div>";
    }
  }

  function openSearch() {
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
    input.value = "";
    results.innerHTML = "";
    status.hidden = true;
    if (!entries) {
      status.textContent = "正在建立索引…";
      status.hidden = false;
      buildIndex().then(function (list) {
        entries = list;
        if (overlay.classList.contains("open")) {
          if (input.value.trim()) render(input.value.trim());
          else status.hidden = true;
        }
      });
    }
    setTimeout(function () { input.focus(); }, 50);
  }

  function closeSearch() {
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }

  searchBtn.addEventListener("click", openSearch);
  closeBtn.addEventListener("click", closeSearch);
  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) closeSearch();
  });
  results.addEventListener("click", function () { closeSearch(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlay.classList.contains("open")) closeSearch();
  });
  var deb;
  input.addEventListener("input", function () {
    clearTimeout(deb);
    deb = setTimeout(function () {
      var q = input.value.trim();
      if (q && entries) render(q);
      else { results.innerHTML = ""; status.hidden = true; }
    }, 160);
  });
})();
