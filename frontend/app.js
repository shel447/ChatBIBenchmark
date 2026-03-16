const navButtons = document.querySelectorAll("[data-view-target]");
const views = document.querySelectorAll("[data-view]");

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
