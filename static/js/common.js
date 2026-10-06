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

    start() {
      const refresh = async () => {
        if (await this.check()) {
          this.revision++;
        }

        setTimeout(refresh, DATA_REFRESH_INTERVAL_SEC * 1000);
      };

      refresh();
    },

    async check() {
      try {
        const res = await fetch("/api/health", {
          cache: "no-store",
        });

        if (!res.ok) {
          throw new Error();
        }

        this.connected = true;
      } catch {
        this.connected = false;
      }

      return this.connected;
    },
  });

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
