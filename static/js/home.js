const DATA_REFRESH_INTERVAL_SEC = 10;

document.addEventListener("alpine:init", () => {
  Alpine.store("refresh", {
    revision: 0,

    start() {
      const refresh = () => {
        this.revision++;
        setTimeout(refresh, DATA_REFRESH_INTERVAL_SEC * 1000);
      };

      refresh();
    },
  });

  Alpine.data("home", () => ({
    sidebarOpen: false,

    init() {
      this.closeSidebarOnDesktop();
      this.$store.refresh.start();
    },

    closeSidebarOnDesktop() {
      const media = window.matchMedia("(min-width: 1025px)");

      const handler = (e) => {
        if (e.matches) this.sidebarOpen = false;
      };

      media.addEventListener("change", handler);
    },

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

  Alpine.data("plantImage", () => ({
    imageUrl: null,
    imageBlob: null,
    capturedAt: null,

    init() {
      this.updatePlantImage();
      this.$watch("$store.refresh.revision", () => this.updatePlantImage());
    },

    async updatePlantImage() {
      const res = await fetch("/api/image", {
        cache: "no-store",
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      this.imageBlob = await res.blob();

      if (this.imageUrl) {
        URL.revokeObjectURL(this.imageUrl);
      }

      this.imageUrl = URL.createObjectURL(this.imageBlob);
      this.$refs.img.src = this.imageUrl;

      const capturedAtIso = res.headers.get("MizuMori-Captured-At");

      if (capturedAtIso) {
        this.capturedAt = new Date(capturedAtIso);
      }
    },

    saveImage() {
      if (!this.imageBlob) {
        return;
      }

      const url = URL.createObjectURL(this.imageBlob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `MizuMori_${this.formatDate(this.capturedAt, "YYYYMMDDHHmmss")}.jpg`;
      a.click();
      a.remove();

      URL.revokeObjectURL(url);
    },
  }));

  Alpine.data("sensorValues", () => ({
    soilMoisture: null,
    temperature: null,
    humidity: null,
    measuredAt: null,

    init() {
      this.updateSensorValues();
      this.$watch("$store.refresh.revision", () => this.updateSensorValues());
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
      this.temperature = sensorValues.temperature.value.toFixed(1);
      this.humidity = sensorValues.humidity.value.toFixed(1);
    },
  }));

  Alpine.data("systemStatus", () => ({}));

  Alpine.data("systemHistory", () => ({
    WATERING_TYPE: {
      auto: "自動",
      manual: "手動",
    },

    histories: [],
    total: 0,
    limit: 10,

    async init() {
      this.getWateringHistory(this.limit);
      this.$watch("$store.refresh.revision", () => this.getWateringHistory(this.limit));
    },

    async getWateringHistory(limit) {
      const res = await fetch(`/api/watering-history?limit=${limit}`);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const { history, total_count } = await res.json();

      this.histories = history;
      this.total = total_count;
    },

    showMoreHistory() {
      this.limit += 10;
      this.getWateringHistory(this.limit);
    },
  }));
});
