export default {
  isDark: localStorage.getItem("PBL:theme") === "dark",

  init() {
    this.applyTheme();
  },

  toggleTheme() {
    this.isDark = !this.isDark;
    this.applyTheme();
  },

  applyTheme() {
    const theme = this.isDark ? "dark" : "light";

    document.documentElement.dataset.theme = theme;
    localStorage.setItem("PBL:theme", theme);
  },
};
