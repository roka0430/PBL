const THEME_STORAGE_KEY = "PBL:theme";

export default {
  isDark: localStorage.getItem(THEME_STORAGE_KEY) === "dark",

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
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  },
};
