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
