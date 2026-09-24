import theme from "./modules/theme.js";

document.addEventListener("alpine:init", () => {
  Alpine.store("role", {
    role: "",

    get label() {
      return (
        {
          admin: "管理者",
          viewer: "閲覧者",
        }[this.role] ?? ""
      );
    },

    init() {
      this.role = document.body?.dataset.userRole ?? "";
    },
  });

  Alpine.data("common_theme", () => theme);
});
