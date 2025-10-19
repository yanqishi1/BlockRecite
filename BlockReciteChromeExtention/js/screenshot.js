let isScreenshotMode = false;
let overlay = null;
let selection = null;
let instructions = null;

// 接收来自 background script 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'initScreenshot') {
        try {
            initializeScreenshot();
            sendResponse({ success: true });
        } catch (error) {
            console.error('Screenshot initialization failed:', error);
            sendResponse({ success: false, error: error.message });
        }
    }
    return true; // 保持消息通道开放
});

function initializeScreenshot() {
    if (isScreenshotMode) return;
    isScreenshotMode = true;

    // 创建覆盖层
    overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 999999;
        cursor: crosshair;
    `;

    // 创建选择区域
    selection = document.createElement('div');
    selection.style.cssText = `
        position: absolute;
        border: 2px solid #4CAF50;
        background: rgba(76, 175, 80, 0.1);
        display: none;
        pointer-events: none;
    `;

    // 创建提示文本
    instructions = document.createElement('div');
    instructions.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        color: white;
        background: rgba(0, 0, 0, 0.7);
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 14px;
        z-index: 1000000;
    `;
    instructions.textContent = '按住鼠标左键拖动选择区域，松开完成截图';

    overlay.appendChild(selection);
    overlay.appendChild(instructions);
    document.body.appendChild(overlay);

    let isSelecting = false;
    let startX, startY;

    // 鼠标按下事件
    overlay.addEventListener('mousedown', (e) => {
        isSelecting = true;
        startX = e.clientX;
        startY = e.clientY;
        selection.style.display = 'block';
        selection.style.left = startX + 'px';
        selection.style.top = startY + 'px';
        selection.style.width = '0';
        selection.style.height = '0';
    });

    // 鼠标移动事件
    overlay.addEventListener('mousemove', (e) => {
        if (!isSelecting) return;

        const currentX = e.clientX;
        const currentY = e.clientY;

        const width = Math.abs(currentX - startX);
        const height = Math.abs(currentY - startY);

        selection.style.left = Math.min(startX, currentX) + 'px';
        selection.style.top = Math.min(startY, currentY) + 'px';
        selection.style.width = width + 'px';
        selection.style.height = height + 'px';
    });

    // 鼠标松开事件
    overlay.addEventListener('mouseup', async () => {
        if (!isSelecting) return;
        isSelecting = false;

        const rect = selection.getBoundingClientRect();
        
        try {
            // 捕获屏幕
            const stream = await navigator.mediaDevices.getDisplayMedia({
                preferCurrentTab: true
            });
            
            const video = document.createElement('video');
            video.srcObject = stream;
            
            await new Promise(resolve => video.onloadedmetadata = resolve);
            video.play();

            // 等待一帧以确保视频已经开始播放
            await new Promise(resolve => requestAnimationFrame(resolve));

            const dpr = window.devicePixelRatio;
            const scrollX = window.scrollX;
            const scrollY = window.scrollY;

            const canvas = document.createElement('canvas');
            canvas.width = rect.width;
            canvas.height = rect.height;
            
            const ctx = canvas.getContext('2d');

            // 计算实际的截图区域
            const sourceX = (rect.left + scrollX);
            const sourceY = (rect.top + scrollY);
            const sourceWidth = rect.width;
            const sourceHeight = rect.height;

            // 在绘制之前添加调试信息
            console.log('截图区域信息:', {
                rect: {
                    left: rect.left,
                    top: rect.top,
                    width: rect.width,
                    height: rect.height
                },
                scroll: {
                    x: scrollX,
                    y: scrollY
                },
                source: {
                    x: sourceX,
                    y: sourceY,
                    width: sourceWidth,
                    height: sourceHeight
                }
            });

            // 绘制到画布上
            ctx.drawImage(
                video,
                sourceX,
                sourceY,
                sourceWidth,
                sourceHeight,
                0,
                0,
                canvas.width,
                canvas.height
            );

            // 停止视频流
            stream.getTracks().forEach(track => track.stop());

            // 保存截图
            canvas.toBlob(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'screenshot.png';
                a.click();
                URL.revokeObjectURL(url);
            }, 'image/png', 1.0);

        } catch (err) {
            console.error('截图失败:', err);
        }

        cleanup();
    });

    // ESC 键取消截图
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            cleanup();
        }
    });
}

function cleanup() {
    if (overlay && overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
    }
    isScreenshotMode = false;
    overlay = null;
    selection = null;
    instructions = null;
} 