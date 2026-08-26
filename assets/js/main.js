/* CCCM - 交互与显现 */
(function () {
  "use strict";

  /* 多语言文案 */
  var IS_EN = document.documentElement.lang === "en";
  var IS_FR = document.documentElement.lang === "fr";
  var IS_DE = document.documentElement.lang === "de";
  var T = {
    openMenu: IS_EN ? "Open menu" : IS_FR ? "Ouvrir le menu" : IS_DE ? "Menü öffnen" : "打开菜单",
    closeMenu: IS_EN ? "Close menu" : IS_FR ? "Fermer le menu" : IS_DE ? "Menü schließen" : "关闭菜单",
    searchLabel: IS_EN ? "Search site" : IS_FR ? "Rechercher sur le site" : IS_DE ? "Website durchsuchen" : "全站搜索",
    placeholder: IS_EN
      ? "Search the site, e.g. Jiao Shunfa, AI Innovation Center, Masters Forum…"
      : IS_FR
      ? "Rechercher sur le site : Jiao Shunfa, Centre d'innovation IA, Forum des grands maîtres…"
      : IS_DE
      ? "Die Website durchsuchen, z. B. Jiao Shunfa, KI-Innovationszentrum, Forum der Großen Meister…"
      : "搜索全站内容，如：焦顺发、AI创新中心、国医名家论坛…",
    indexing: IS_EN ? "Building index…" : IS_FR ? "Création de l'index…" : IS_DE ? "Index wird erstellt…" : "正在建立索引…",
    results: function (n) {
      if (IS_EN) return n + " result" + (n === 1 ? "" : "s");
      if (IS_FR) return n + " résultat" + (n === 1 ? "" : "s");
      if (IS_DE) return n + " Ergebnis" + (n === 1 ? "" : "se");
      return "共 " + n + " 条结果";
    },
    empty: function (q) {
      if (IS_EN) return "No content found for “" + q + "”";
      if (IS_FR) return "Aucun contenu trouvé pour « " + q + " »";
      if (IS_DE) return "Keine Inhalte zu „" + q + "“ gefunden";
      return "未找到与「" + q + "」相关的内容";
    }
  };

  /* 移动端导航：右上角按钮 + 下拉面板 */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav");
  if (toggle && nav) {
    var setNav = function (open) {
      nav.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? T.closeMenu : T.openMenu);
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

  /* 语言切换菜单 */
  var langSwitch = document.querySelector(".lang-switch");
  if (langSwitch) {
    var langBtn = langSwitch.querySelector(".lang-btn");
    langBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = langSwitch.classList.toggle("open");
      langBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (langSwitch.classList.contains("open") && !langSwitch.contains(e.target)) {
        langSwitch.classList.remove("open");
        langBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* 页脚年份 */
  var year = document.querySelector("[data-year]");
  if (year) year.textContent = String(new Date().getFullYear());

  /* 滚动显现（threshold 0：任意可见即触发；高于视口的整块内容直接显示） */
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
      { threshold: 0, rootMargin: "0px 0px -8% 0px" }
    );
    items.forEach(function (el) {
      if (el.offsetHeight > window.innerHeight * 0.9) {
        el.classList.add("in");
      } else {
        io.observe(el);
      }
    });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- 全局搜索 ---------- */
  var PAGES = (IS_EN ? [
    ["Home", "Overview", "Mission", "Signature Events", "Outreach", "Evaluation", "Conclusion", "Chairman"]
  ] : IS_FR ? [
    ["Accueil", "Présentation", "Mission", "Événements phares", "Diffusion continue", "Évaluation", "Conclusion", "Président"]
  ] : IS_DE ? [
    ["Startseite", "Überblick", "Leitbild", "Leitveranstaltungen", "Laufende Arbeit", "Bewertung", "Fazit", "Vorsitzender"]
  ] : [
    ["首页", "组织概述", "成立宗旨", "标志性活动", "长效传播", "行业评价", "总结", "主席简介"]
  ]).map(function (name, i) {
    return { url: ["index.html", "overview.html", "mission.html", "activities.html", "outreach.html", "evaluation.html", "summary.html", "chairman.html"][i], name: name };
  });
  var ICON_SVG =
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>';

  var headerInner = document.querySelector(".header-inner");
  if (!headerInner) return;

  /* 搜索按钮：桌面端在导航右侧，移动端与菜单按钮并排于右上角 */
  var searchBtn = document.createElement("button");
  searchBtn.type = "button";
  searchBtn.className = "search-btn";
  searchBtn.setAttribute("aria-label", T.searchLabel);
  searchBtn.innerHTML = ICON_SVG;
  headerInner.appendChild(searchBtn);

  /* 搜索浮层 */
  var overlay = document.createElement("div");
  overlay.className = "search-overlay";
  overlay.innerHTML =
    '<div class="search-panel" role="dialog" aria-label="全站搜索">' +
    '<div class="search-head">' +
    '<input class="search-input" type="search" placeholder="' + T.placeholder + '" aria-label="' + T.searchLabel + '">' +
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
      status.textContent = T.results(hits.length);
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
      results.innerHTML = '<div class="search-empty">' + T.empty(esc(q)) + "</div>";
    }
  }

  function openSearch() {
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
    input.value = "";
    results.innerHTML = "";
    status.hidden = true;
    if (!entries) {
      status.textContent = T.indexing;
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
