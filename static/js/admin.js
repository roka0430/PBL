document.addEventListener("alpine:init", () => {
  Alpine.store("settings", {
    SETTINGS_TYPES: {
      settings: [
        "sensor_check_interval_sec",
        "startup_delay_sec",
        "soil_moisture_dry",
        "soil_moisture_wet",
        "watering_amount_ml",
        "pump_flow_ml_per_sec",
      ],
      auto_watering_threshold: [],
      auto_watering_fixed_amount: [],
      auto_watering_scheduled: [],
    },

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

    getByType(type) {
      const settings = {};

      for (const id of this.SETTINGS_TYPES[type]) {
        settings[id] = { id, ...this.settings[id] };
      }

      return settings;
    },

    getListByType(type) {
      return Object.values(this.getByType(type));
    },
  });

  Alpine.store("settingsPopup", {});

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
        ids: ["sensor_check_interval_sec", "startup_delay_sec", "soil_moisture_dry", "soil_moisture_wet"],
      },
      {
        title: "ポンプ",
        ids: ["watering_amount_ml", "pump_flow_ml_per_sec"],
      },
    ],

    CALIBRATABLE_SETTINGS: ["soil_moisture_dry", "soil_moisture_wet", "pump_flow_ml_per_sec"],

    init() {
      this.$watch(
        () => this.$store.settings.revision,
        () => {
          const settings = this.$store.settings.getByType("settings");
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

    editSetting(id) {
      console.log("edit", id);
    },

    calibrateSetting(id) {
      console.log("calibrate", id);
    },
  }));
});
