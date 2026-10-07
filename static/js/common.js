const DATA_REFRESH_INTERVAL_SEC = 10;
const THEME_STORAGE_KEY = "PBL:theme";

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

  Alpine.store("health", {
    revision: 0,
    connected: false,

    init() {
      this.start();
    },

    start() {
      const refresh = async () => {
        await this.check();

        if (this.connected) {
          this.revision++;
        }

        setTimeout(refresh, DATA_REFRESH_INTERVAL_SEC * 1000);
      };

      refresh();
    },

    async check() {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);

      try {
        const res = await fetch("/api/health", {
          cache: "no-store",
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error();
        }

        this.connected = true;
      } catch {
        this.connected = false;
      } finally {
        clearTimeout(timeout);
      }
    },
  });

  Alpine.data("body", () => ({
    formatDateObject(date, format) {
      const values = {
        YYYY: String(date.getFullYear()).padStart(4, "0"),
        YY: String(date.getFullYear()).slice(-2),
        MM: String(date.getMonth() + 1).padStart(2, "0"),
        DD: String(date.getDate()).padStart(2, "0"),
        HH: String(date.getHours()).padStart(2, "0"),
        mm: String(date.getMinutes()).padStart(2, "0"),
        ss: String(date.getSeconds()).padStart(2, "0"),
      };

      return format.replace(/YYYY|YY|MM|DD|HH|mm|ss/g, (match) => values[match]);
    },

    formatDate(date, format = "YYYY-MM-DD") {
      if (!date) {
        return "";
      }

      if (date instanceof Date) {
        return this.formatDateObject(date, format);
      }

      if (typeof date === "string") {
        return this.formatDateObject(new Date(date), format);
      }

      throw new TypeError("date must be a Date or ISO date string");
    },
  }));

  Alpine.data("navigation", () => ({
    sidebarOpen: false,

    init() {
      this.closeSidebarOnDesktop();
    },

    closeSidebarOnDesktop() {
      const media = window.matchMedia("(min-width: 1025px)");

      const handler = (e) => {
        if (e.matches) this.sidebarOpen = false;
      };

      media.addEventListener("change", handler);
    },
  }));

  Alpine.data("common_theme", () => ({
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
  }));
});
