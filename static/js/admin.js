import themeChange from "./modules/theme-change.js";

document.addEventListener("alpine:init", () => {
  Alpine.data("themeChange", () => themeChange);
});
