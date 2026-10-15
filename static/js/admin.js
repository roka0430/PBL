document.addEventListener("alpine:init", () => {
  Alpine.store("settings", {
    settings: {},
    revision: 0,

    async init() {
      this.settings = await this.loadSettings();
      this.revision++;
    },

    async loadSettings() {
      const res = await fetch("/api/settings/definition");

      if (!res.ok) {
        throw new Error("Failed to load settings");
      }

      return await res.json();
    },

    getByGroup(group) {
      const settings = {};

      for (const [id, setting] of Object.entries(this.settings[group])) {
        settings[id] = { id, ...setting };
      }

      return settings;
    },

    getListByGroup(group) {
      return Object.values(this.getByGroup(group));
    },
  });

  Alpine.store("settingsPopup", {
    edit(group, id) {
      console.log(group, id);
    },
  });

  Alpine.data("sensors", () => ({
    soilMoisture: null,
    soilMoistureRaw: null,
    temperature: null,
    humidity: null,
    measuredAt: null,

    init() {
      this.$watch("$store.health.revision", () => this.updateSensorValues());
    },

    async updateSensorValues() {
      const res = await fetch("/api/sensors", {
        cache: "no-store",
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const sensorValues = await res.json();

      if (!sensorValues.ready) {
        console.log("Sensors are not ready yet.");
        return;
      }

      const measuredAts = Object.values(sensorValues)
        .map((value) => value.measured_at)
        .filter(Boolean);
      this.measuredAt = new Date(Math.min(...measuredAts.map((date) => new Date(date).getTime())));

      this.soilMoisture = sensorValues.soil_moisture.value.toFixed(1);
      this.soilMoistureRaw = sensorValues.soil_moisture_raw.value.toFixed(0);
      this.temperature = sensorValues.temperature.value.toFixed(1);
      this.humidity = sensorValues.humidity.value.toFixed(1);
    },
  }));

  Alpine.data("emergencyStop", () => ({
    async emergencyStop() {
      const res = await fetch("/api/watering/emergency-stop", { method: "POST" });

      if (!res.ok) {
        throw new Error("緊急停止に失敗しました");
      }

      alert("緊急停止しました");
    },
  }));

  Alpine.data("autoWatering", () => ({
    MODES: {
      OFF: "off",
      THRESHOLD_CONTROL: "threshold_control",
      FIXED_AMOUNT: "fixed_amount",
      SCHEDULED: "scheduled",
    },

    settings: [],
    mode: null,
    enable: false,
    updating: true,

    async init() {
      await this.initWateringMode();
      this.loadSettings();

      this.$watch(
        () => this.$store.settings.revision,
        () => {
          this.loadSettings();
        },
      );
    },

    get group() {
      return this.mode.slice(0, 3);
    },

    async initWateringMode() {
      const res = await fetch("/api/auto-watering-mode");

      if (!res.ok) {
        throw new Error("Failed to load current watering mode");
      }

      const { mode } = await res.json();

      if (mode === this.MODES.OFF) {
        this.mode = this.MODES.THRESHOLD_CONTROL;
        this.enable = false;
        this.updating = false;
        return;
      }

      if (Object.values(this.MODES).includes(mode)) {
        this.mode = mode;
        this.enable = true;
      }

      this.updating = false;
    },

    loadSettings() {
      this.settings = this.$store.settings.getListByGroup(this.group);
    },

    toggleMode() {
      this.enable = !this.enable;
      this.changeMode();
    },

    async changeMode() {
      this.updating = true;

      const res = await fetch("/api/auto-watering-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: this.getCurrentMode() }),
      });

      if (!res.ok) {
        throw new Error("モードを変更できませんでした");
      }

      this.updating = false;
      this.loadSettings();
    },

    getCurrentMode() {
      if (!this.enable) {
        return this.MODES.OFF;
      }

      return this.mode;
    },
  }));

  Alpine.data("manualWatering", () => ({
    amount: 10,
    watering: true,
    timeout: null,

    init() {
      this.watchSystem();
    },

    async startWatering() {
      // TODO ポップアップで確認
      if (!confirm("給水しますか？")) {
        return;
      }

      const amount = this.amount;
      this.amount = 10;

      const res = await fetch("/api/watering", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          amount: amount,
        }),
      });

      const result = await res.json();

      if (result.success) {
        this.watering = true;
        this.watchSystem();
      } else {
        console.log(result);
        // TODO 失敗ならエラーメッセージをポップアップ表示
      }
    },

    stopWatering() {
      this.watering = false;
      clearTimeout(this.timeout);
      fetch("/api/watering/stop", { method: "POST" });
    },

    async watchSystem() {
      const res = await fetch("/api/status");

      if (res.ok) {
        const status = await res.json();
        if (status.status !== "watering") {
          this.watering = false;
          clearTimeout(this.timeout);
          return;
        }
      }

      this.timeout = setTimeout(() => this.watchSystem(), 1000);
    },
  }));

  Alpine.data("settings", () => ({
    settings: {},
    settingsLayout: [],

    SETTINGS_GROUPS: [
      {
        title: "センサ",
        ids: ["sensing_interval_sec", "startup_waiting_sec", "soil_moisture_dry", "soil_moisture_wet"],
      },
      {
        title: "ポンプ",
        ids: ["pump_flow_rate_ml_sec"],
      },
    ],

    CALIBRATABLE_SETTINGS: ["soil_moisture_dry", "soil_moisture_wet", "pump_flow_rate_ml_sec"],

    init() {
      this.$watch(
        () => this.$store.settings.revision,
        () => {
          const settings = this.$store.settings.getByGroup("sys");
          this.settingsLayout = this.createSettingsLayout(settings);
        },
      );
    },

    createSettingsLayout(settings) {
      const settingsLayout = [];

      for (const { title, ids } of this.SETTINGS_GROUPS) {
        settingsLayout.push({
          type: "heading",
          label: title,
        });

        for (const id of ids) {
          settingsLayout.push({
            type: "setting",
            ...settings[id],
          });
        }
      }

      return settingsLayout;
    },

    isCalibratable(id) {
      return this.CALIBRATABLE_SETTINGS.includes(id);
    },
  }));
});
