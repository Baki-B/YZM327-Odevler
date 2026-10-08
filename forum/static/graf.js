// Üye ağı: kütüphanesiz kuvvet yönelimli yerleşim (itme + yay + merkez çekimi), SVG ile çizim.
(function () {
  "use strict";
  var svg = document.getElementById("graf");
  if (!svg) return;
  var NS = "http://www.w3.org/2000/svg";
  var G = 800, Y = 560;

  fetch(svg.dataset.kaynak, { credentials: "same-origin" }).then(function (y) { return y.json(); }).then(ciz);

  function ciz(veri) {
    var dugumler = veri.dugumler, kenarlar = veri.kenarlar;
    var harita = {};
    dugumler.forEach(function (d, i) {
      var aci = (2 * Math.PI * i) / dugumler.length;
      d.x = G / 2 + 200 * Math.cos(aci); d.y = Y / 2 + 170 * Math.sin(aci);
      d.r = 7 + d.etki / 9;
      harita[d.id] = d;
    });
    kenarlar = kenarlar.filter(function (k) { return harita[k.kaynak] && harita[k.hedef]; });
    // Aynı görüş grubundakiler birbirine çekilir. Aralarına çizgi çizilmez; ikili oy benzerliği sunucudan gelmez.
    var grupCiftleri = [];
    dugumler.forEach(function (a, i) {
      dugumler.slice(i + 1).forEach(function (b) { if (a.grup && a.grup === b.grup) grupCiftleri.push([a, b]); });
    });

    // Simülasyon
    for (var adim = 0; adim < 350; adim++) {
      var sicaklik = 1 - adim / 350;
      dugumler.forEach(function (d) { d.dx = (G / 2 - d.x) * 0.004; d.dy = (Y / 2 - d.y) * 0.004; });
      for (var i = 0; i < dugumler.length; i++) {
        for (var j = i + 1; j < dugumler.length; j++) {
          var a = dugumler[i], b = dugumler[j];
          var ox = a.x - b.x, oy = a.y - b.y, m2 = ox * ox + oy * oy + 0.01, kuvvet = 22000 / m2;
          var m = Math.sqrt(m2);
          a.dx += kuvvet * ox / m; a.dy += kuvvet * oy / m; b.dx -= kuvvet * ox / m; b.dy -= kuvvet * oy / m;
        }
      }
      function yay(a, b, hedef, carpan) {
        var ox = b.x - a.x, oy = b.y - a.y, m = Math.sqrt(ox * ox + oy * oy) + 0.01, kuvvet = (m - hedef) * 0.02 * carpan;
        a.dx += kuvvet * ox / m; a.dy += kuvvet * oy / m; b.dx -= kuvvet * ox / m; b.dy -= kuvvet * oy / m;
      }
      kenarlar.forEach(function (k) { yay(harita[k.kaynak], harita[k.hedef], 190, 1); });
      grupCiftleri.forEach(function (c) { yay(c[0], c[1], 120, 1.5); });
      dugumler.forEach(function (d) {
        var hiz = Math.sqrt(d.dx * d.dx + d.dy * d.dy), sinir = 12 * sicaklik + 0.5;
        if (hiz > sinir) { d.dx *= sinir / hiz; d.dy *= sinir / hiz; }
        d.x = Math.max(30, Math.min(G - 30, d.x + d.dx)); d.y = Math.max(30, Math.min(Y - 30, d.y + d.dy));
      });
    }

    // Yerleşimi çizim alanına sığdır (kenar boşluğu 60)
    var xs = dugumler.map(function (d) { return d.x; }), ys = dugumler.map(function (d) { return d.y; });
    var minX = Math.min.apply(null, xs), maxX = Math.max.apply(null, xs);
    var minY = Math.min.apply(null, ys), maxY = Math.max.apply(null, ys);
    dugumler.forEach(function (d) {
      d.x = maxX > minX ? 60 + (d.x - minX) * (G - 120) / (maxX - minX) : G / 2;
      d.y = maxY > minY ? 60 + (d.y - minY) * (Y - 120) / (maxY - minY) : Y / 2;
    });

    // Çizim
    var kenarKatmani = document.createElementNS(NS, "g"), dugumKatmani = document.createElementNS(NS, "g");
    svg.appendChild(kenarKatmani); svg.appendChild(dugumKatmani);
    kenarlar.forEach(function (k) {
      var cizgi = document.createElementNS(NS, "line");
      cizgi.setAttribute("class", "kenar kenar-" + k.tur.toLowerCase());
      cizgi.setAttribute("stroke-width", Math.min(1 + k.agirlik, 5));
      cizgi.dataset.tur = k.tur;
      k.el = cizgi;
      kenarKatmani.appendChild(cizgi);
    });
    dugumler.forEach(function (d) {
      var grup = document.createElementNS(NS, "g"), sekil;
      if (d.yz) {
        sekil = document.createElementNS(NS, "rect");
        sekil.setAttribute("width", d.r * 2); sekil.setAttribute("height", d.r * 2);
        sekil.setAttribute("x", -d.r); sekil.setAttribute("y", -d.r); sekil.setAttribute("rx", 3);
      } else if (d.uzman) {
        sekil = document.createElementNS(NS, "polygon");
        sekil.setAttribute("points", [0, -d.r * 1.25, d.r * 1.25, 0, 0, d.r * 1.25, -d.r * 1.25, 0].join(","));
      } else {
        sekil = document.createElementNS(NS, "circle");
        sekil.setAttribute("r", d.r);
      }
      sekil.setAttribute("class", "dugum-sekli" + (d.yz ? " yz" : ""));
      sekil.setAttribute("fill", d.renk);  // Yapay zeka düğümlerinin rengi CSS'ten gelir (.yz)
      var baslik = document.createElementNS(NS, "title");
      baslik.textContent = "@" + d.ad + " · etki " + d.etki + (d.grup ? " · " + d.grup : "") + (d.uzman ? " · uzman" : "") + (d.yz ? " · yapay zeka" : "");
      sekil.appendChild(baslik);
      var yazi = document.createElementNS(NS, "text");
      yazi.setAttribute("y", -d.r - 6); yazi.setAttribute("text-anchor", "middle");
      yazi.textContent = "@" + d.ad;
      grup.appendChild(sekil); grup.appendChild(yazi);
      d.el = grup;
      dugumKatmani.appendChild(grup);
      surukle(d);
    });
    guncelle();

    function guncelle() {
      kenarlar.forEach(function (k) {
        var a = harita[k.kaynak], b = harita[k.hedef];
        k.el.setAttribute("x1", a.x); k.el.setAttribute("y1", a.y); k.el.setAttribute("x2", b.x); k.el.setAttribute("y2", b.y);
      });
      dugumler.forEach(function (d) { d.el.setAttribute("transform", "translate(" + d.x + "," + d.y + ")"); });
    }

    function nokta(e) {
      var p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
      return p.matrixTransform(svg.getScreenCTM().inverse());
    }

    function surukle(d) {
      var basladi = null, tasindi = false;
      d.el.addEventListener("pointerdown", function (e) { basladi = nokta(e); tasindi = false; d.el.setPointerCapture(e.pointerId); });
      d.el.addEventListener("pointermove", function (e) {
        if (!basladi) return;
        var p = nokta(e);
        if (Math.abs(p.x - basladi.x) + Math.abs(p.y - basladi.y) > 3) tasindi = true;
        d.x = p.x; d.y = p.y; guncelle();
      });
      d.el.addEventListener("pointerup", function () {
        if (basladi && !tasindi) window.location.href = (document.body.getAttribute("data-kok") || "") + "/kullanici/" + encodeURIComponent(d.ad);
        basladi = null;
      });
    }

    document.querySelectorAll("[data-kenar-turu]").forEach(function (kutu) {
      kutu.addEventListener("change", function () {
        kenarlar.forEach(function (k) { if (k.tur === kutu.value) k.el.style.display = kutu.checked ? "" : "none"; });
      });
    });
  }
})();
