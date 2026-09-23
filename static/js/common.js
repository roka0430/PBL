import theme from "./modules/theme.js";

document.addEventListener("alpine:init", () => {
  Alpine.data("common_theme", () => theme);
});
