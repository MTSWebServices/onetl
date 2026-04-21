(function () {
  var shadowRoots = new WeakMap();
  var _attachShadow = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function (init) {
    var shadow = _attachShadow.call(this, init);
    shadowRoots.set(this, shadow);
    return shadow;
  };

  var ZOOM_STEPS = [100, 150, 200, 300];

  document.addEventListener("click", function (e) {
    if (e.target.closest(".mermaid-zoom-overlay") || e.target.closest(".mermaid-zoom-toolbar")) return;

    var path = e.composedPath();
    var container = null;
    for (var i = 0; i < path.length; i++) {
      var el = path[i];
      if (el.classList && el.classList.contains("mermaid")) {
        container = el;
        break;
      }
    }
    if (!container) return;

    var root = container.shadowRoot || shadowRoots.get(container);
    if (!root) return;
    var svg = root.querySelector("svg");
    if (!svg) return;

    var currentStep = 1; // start at 150%

    var overlay = document.createElement("div");
    overlay.className = "mermaid-zoom-overlay";

    var toolbar = document.createElement("div");
    toolbar.className = "mermaid-zoom-toolbar";

    var btnMinus = document.createElement("button");
    btnMinus.textContent = "−";
    var btnPlus = document.createElement("button");
    btnPlus.textContent = "+";
    var btnClose = document.createElement("button");
    btnClose.textContent = "✕";
    btnClose.className = "mermaid-zoom-close";

    toolbar.appendChild(btnMinus);
    toolbar.appendChild(btnPlus);
    toolbar.appendChild(btnClose);

    var clone = svg.cloneNode(true);
    clone.removeAttribute("width");
    clone.removeAttribute("height");
    clone.style.width = ZOOM_STEPS[currentStep] + "%";

    overlay.appendChild(clone);
    document.body.appendChild(toolbar);
    document.body.appendChild(overlay);

    function updateZoom() {
      clone.style.width = ZOOM_STEPS[currentStep] + "%";
      btnMinus.disabled = currentStep === 0;
      btnPlus.disabled = currentStep === ZOOM_STEPS.length - 1;
    }

    btnMinus.addEventListener("click", function (e) {
      e.stopPropagation();
      if (currentStep > 0) { currentStep--; updateZoom(); }
    });
    btnPlus.addEventListener("click", function (e) {
      e.stopPropagation();
      if (currentStep < ZOOM_STEPS.length - 1) { currentStep++; updateZoom(); }
    });
    btnClose.addEventListener("click", function (e) {
      e.stopPropagation();
      close();
    });

    overlay.addEventListener("click", close);

    function close() {
      overlay.remove();
      toolbar.remove();
      document.removeEventListener("keydown", onKey);
    }
    function onKey(e) { if (e.key === "Escape") close(); }
    document.addEventListener("keydown", onKey);

    updateZoom();
  });
})();
