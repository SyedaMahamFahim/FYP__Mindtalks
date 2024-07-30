// Function to handle file upload
function handleFileUpload(formData) {
    var progressBar = document.getElementById("progressBar");
    var progressText = document.getElementById("progressText");
    var processingMessage = document.getElementById("processingMessage");

    // Initialize progress bar
    progressBar.style.width = "0%";
    progressText.innerText = "0%";

    // Show loading spinner
    document.getElementById("loading").style.display = "block";

    // Create XMLHttpRequest for file upload
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload", true);

    // Event listener for upload progress
    xhr.upload.onprogress = function (event) {
      if (event.lengthComputable) {
        var percentComplete = (event.loaded / event.total) * 100;
        progressBar.style.width = percentComplete + "%";
        progressText.innerText = percentComplete.toFixed(2) + "%";
      }
    };

    // Event listener for upload completion
    xhr.onload = function () {
      if (xhr.status === 200) {
        // Hide loading spinner
        document.getElementById("loading").style.display = "none";
        // Display file path
        document.getElementById("filePath").innerText = xhr.responseText;
        // Show processing message
        processingMessage.style.display = "block";
        // Call processing function
        processUploadedFile(xhr.responseText);
      } else {
        // Hide loading spinner
        document.getElementById("loading").style.display = "none";
        // Show error message
        document.getElementById("error").style.display = "block";
      }
    };

    // Send FormData
    xhr.send(formData);
  }

  // Function to process the uploaded file
  // Function to process the uploaded file
function processUploadedFile(filename) {
    // Create XMLHttpRequest for processing
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/processing", true);
    xhr.setRequestHeader("Content-Type", "application/json");
  
    // Event listener for processing completion
    xhr.onload = function () {
      if (xhr.status === 200) {
        console.log('xhr.responseText',xhr.responseText)
        // Hide processing message
        document.getElementById("processingMessage").style.display = "none";
        // Display logs
        document.getElementById("logs").innerHTML = xhr.responseText;
        // Display processing progress
        document.getElementById("processingProgress").innerText = "Processing completed";
      } else {
        // Hide processing message
        document.getElementById("processingMessage").style.display = "none";
        // Log error
        console.error("Error processing file");
        // Handle error
      }
    };
  
    // Event listener for processing updates
    xhr.onreadystatechange = function () {
      if (xhr.readyState === XMLHttpRequest.LOADING) {
        // Display processing progress
        document.getElementById("processingProgress").innerText = "Processing in progress...";
      }
    };
  
    // Send filename to be processed
    xhr.send(JSON.stringify({ filename: filename }));
  }
  

  // Event listener for form submission
  document.addEventListener("DOMContentLoaded", function () {
    document
      .getElementById("uploadForm")
      .addEventListener("submit", function (e) {
        e.preventDefault(); // Prevent page reload
        var formData = new FormData(this);
        // Call function to handle file upload
        handleFileUpload(formData);
      });
  });