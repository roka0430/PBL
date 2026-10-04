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
    imageCapturedAt: null,

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
        this.imageCapturedAt = new Date(capturedAtIso);

        const capturedAtString = this.imageCapturedAt.toLocaleString("ja-JP", {
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

      const capturedAtString = this.imageCapturedAt
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
});
