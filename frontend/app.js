const navButtons = document.querySelectorAll("[data-view-target]");
const views = document.querySelectorAll("[data-view]");
const typeSelect = document.querySelector("[data-case-type]");
const typePanels = document.querySelectorAll("[data-type-panel]");

function activateView(target) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === target);
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === target);
  });
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateView(button.dataset.viewTarget);
  });
});

activateView("dashboard");

function activateTypePanel(type) {
  typePanels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.typePanel === type);
  });
}

if (typeSelect) {
  activateTypePanel(typeSelect.value);
  typeSelect.addEventListener("change", (event) => {
    activateTypePanel(event.target.value);
  });
}
