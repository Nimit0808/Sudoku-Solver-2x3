document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const solveBtn = document.getElementById('solve-btn');
    const loadingState = document.getElementById('loading-state');
    const errorBox = document.getElementById('error-box');
    const resultContainer = document.getElementById('result-container');
    
    const cameraBtn = document.getElementById('camera-btn');
    const cameraContainer = document.getElementById('camera-container');
    const cameraFeed = document.getElementById('camera-feed');
    const captureBtn = document.getElementById('capture-btn');
    const closeCameraBtn = document.getElementById('close-camera-btn');
    const cameraCanvas = document.getElementById('camera-canvas');

    const cropContainer = document.getElementById('crop-container');
    const cropImage = document.getElementById('crop-image');
    const cropSolveBtn = document.getElementById('crop-solve-btn');
    const cancelCropBtn = document.getElementById('cancel-crop-btn');

    let currentFile = null;
    let cameraStream = null;
    let cropper = null;

    // Camera Handlers
    cameraBtn.addEventListener('click', async () => {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            cameraFeed.srcObject = cameraStream;
            dropZone.style.display = 'none';
            cameraContainer.style.display = 'block';
        } catch (err) {
            showError('Could not access the camera. Please allow camera permissions.');
        }
    });

    closeCameraBtn.addEventListener('click', () => {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
        }
        cameraContainer.style.display = 'none';
        dropZone.style.display = 'block';
    });

    captureBtn.addEventListener('click', () => {
        cameraCanvas.width = cameraFeed.videoWidth;
        cameraCanvas.height = cameraFeed.videoHeight;
        const ctx = cameraCanvas.getContext('2d');
        ctx.drawImage(cameraFeed, 0, 0, cameraCanvas.width, cameraCanvas.height);
        
        cameraCanvas.toBlob((blob) => {
            const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
            
            // Stop camera
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
            }
            cameraContainer.style.display = 'none';
            
            handleFile(file);
        }, 'image/jpeg', 0.95);
    });

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Click handlers
    dropZone.addEventListener('click', (e) => {
        if (e.target !== browseBtn && e.target !== cameraBtn) {
            fileInput.click();
        }
    });

    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file.');
            return;
        }

        const reader = new FileReader();
        
        reader.onload = (e) => {
            // Load into cropper instead of directly solving
            cropImage.src = e.target.result;
            dropZone.style.display = 'none';
            cropContainer.style.display = 'block';
            resetUI();
            
            if (cropper) {
                cropper.destroy();
            }
            
            cropper = new Cropper(cropImage, {
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                restore: false,
                guides: true,
                center: true,
                highlight: false,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
            });
        };
        
        reader.readAsDataURL(file);
    }

    cancelCropBtn.addEventListener('click', () => {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        cropContainer.style.display = 'none';
        dropZone.style.display = 'block';
    });

    cropSolveBtn.addEventListener('click', () => {
        if (!cropper) return;
        
        // Get cropped canvas
        const canvas = cropper.getCroppedCanvas();
        
        canvas.toBlob(async (blob) => {
            currentFile = new File([blob], "cropped.jpg", { type: "image/jpeg" });
            
            // Cleanup cropper UI
            cropper.destroy();
            cropper = null;
            cropContainer.style.display = 'none';
            
            // Show preview
            imagePreview.src = canvas.toDataURL();
            previewContainer.style.display = 'block';
            
            // Automatically solve
            await processSolve();
        }, 'image/jpeg', 0.95);
    });

    // The old solveBtn logic is now inside processSolve
    solveBtn.addEventListener('click', async () => {
        if (currentFile) {
            await processSolve();
        }
    });

    async function processSolve() {
        if (!currentFile) return;

        solveBtn.style.display = 'none';
        loadingState.style.display = 'block';
        errorBox.style.display = 'none';
        resultContainer.style.display = 'none';

        const formData = new FormData();
        formData.append('image', currentFile);

        try {
            const response = await fetch('/solve', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            loadingState.style.display = 'none';

            if (!response.ok) {
                showError(data.error || 'An error occurred during processing.');
                // Show extracted grid if it failed to solve
                if (data.extracted_grid) {
                    renderGrid('original-grid', data.extracted_grid, null, true);
                    document.querySelector('#result-container .grid-section:last-child').style.display = 'none';
                    resultContainer.style.display = 'flex';
                }
                solveBtn.style.display = 'inline-block';
                return;
            }

            if (data.success) {
                document.querySelector('#result-container .grid-section:last-child').style.display = 'block';
                renderGrid('original-grid', data.original_grid, null, true);
                renderGrid('solved-grid', data.solved_grid, data.original_grid, false);
                resultContainer.style.display = 'flex';
            } else {
                showError(data.error);
                solveBtn.style.display = 'inline-block';
            }

        } catch (error) {
            loadingState.style.display = 'none';
            solveBtn.style.display = 'inline-block';
            showError('Failed to connect to the server.');
        }
    }

    function renderGrid(containerId, gridData, originalData = null, editable = false) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        for (let i = 0; i < 6; i++) {
            for (let j = 0; j < 6; j++) {
                const val = gridData[i][j];
                
                if (editable) {
                    const input = document.createElement('input');
                    input.type = 'number';
                    input.min = '1';
                    input.max = '6';
                    input.className = 'cell cell-input';
                    input.dataset.row = i;
                    input.dataset.col = j;
                    
                    if (val !== 0) {
                        input.value = val;
                    }
                    container.appendChild(input);
                } else {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    
                    if (val === 0) {
                        cell.textContent = '';
                        cell.classList.add('empty-cell');
                    } else {
                        cell.textContent = val;
                        if (originalData && originalData[i][j] === 0) {
                            cell.classList.add('new');
                            cell.style.animationDelay = `${(i * 6 + j) * 0.02}s`;
                        }
                    }
                    container.appendChild(cell);
                }
            }
        }
    }

    // Handle solving from the edited grid
    const solveManualBtn = document.createElement('button');
    solveManualBtn.className = 'btn btn-primary';
    solveManualBtn.textContent = 'Solve Edited Grid';
    solveManualBtn.style.marginTop = '1rem';
    solveManualBtn.id = 'solve-manual-btn';
    
    document.querySelector('#result-container .grid-section:first-child').appendChild(solveManualBtn);

    solveManualBtn.addEventListener('click', async () => {
        // Collect data from inputs
        const inputs = document.querySelectorAll('#original-grid .cell-input');
        const manualGrid = [];
        for (let i = 0; i < 6; i++) {
            manualGrid.push([0,0,0,0,0,0]);
        }
        
        inputs.forEach(input => {
            const r = parseInt(input.dataset.row);
            const c = parseInt(input.dataset.col);
            const v = parseInt(input.value);
            if (!isNaN(v) && v >= 1 && v <= 6) {
                manualGrid[r][c] = v;
            }
        });

        const formData = new FormData();
        formData.append('grid', JSON.stringify(manualGrid));

        try {
            const response = await fetch('/solve_manual', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.success) {
                document.querySelector('#result-container .grid-section:last-child').style.display = 'block';
                renderGrid('solved-grid', data.solved_grid, manualGrid, false);
                errorBox.style.display = 'none';
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('Failed to solve.');
        }
    });

    function showError(msg) {
        errorBox.textContent = msg;
        errorBox.style.display = 'block';
    }

    function resetUI() {
        errorBox.style.display = 'none';
        resultContainer.style.display = 'none';
        solveBtn.style.display = 'inline-block';
        loadingState.style.display = 'none';
    }
});
