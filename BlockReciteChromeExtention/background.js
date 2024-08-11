// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function setupContextMenu() {
    chrome.contextMenus.create({
        id: 'define-word',
        title: 'BlockRecite',
        contexts: ['selection']
    });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "capture") {
        chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
            sendResponse({ screenshotUrl: dataUrl });
        });
        return true; // 表示异步响应
    }
});

chrome.runtime.onInstalled.addListener(() => {
    setupContextMenu();
});

chrome.contextMenus.onClicked.addListener((data, tab) => {
    // Store the last word in chrome.storage.session.
    chrome.storage.session.set({ lastWord: data.selectionText });

    // Make sure the side panel is open.
    chrome.sidePanel.open({ tabId: tab.id });
});


// 跨域请求设置
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    new Promise((resolve, reject) => {
        if (typeof request !== 'object' || !request.type) {
            console.error('参数异常');
            reject(`消息 ${JSON.stringify(request)} 格式不符合规范`);
            return;
        }
        switch (request.type) {
            case 'get':
                fetch(request.url).then((res) => {
                    resolve(res.json());
                });
                break;
            case 'post':
                fetch(request.url).then((res) => {
                    resolve(res.json());
                });
                break;
            default:
                console.log("Not Support this Method")
        }
    }).then((res) => {
        sendResponse(res);
    });
    return true;
});

