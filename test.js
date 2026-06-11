import { showAlert } from "./uiHelpers.js";

const dropArea = document.getElementById("dropArea");
const fileInput = document.getElementById("fileInput");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");

export let selectedFilePath = null;
let localUpdateButtonsCallback = () => {};

function displayFileInfo(details) {
  if (details && details.name) {
    fileName.textContent = details.name;
    fileInfo.style.display = "block";
  } else {
    fileName.textContent = "No file selected";
    fileInfo.style.display = "none";
  }
}

export function setupFileHandlers(updateButtonsCb) {
  localUpdateButtonsCallback = updateButtonsCb;

  if (selectedFilePath) {
    const justName = selectedFilePath.substring(selectedFilePath.lastIndexOf('/') + 1).substring(selectedFilePath.lastIndexOf('\\') + 1);
    displayFileInfo({ name: justName });
  } else {
    displayFileInfo(null);
  }
  localUpdateButtonsCallback(); 

  if (window.runtime && window.runtime.OnFileDrop) {
    window.runtime.OnFileDrop((x, y, paths) => {
      if (paths && paths.length > 0) {
        selectedFilePath = paths[0];
        const justName = selectedFilePath.substring(selectedFilePath.lastIndexOf('/') + 1).substring(selectedFilePath.lastIndexOf('\\') + 1);
        displayFileInfo({ name: justName });
        localUpdateButtonsCallback();
        showAlert("File dropped: " + justName, "success");
      }
    }, true);
  } else {
    console.error("Wails OnFileDrop runtime function is not available.");
  }

  ["dragenter", "dragover"].forEach((eventName) => {
    dropArea.addEventListener(eventName, (e) => {
      preventDefaults(e);
      highlight();
    }, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(eventName, (e) => {
      preventDefaults(e);
      unhighlight();
    }, false);
  });

  dropArea.addEventListener("click", () => {
    if (window.go && window.go.main && window.go.main.App && window.go.main.App.SelectSourceFile) {
      window.go.main.App.SelectSourceFile("Select Source File")
        .then(filePath => {
          if (filePath) {
            selectedFilePath = filePath;
            const justName = filePath.substring(filePath.lastIndexOf('/') + 1).substring(filePath.lastIndexOf('\\') + 1);
            displayFileInfo({ name: justName });
            showAlert("File selected: " + justName, "success");
          } else {
          }
          localUpdateButtonsCallback();
        })
        .catch(err => {
          showAlert("Error selecting file: " + err, "error");
          selectedFilePath = null;
          displayFileInfo(null);
          localUpdateButtonsCallback();
        });
    } else {
      showAlert("Backend function SelectSourceFile not available.", "error");
    }
  });

  fileInput.addEventListener("change", () => {
    if (dropArea.click) {
        dropArea.click();
    }
  });
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function highlight() {
  dropArea.classList.add("active");
}

function unhighlight() {
  dropArea.classList.remove("active");
}

export function clearSelectedFile() {
  selectedFilePath = null;
  displayFileInfo(null);
  if (fileInput) {
    fileInput.value = "";
  }
  localUpdateButtonsCallback();
}