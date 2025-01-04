document.addEventListener('DOMContentLoaded', function() {
    const captureBtn = document.getElementById('captureBtn');
    
    // 点击截图按钮
    captureBtn.addEventListener('click', function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            // 先注入脚本，然后发送消息
            chrome.scripting.executeScript({
                target: { tabId: tabs[0].id },
                files: ['js/screenshot.js']
            }).then(() => {
                chrome.tabs.sendMessage(tabs[0].id, {action: 'initScreenshot'}, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error(chrome.runtime.lastError);
                        return;
                    }
                    window.close(); // 成功启动截图后关闭popup
                });
            }).catch(err => {
                console.error('Failed to inject script:', err);
            });
        });
    });

    // 保持其他代码不变...
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