const THEME_STORAGE_KEY = "PBL:theme";

export default {
  theme: localStorage.getItem(THEME_STORAGE_KEY) ?? "system",

  init() {
    this.applyTheme();
  },

  setSystemTheme() {
    this.setTheme("system");
  },

  setLightTheme() {
    this.setTheme("light");
  },

  setDarkTheme() {
    this.setTheme("dark");
  },

  setTheme(theme) {
    this.theme = theme;
    this.applyTheme();
  },

  applyTheme() {
    document.documentElement.dataset.theme = this.theme;
    localStorage.setItem(THEME_STORAGE_KEY, this.theme);
  },
};
