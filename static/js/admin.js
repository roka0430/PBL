document.addEventListener("alpine:init", () => {
  Alpine.store("settings", {
    settings: {},
    revision: 0,
    loading: false,

    async init() {
      await this.loadSettings();
    },

    async loadSettings() {
      if (this.loading) {
        return;
      }

      this.loading = true;

      try {
        const res = await fetch("/api/settings/definition");

        if (!res.ok) {
          throw new Error("Failed to load settings");
        }

        this.settings = await res.json();
      } finally {
        this.revision++;
        this.loading = false;
      }
    },

    getByGroup(group) {
      const settings = {};

      if (!(group in this.settings)) {
        return null;
      }

      for (const [id, setting] of Object.entries(this.settings[group])) {
        settings[id] = { id, ...setting };
      }

      return settings;
    },

    getListByGroup(group) {
      return Object.values(this.getByGroup(group));
    },

    getById(group, id) {
      const settings = this.getByGroup(group);

      if (settings === null || !(id in settings)) {
        return null;
      }

      return settings[id];
    },

    async update(group, id, value) {
      try {
        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            key: `${group}.${id}`,
            value: value,
          }),
        });

        const result = await res.json();

        if (!res.ok) {
          return {
            success: false,
            message: result.message ?? "設定の更新に失敗しました",
          };
        }

        this._set(group, id, result.value);

        return {
          success: true,
          value: result.value,
        };
      } catch {
        return {
          success: false,
          message: "サーバーに接続できませんでした",
        };
      }
    },

    _set(group, id, value) {
      if (!(group in this.settings)) {
        return;
      }

      if (!(id in this.settings[group])) {
        return;
      }

      this.settings[group][id].value = value;
      this.revision++;
    },
  });

  Alpine.store("watering", {
    syncAfterEmergencyStop: null,
  });

  Alpine.store("popup", {
    opened: false,
    id: "",

    settingGroup: null,
    settingId: null,
    revision: 0,

    open(id, settingGroup, settingId) {
      this.id = id;
      this.settingGroup = settingGroup;
      this.settingId = settingId;
      this.opened = true;
      this.revision++;
    },

    close() {
      this.id = "";
      this.opened = false;
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
    stopping: false,

    async emergencyStop() {
      this.stopping = true;

      try {
        const res = await fetch("/api/watering/emergency-stop", { method: "POST" });

        if (!res.ok) {
          throw new Error("緊急停止に失敗しました");
        }

        await this.$store.watering.syncAfterEmergencyStop?.();

        alert("緊急停止しました");
      } finally {
        this.stopping = false;
      }
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
      await this.syncWateringMode();
      this.loadSettings();

      this.$store.watering.syncAfterEmergencyStop = () => this.onEmergencyStop();

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

    async onEmergencyStop() {
      this.enable = false;
      this.updating = true;

      try {
        await this.syncWateringMode();
        this.loadSettings();
      } finally {
        this.updating = false;
      }
    },

    async syncWateringMode() {
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
        ids: [
          "sensing_interval_sec",
          "startup_waiting_sec",
          "high_temperature_threshold",
          "low_temperature_threshold",
          "soil_moisture_dry",
          "soil_moisture_wet",
          "sensor_saving_interval_sec",
        ],
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

  Alpine.data("settingsPopup", () => ({
    saving: false,

    group: null,
    id: null,

    description: null,
    heading: null,
    unit: null,
    min: null,
    max: null,
    currentValue: null,
    value: null,

    init() {
      this.$watch(
        () => this.$store.popup.revision,
        () => this.updatePopup(),
      );
    },

    updatePopup() {
      this.group = this.$store.popup.settingGroup;
      this.id = this.$store.popup.settingId;

      const setting = this.$store.settings.getById(this.group, this.id);

      this.description = setting.description;
      this.heading = setting.label;
      this.unit = setting.unit;
      this.min = setting.min;
      this.max = setting.max;
      this.currentValue = this.value = setting.value;

      this.$nextTick(() => {
        this.$refs.input.focus();
      });
    },

    async save() {
      this.saving = true;

      const result = await this.$store.settings.update(this.group, this.id, Number(this.value));

      if (!result.success) {
        alert("設定値を変更できませんでした");
      }

      this.$store.popup.close();
      this.saving = false;
    },

    get validation() {
      const value = this.value;

      if (value === "") {
        return {
          isValid: false,
          message: "値を入力してください",
        };
      }

      const number = Number(value);

      if (!Number.isFinite(number)) {
        return {
          isValid: false,
          message: "数値を入力してください",
        };
      }

      if (this.min !== null && number < this.min) {
        return {
          isValid: false,
          message: `${this.min}${this.unit}以上の値を入力してください`,
        };
      }

      if (this.max !== null && number > this.max) {
        return {
          isValid: false,
          message: `${this.max}${this.unit}以下の値を入力してください`,
        };
      }

      return {
        isValid: true,
        message: "",
      };
    },
  }));

  Alpine.data("calibrationPopup", () => ({
    settingId: null,
    heading: null,
    description: null,
    unit: null,
    min: null,
    max: null,
    currentValue: null,
    calibrationResult: null,

    calibrating: false,
    complete: false,

    init() {
      this.$watch(
        () => this.$store.popup.revision,
        () => this.updatePopup(),
      );
    },

    updatePopup() {
      this.group = this.$store.popup.settingGroup;
      this.id = this.$store.popup.settingId;
      const setting = this.$store.settings.getById(this.group, this.id);

      this.settingId = setting.id;
      this.description = setting.description;
      this.heading = setting.label;
      this.unit = setting.unit;
      this.min = setting.min;
      this.max = setting.max;
      this.currentValue = setting.value;
    },

    async drySoilCalibrate() {
      if (!confirm("校正を開始しますか？")) {
        return;
      }

      this.calibrating = true;
      this.calibrationResult = "測定中";

      const res = await fetch("/api/calibration/soil-moisture-dry", {
        method: "POST",
      });

      if (!res.ok) {
        console.log("error");
        this.calibrating = false;
        this.calibrationResult = "測定失敗";
        return;
      }

      const result = await res.json();

      this.calibrating = false;
      this.complete = true;
      this.calibrationResult = result.value;
    },
  }));
});
