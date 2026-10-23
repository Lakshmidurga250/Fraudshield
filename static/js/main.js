/**
 * FraudShield UI Interactivity & Preset Loader
 */
document.addEventListener("DOMContentLoaded", () => {
  // Auto-dismiss alerts after 5 seconds if desired
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    const closeBtn = alert.querySelector(".alert-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => alert.remove());
    }
  });

  // Sample transaction quick-fill buttons on Prediction form
  const btnFillNormal = document.getElementById("btn-fill-normal");
  const btnFillSuspicious = document.getElementById("btn-fill-suspicious");

  if (btnFillNormal) {
    btnFillNormal.addEventListener("click", () => {
      populatePreset({
        amount: "34.50",
        time_val: "14200",
        v1: "0.08", v2: "-0.04", v3: "0.12", v4: "-0.02", v5: "0.05",
        v6: "-0.01", v7: "0.03", v8: "0.02", v9: "-0.01", v10: "0.04",
        v11: "0.02", v12: "-0.03", v13: "0.01", v14: "0.05", v15: "-0.02",
        v16: "0.01", v17: "-0.02", v18: "0.03", v19: "-0.01", v20: "0.02",
        v21: "-0.01", v22: "0.02", v23: "0.01", v24: "-0.03", v25: "0.02",
        v26: "-0.01", v27: "0.01", v28: "0.01"
      });
    });
  }

  if (btnFillSuspicious) {
    btnFillSuspicious.addEventListener("click", () => {
      populatePreset({
        amount: "899.00",
        time_val: "42000",
        v1: "-1.85", v2: "2.10", v3: "-2.40", v4: "4.15", v5: "-1.20",
        v6: "-0.80", v7: "-2.30", v8: "1.20", v9: "-1.90", v10: "-3.80",
        v11: "3.75", v12: "-4.90", v13: "0.15", v14: "-6.40", v15: "-0.25",
        v16: "-2.80", v17: "-3.60", v18: "-1.20", v19: "0.85", v20: "0.60",
        v21: "0.45", v22: "-0.15", v23: "-0.20", v24: "0.10", v25: "0.20",
        v26: "0.05", v27: "0.40", v28: "0.15"
      });
    });
  }

  function populatePreset(data) {
    for (const [key, val] of Object.entries(data)) {
      const field = document.getElementById(key);
      if (field) {
        field.value = val;
        field.dispatchEvent(new Event("input", { bubbles: true }));
      }
    }
  }
});
