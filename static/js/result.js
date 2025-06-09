document.addEventListener('DOMContentLoaded', function() {
    // Data sekarang datang dari objek `predictionData`
    const label = predictionData.label;
    const confidence = predictionData.confidence;
    const shareableUrl = predictionData.pageUrl;

    const resultLabel = document.getElementById("resultLabel");
    const progressBar = document.getElementById("progressBar");
    const percentText = document.getElementById("percentText");

    // Menampilkan hasil prediksi awal
    let resultText = "";
    if (label === "RealArt") {
      resultText = "Gambar Asli (Real)";
      progressBar.style.background = "linear-gradient(to right, #3b82f6, #0ea5e9)";
    } else if (label === "AiArtData") {
      resultText = "Gambar Buatan AI";
      progressBar.style.background = "linear-gradient(to right, #ef4444, #f59e0b)";
    } else {
      resultText = "Tidak Diketahui";
      progressBar.style.background = "#94a3b8";
    }
    resultLabel.textContent = resultText;
    progressBar.style.width = confidence + "%";
    percentText.textContent = confidence + "%";

    // --- Logika Tombol Berbagi ---
    const copyLinkBtn = document.getElementById('copyLinkBtn');
    const shareTwitterBtn = document.getElementById('shareTwitterBtn');
    const shareFacebookBtn = document.getElementById('shareFacebookBtn');
    const shareWhatsappBtn = document.getElementById('shareWhatsappBtn');

    const shareText = `Hasil analisis Detectify AI: Gambar ini adalah ${resultText} dengan keyakinan ${confidence}%. Lihat hasilnya di sini:`;

    copyLinkBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(shareableUrl).then(() => {
            copyLinkBtn.textContent = 'Disalin!';
            setTimeout(() => { copyLinkBtn.textContent = 'Salin Tautan'; }, 2000);
        });
    });

    shareTwitterBtn.addEventListener('click', () => {
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareableUrl)}`;
        window.open(twitterUrl, '_blank');
    });

    shareFacebookBtn.addEventListener('click', () => {
        const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareableUrl)}`;
        window.open(facebookUrl, '_blank');
    });

    shareWhatsappBtn.addEventListener('click', () => {
        const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText + ' ' + shareableUrl)}`;
        window.open(whatsappUrl, '_blank');
    });

    // --- LOGIKA TOMBOL FEEDBACK (BARU) ---
    const feedbackBtnAi = document.getElementById('feedbackBtnAi');
    const feedbackBtnReal = document.getElementById('feedbackBtnReal');
    const feedbackContainer = document.getElementById('feedbackContainer');
    const feedbackMessage = document.getElementById('feedbackMessage');

    function sendFeedback(event) {
        const button = event.target;
        const predictionId = button.dataset.predictionId;
        const correctLabel = button.dataset.correctLabel;

        // Tampilkan status loading dan nonaktifkan tombol
        feedbackMessage.style.display = 'block';
        feedbackMessage.className = 'alert alert-info mt-3';
        feedbackMessage.textContent = 'Mengirim masukan...';
        feedbackBtnAi.disabled = true;
        feedbackBtnReal.disabled = true;

        fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prediction_id: predictionId,
                correct_label: correctLabel
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                feedbackMessage.className = 'alert alert-success mt-3';
                feedbackMessage.textContent = data.message;
                // Sembunyikan seluruh kontainer feedback setelah berhasil
                if(feedbackContainer) {
                    setTimeout(() => { feedbackContainer.style.display = 'none'; }, 2000);
                }
            } else {
                feedbackMessage.className = 'alert alert-danger mt-3';
                feedbackMessage.textContent = `Error: ${data.message}`;
                // Aktifkan kembali tombol jika gagal
                feedbackBtnAi.disabled = false;
                feedbackBtnReal.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            feedbackMessage.className = 'alert alert-danger mt-3';
            feedbackMessage.textContent = 'Gagal terhubung ke server.';
            // Aktifkan kembali tombol jika gagal
            feedbackBtnAi.disabled = false;
            feedbackBtnReal.disabled = false;
        });
    }

    // Hanya tambahkan event listener jika tombolnya ada di halaman
    if (feedbackBtnAi) {
        feedbackBtnAi.addEventListener('click', sendFeedback);
    }
    if (feedbackBtnReal) {
        feedbackBtnReal.addEventListener('click', sendFeedback);
    }
});