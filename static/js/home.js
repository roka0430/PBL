document.addEventListener("alpine:init", () => {
  Alpine.data("home", () => ({
    sidebarOpen: false,

    init() {
      const media = window.matchMedia("(min-width: 1025px)");

      const handler = (e) => {
        if (e.matches) this.sidebarOpen = false;
      };

      media.addEventListener("change", handler);
    },
  }));

  Alpine.data("plantImage", () => ({
    imageUrl: null,
    imageBlob: null,
    capturedAt: null,

    init() {
      this.scheduleImageUpdate();
    },

    scheduleImageUpdate() {
      this.updatePlantImage();

      setTimeout(() => {
        this.scheduleImageUpdate();
      }, 10000);
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

        const capturedAtString = this.capturedAt.toLocaleString("ja-JP", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });

        this.$refs.capturedAt.textContent = capturedAtString.replace(/\//g, "-");
      }
    },

    saveImage() {
      if (!this.imageBlob) {
        return;
      }

      const capturedAtString = this.capturedAt
        .toLocaleString("ja-JP", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
        .replace(/\D/g, "");

      const url = URL.createObjectURL(this.imageBlob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `MizuMori_${capturedAtString}.jpg`;
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
      this.scheduleSensorUpdate();
    },

    scheduleSensorUpdate() {
      this.updateSensorValues();

      setTimeout(() => {
        this.scheduleSensorUpdate();
      }, 10000);
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

      const measuredAts = Object.values(sensorValues).map((value) => value.measured_at);
      this.measuredAt = new Date(Math.min(...measuredAts.map((date) => new Date(date).getTime())));

      this.soilMoisture = sensorValues.soil_moisture.value.toFixed(1);
      this.temperature = sensorValues.temperature.value.toFixed(1);
      this.humidity = sensorValues.humidity.value.toFixed(1);
    },
  }));
});
