document.getElementById('captureBtn').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'capture' }, (response) => {
        if (response.screenshotUrl) {
            const screenshotImg = document.getElementById('screenshotImg');
            screenshotImg.src = response.screenshotUrl;
            screenshotImg.style.display = 'block';

            // 创建一个下载链接
            const link = document.createElement('a');
            link.href = response.screenshotUrl;
            link.download = 'screenshot.png';
            link.click();
        }
    });
});

document.getElementById('backEndIP').addEventListener('change', function() {
    // 获取当前选择的值
    var selectedValue = this.value;

    // 更新 Chrome 插件的全局变量（使用 chrome.storage API）
    chrome.storage.local.set({ backEndIP: selectedValue }, function() {
        console.log('Backend IP has been set to: ' + selectedValue);
    });
});

// 初始化：从 Chrome 存储中获取并设置下拉框的值
chrome.storage.local.get('backEndIP', function(result) {
    if (result.backEndIP) {
        document.getElementById('backEndIP').value = result.backEndIP;
    }
});