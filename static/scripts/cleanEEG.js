document.addEventListener("DOMContentLoaded", function () {
  const forms = document.querySelectorAll(".preprocessEeg");

  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      const formData = new FormData(form);
      const fileInput = form.querySelector(".fileInput");
      const folderName = form.querySelector('input[name="folder_name"]').value;
      const subject = form.querySelector('#subject').value; // Get selected subject
      const session = form.querySelector('#session').value; // Get selected session
      const messageDiv = form.querySelector('.message'); // Get message div

      if (fileInput && fileInput.files.length > 0) {
        formData.append("file", fileInput.files[0]);
        formData.append("folder_name", folderName);
        formData.append("subject", subject); // Append subject to FormData
        formData.append("session", session); // Append session to FormData
        
        // Show loading message
        messageDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Extracting features...';

        fetch("/preprocess_eeg_data", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.error) {
              messageDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
              console.log("this is the data", data);
              messageDiv.innerHTML = `<div class="alert alert-success">File processed successfully. 
              <a href="${data.eog_file}" target="_blank">EOG File</a>
              <a href="${data.baseline_file}" target="_blank">Baseline File</a>
              <a href="${data.pickle_file}" target="_blank">Pickle File</a>
              <a href="${data.events_file}" target="_blank">Events File</a>
              <a href="${data.eeg_file}" target="_blank">EEG File</a>

              
              </div>`;
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            messageDiv.innerHTML = `<div class="alert alert-danger">Error processing the file.</div>`;
          })
          .finally(() => {
            form.reset();
          });
      } else {
        alert("Please select a file.");
      }
    });
  });
});
