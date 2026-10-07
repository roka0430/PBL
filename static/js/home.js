document.addEventListener("alpine:init", () => {
  Alpine.data("plantImage", () => ({
    imageUrl: null,
    imageBlob: null,
    capturedAt: null,

    init() {
      this.$watch("$store.health.revision", () => this.updatePlantImage());
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
    showCount: 10,

    init() {
      const historyList = this.$refs.historyList;
      const listHeight = historyList.clientHeight;
      const itemHeight = parseFloat(getComputedStyle(historyList).getPropertyValue("--history-item-height"));
      const gap = parseFloat(getComputedStyle(historyList).rowGap) || 0;

      this.showCount = Math.max(6, parseInt(listHeight / (gap + itemHeight)) + 1);

      this.$watch("$store.health.revision", () => {
        if (this.histories.length === 0) {
          this.getWateringHistory();
        } else {
          this.getNewWateringHistory();
        }
      });
    },

    async getWateringHistory() {
      const before_id = this.histories.length > 0 ? Math.min(...this.histories.map((history) => history.id)) : null;
      const limit = this.showCount - this.histories.length;

      if (limit <= 0) {
        return;
      }

      const res = await fetch(`/api/watering-history?before_id=${before_id}&limit=${limit}`);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const { histories, total_count } = await res.json();

      this.histories.push(...histories);
      this.total = total_count;
    },

    async getNewWateringHistory() {
      const max_id = this.histories.length > 0 ? Math.max(...this.histories.map((history) => history.id)) : null;

      if (max_id === null) {
        return;
      }

      const res = await fetch(`/api/watering-history?after_id=${max_id}`);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const { histories, total_count } = await res.json();

      this.histories.unshift(...histories);
      this.showCount += histories.length;
      this.total = total_count;
    },

    showMoreHistory() {
      this.showCount += 10;
      this.getWateringHistory();
    },
  }));
});
