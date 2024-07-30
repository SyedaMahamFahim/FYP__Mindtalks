document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("modelForm");

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData(form);
    const fileInput = form.querySelector(".fileInput");
    const messageDiv = form.querySelector(".message"); // Get message div

    if (fileInput && fileInput.files.length > 0) {
      formData.append("file", fileInput.files[0]);


      fileInput.style.display = "none";
      form.querySelector(".modelBtn").style.display = "none";
      formLabel = this.querySelector(".model-label");
      formLabel.style.display = "none";
      formToggle = this.querySelector(".form-toggle");
      formToggle.style.display = "none";

      // Show loading message
      messageDiv.innerHTML = displayLoadingMessage();

      // AJAX request to handle file upload and processing
      fetch("/predict", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          // Handle response based on success or error
          if (data.error) {
            messageDiv.innerHTML = displayError(data.error);
          } else {
            console.log("this is the data", data);
            modelResultShow(data);
            // Display success message or result details
            messageDiv.innerHTML = ``;
          }
        })
        .catch((error) => {
          messageDiv.innerHTML = displayError(data.error);
        })
        .finally(() => {
          form.reset(); // Reset the form after processing
        });
    } else {
      alert("Please select a file.");
    }
  });
});

const displayLoadingMessage = () => {
  return `
    <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
      <div class="text-center">
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
          <span class="visually-hidden">Loading...</span>
        </div>
        <div class="mt-3">
          <h5>Model is predicting the output...</h5>
        </div>
      </div>
    </div>
  `;
};

const displayError = (message) => {
  return `
    <div class="alert alert-danger">${message}</div>
    <button type="button" class="btn btn-primary mt-3" onclick="window.location.reload();">Try Again</button>
  `;
};

const modelAccuray = (accuracy) => {
  return `<div class="alert alert-success">Accuracy: ${accuracy}</div>`;
};
const modelResultShow = (data) => {
  const classDistribution = data?.class_distribution;
  const metrics = {
    accuracy: data.accuracy,
    f1_score: data.f1_score,
    precision: data.precision,
    recall: data.recall,
  };

  let accuracyHtml = modelAccuray(data.accuracy);
  let classTable_Html = classDistributionTable(classDistribution);
  let metricsHtml = modelMetricsDisplay(metrics);
  let classificationReport = classificationReportTable(
    data.classification_report
  );

  let graphsHtml = displayImages(data.confusion_matrix_image_url, data.roc_auc);

  document.getElementById("modelAccuracy").innerHTML = accuracyHtml;
  document.getElementById("modelGraphs").innerHTML = graphsHtml;
  document.getElementById("modelMetrics").innerHTML = metricsHtml;
  document.getElementById("classDistributionTable").innerHTML = classTable_Html;
  document.getElementById("classificationReport").innerHTML =
    classificationReport;
};

const classDistributionTable = (classDistribution) => {
  const tableHtml = `

         <div class="card my-4">
  <div class="card-header text-center">
    <h3>Class Distribution</h3>
  </div>
  <div class="card-body">
    <table class="table table-bordered table-striped">
      <thead>
        <tr>
          <th>Class</th>
          <th>Count</th>
        </tr>
      </thead>
      <tbody>
        ${Object.entries(classDistribution)
          .map(
            ([key, value]) => `
          <tr>
            <td>${key}</td>
            <td>${value}</td>
          </tr>
        `
          )
          .join("")}
      </tbody>
    </table>
  </div>
</div>

        `;
  return tableHtml;
};

const classificationReportTable = (classificationReport) => {
  const classNames = {
    0: "DOWN",
    1: "LEFT",
    2: "RIGHT",
    3: "UP",
  };

  const tableHtml = `
    <div class="card my-4">
      <div class="card-header text-center">
        <h4>Classification Report</h4>
      </div>
      <div class="card-body">
        <table class="table table-bordered table-striped">
          <thead>
            <tr>
              <th>Class</th>
              <th>F1-score</th>
              <th>Precision</th>
              <th>Recall</th>
              <th>Support</th>
            </tr>
          </thead>
          <tbody>
            ${Object.keys(classificationReport)
              .map((key) => {
                if (
                  key === "accuracy" ||
                  key === "macro avg" ||
                  key === "weighted avg"
                ) {
                  return "";
                }
                const className = classNames[key] || key;
                return `
                <tr>
                  <td>${className}</td>
                  <td>${classificationReport[key]["f1-score"]}</td>
                  <td>${classificationReport[key]["precision"]}</td>
                  <td>${classificationReport[key]["recall"]}</td>
                  <td>${classificationReport[key]["support"]}</td>
                </tr>
              `;
              })
              .join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
  return tableHtml;
};

const modelMetricsDisplay = (metrics) => {
  const metricsHtml = `
    <div class="card my-4">
      <div class="card-header text-center">
        <h4>Model Metrics</h4>
      </div>
      <div class="card-body">
        <table class="table table-bordered table-striped">
          <tbody>
            <tr>
              <th>Accuracy</th>
              <td>${metrics.accuracy}</td>
            </tr>
            <tr>
              <th>F1-score</th>
              <td>${metrics.f1_score}</td>
            </tr>
            <tr>
              <th>Precision</th>
              <td>${metrics.precision}</td>
            </tr>
            <tr>
              <th>Recall</th>
              <td>${metrics.recall}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
  return metricsHtml;
};

const displayImages = (confusionMatrixUrl, rocAucUrl) => {
  const imagesHtml = `
    <div class="card my-4">
      <div class="card-header text-center">
        <h4>Confusion Matrix</h4>
      </div>
      <div class="card-body text-center">
        <img src="${confusionMatrixUrl}" class="img-fluid" alt="Confusion Matrix">
      </div>
    </div>
    <div class="card my-4">
      <div class="card-header text-center">
        <h4>ROC AUC Curve</h4>
      </div>
      <div class="card-body text-center">
        <img src="${rocAucUrl}" class="img-fluid" alt="ROC AUC Curve">
      </div>
    </div>
  `;
  return imagesHtml;
};
