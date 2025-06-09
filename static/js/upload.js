document.addEventListener('DOMContentLoaded', function() {

  const fileInput = document.getElementById('fileInput');
  const preview = document.getElementById("preview");
  const dropZone = document.getElementById('dropZone');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const errorMessageContainer = document.getElementById('errorMessageContainer');
  const detectButton = document.getElementById('detectButton');
  const imageUrlInput = document.getElementById('imageUrlInput');
  const detectFromUrlButton = document.getElementById('detectFromUrlButton');
  
  const card = document.querySelector('.card');
  const detectUrl = card.dataset.detectUrl;
  
  function handleFiles(files) {
    if (files.length === 0) return;
    const file = files[0];

    if (!file.type.startsWith('image/')) {
      const fileName = file.name;
      const fileType = file.type || 'Tidak diketahui';
      const errorMessage = `File tidak valid: "${fileName}".<br>Tipe file terdeteksi: <strong>${fileType}</strong>.<br>Harap unggah file gambar.`;
      
      displayErrorMessage(errorMessage);
      preview.src = "";
      preview.style.display = "none";
      fileInput.value = "";
      return;
    }

    clearMessages();
    const reader = new FileReader();
    reader.onload = function(e) {
      preview.src = e.target.result;
      preview.style.display = "block";
    };
    reader.readAsDataURL(file);

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
  }
  
  function displayLoading(isLoading) {
    loadingIndicator.style.display = isLoading ? "block" : "none";
  }

  function displayErrorMessage(message) {
    errorMessageContainer.innerHTML = `<p>${message}</p>`;
  }

  function clearMessages() {
    loadingIndicator.style.display = "none";
    errorMessageContainer.innerHTML = "";
  }

// Ganti seluruh fungsi sendDetectionRequest yang lama dengan yang ini

  function sendDetectionRequest(body, headers = {}) {
      clearMessages();
      displayLoading(true);

      fetch(detectUrl, {
          method: 'POST',
          body: body,
          headers: headers,
      })
      .then(response => {
          // Cek jika response tidak ok (misal, status 500 atau 400)
          if (!response.ok) {
              // Coba parse body error dari JSON
              return response.json().then(err => {
                  // Buat error baru agar bisa ditangkap oleh .catch()
                  throw new Error(err.error || 'Terjadi kesalahan tidak diketahui di server.');
              });
          }
          return response.json();
      })
      .then(data => {
          displayLoading(false); // Sembunyikan loading indicator di sini

          // REVISI UTAMA: Cek isi respons dari server
          if (data.error) {
              // JIKA SERVER MENGEMBALIKAN ERROR: Tampilkan pesan error, jangan redirect.
              let fullErrorMessage = data.error;
              if (data.message) {
                  fullErrorMessage += `: ${data.message}`;
              }
              displayErrorMessage(fullErrorMessage);
          } else if (data.prediction_id) {
              // JIKA SERVER MENGEMBALIKAN SUKSES: Lakukan redirect seperti biasa.
              const resultPageUrl = `/result/${data.prediction_id}`;
              window.location.href = resultPageUrl;
          } else {
              // Fallback jika respons tidak dikenali
              displayErrorMessage("Menerima respons tidak valid dari server.");
          }
      })
      .catch(error => {
          // Blok .catch() ini akan menangani error jaringan atau error yang kita 'throw' di atas
          displayLoading(false);
          console.error('Error saat deteksi:', error);
          displayErrorMessage(error.message);
      });
  }
  detectButton.addEventListener('click', () => {
      if (fileInput.files.length === 0) {
          displayErrorMessage("Silakan pilih atau jatuhkan file gambar terlebih dahulu.");
          return;
      }
      const formData = new FormData();
      formData.append('fileInput', fileInput.files[0]);
      sendDetectionRequest(formData);
  });

  detectFromUrlButton.addEventListener('click', () => {
      const imageUrl = imageUrlInput.value.trim();
      if (!imageUrl) {
          displayErrorMessage("Silakan masukkan URL gambar.");
          return;
      }
      if (!imageUrl.startsWith('http://') && !imageUrl.startsWith('https://')) {
          displayErrorMessage("URL tidak valid. Harus diawali dengan http:// atau https://");
          return;
      }

      sendDetectionRequest(
          JSON.stringify({ imageUrl: imageUrl }),
          { 'Content-Type': 'application/json' }
      );
  });

  fileInput.addEventListener('change', (event) => {
    handleFiles(event.target.files);
  });

  dropZone.addEventListener('dragover', (event) => {
    event.preventDefault(); 
    dropZone.style.borderColor = '#007bff';
  });
  dropZone.addEventListener('dragleave', (event) => {
    event.preventDefault(); 
    dropZone.style.borderColor = '#3b82f6';
  });
  dropZone.addEventListener('drop', (event) => {
    event.preventDefault();
    dropZone.style.borderColor = '#3b82f6';
    handleFiles(event.dataTransfer.files);
  });
  
  dropZone.addEventListener('click', (event) => { 
    if (event.target.tagName !== 'BUTTON') {
      fileInput.click(); 
    }
  });

  const text = "Gunakan alat kami untuk mendeteksi apakah sebuah gambar dibuat oleh kecerdasan buatan. Alat ini cocok untuk siapa saja yang ingin mengecek keaslian gambar dengan cepat dan akurat.";
  const typingElement = document.getElementById("typing-text");
  let index = 0;

  function typeText() {
    if (typingElement && index < text.length) {
      typingElement.innerHTML += text.charAt(index);
      index++;
      setTimeout(typeText, 30);
    }
  }
  
  typeText();
});