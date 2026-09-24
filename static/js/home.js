document.addEventListener("alpine:init", () => {
  Alpine.data("home", () => ({
    sidebarOpen: false,

    init() {
      const media = window.matchMedia("(min-width: 1025px)");

      const handler = (e) => {
        if (e.matches) this.sidebarOpen = false;
      };

      media.addEventListener("change", handler);
    },
  }));
});
