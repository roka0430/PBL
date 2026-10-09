document.addEventListener("alpine:init", () => {
  Alpine.data("sensorValues", () => ({
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
    watering: false,
    timeout: null,

    async startWatering() {
      // TODO ポップアップを作成
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
});
