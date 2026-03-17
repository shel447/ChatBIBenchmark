const navButtons = document.querySelectorAll("[data-view-target]");
const views = document.querySelectorAll("[data-view]");
const typeSelect = document.querySelector("[data-case-type]");
const typePanels = document.querySelectorAll("[data-type-panel]");
const accordionGroups = document.querySelectorAll("[data-accordion]");
const accordionToggles = document.querySelectorAll("[data-accordion-toggle]");

function activateView(target) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === target);
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === target);
  });
  accordionGroups.forEach((group) => {
    const match = group.querySelector(`[data-view-target="${target}"]`);
    if (match) {
      group.classList.add("open");
    }
  });
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateView(button.dataset.viewTarget);
  });
});

accordionToggles.forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const group = toggle.closest("[data-accordion]");
    if (group) {
      group.classList.toggle("open");
    }
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
