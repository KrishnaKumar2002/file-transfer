const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const videoPreview = document.getElementById('videoPreview');
const downloadLink = document.getElementById('downloadLink');

let mediaRecorder;
let recordedChunks = [];

startBtn.addEventListener('click', async () => {
    try {
        // Request screen and audio capture
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: true,
            audio: true
        });

        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            // Create a Blob from the recorded chunks
            const blob = new Blob(recordedChunks, { type: 'video/mp4' });
            const url = URL.createObjectURL(blob);
            
            // Set the video source and download link
            videoPreview.src = url;
            downloadLink.href = url;
            downloadLink.style.display = 'block'; // Show the download link
        };

        mediaRecorder.start();
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } catch (error) {
        console.error('Error accessing media devices.', error);
    }
});

stopBtn.addEventListener('click', () => {
    if (mediaRecorder) {
        mediaRecorder.stop();
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
});
