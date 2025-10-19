document.addEventListener('DOMContentLoaded', function() {
    const articleInput = document.getElementById('articleInput');
    const formatBtn = document.getElementById('formatBtn');
    const restoreBtn = document.getElementById('restoreBtn');
    const inputSection = document.getElementById('inputSection');
    const displaySection = document.getElementById('displaySection');
    const formattedContent = document.getElementById('formattedContent');
    const fontSizeSelect = document.getElementById('fontSizeSelect');

    // 从本地存储加载内容
    loadFromStorage();

    // 格式化文章
    formatBtn.addEventListener('click', function() {
        const text = articleInput.value.trim();
        
        if (!text) {
            alert('请先输入文章内容！');
            return;
        }

        // 保存到本地存储
        saveToStorage(text);

        // 格式化文本
        const formatted = formatArticle(text);
        formattedContent.innerHTML = formatted;

        // 切换显示
        inputSection.classList.add('hidden');
        displaySection.classList.add('visible');
    });

    // 恢复编辑
    restoreBtn.addEventListener('click', function() {
        inputSection.classList.remove('hidden');
        displaySection.classList.remove('visible');
    });

    // 字体大小切换
    fontSizeSelect.addEventListener('change', function() {
        const selectedSize = this.value;
        
        // 移除所有字体大小类
        formattedContent.classList.remove('font-normal', 'font-large', 'font-big');
        
        // 添加选中的字体大小类
        formattedContent.classList.add('font-' + selectedSize);
        
        // 保存字体大小偏好
        saveFontSizePreference(selectedSize);
    });

    // 加载字体大小偏好
    loadFontSizePreference();

    // 格式化文章函数
    function formatArticle(text) {
        // 1. 按换行符分割段落
        let paragraphs = text.split(/\n\s*\n/);
        
        // 2. 清理每个段落
        paragraphs = paragraphs.map(p => {
            // 移除段落内的换行符，替换为空格
            p = p.replace(/\n/g, ' ');
            // 移除多余的空格
            p = p.replace(/\s+/g, ' ');
            // 去除首尾空格
            p = p.trim();
            return p;
        }).filter(p => p.length > 0); // 过滤空段落

        // 3. 将每个段落包装在 <p> 标签中
        const formattedParagraphs = paragraphs.map(p => {
            return `<p>${escapeHtml(p)}</p>`;
        });

        return formattedParagraphs.join('');
    }

    // HTML 转义函数
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 保存到本地存储
    function saveToStorage(text) {
        try {
            // 如果是 Chrome 扩展环境
            if (typeof chrome !== 'undefined' && chrome.storage) {
                chrome.storage.local.set({ articleText: text });
            } else {
                // 否则使用 localStorage
                localStorage.setItem('articleText', text);
            }
        } catch (e) {
            console.error('保存失败:', e);
        }
    }

    // 从本地存储加载
    function loadFromStorage() {
        try {
            // 如果是 Chrome 扩展环境
            if (typeof chrome !== 'undefined' && chrome.storage) {
                chrome.storage.local.get('articleText', function(result) {
                    if (result.articleText) {
                        articleInput.value = result.articleText;
                    }
                });
            } else {
                // 否则使用 localStorage
                const savedText = localStorage.getItem('articleText');
                if (savedText) {
                    articleInput.value = savedText;
                }
            }
        } catch (e) {
            console.error('加载失败:', e);
        }
    }

    // 保存字体大小偏好
    function saveFontSizePreference(size) {
        try {
            if (typeof chrome !== 'undefined' && chrome.storage) {
                chrome.storage.local.set({ fontSize: size });
            } else {
                localStorage.setItem('fontSize', size);
            }
        } catch (e) {
            console.error('保存字体大小失败:', e);
        }
    }

    // 加载字体大小偏好
    function loadFontSizePreference() {
        try {
            if (typeof chrome !== 'undefined' && chrome.storage) {
                chrome.storage.local.get('fontSize', function(result) {
                    const fontSize = result.fontSize || 'normal';
                    fontSizeSelect.value = fontSize;
                    formattedContent.classList.remove('font-normal', 'font-large', 'font-big');
                    formattedContent.classList.add('font-' + fontSize);
                });
            } else {
                const fontSize = localStorage.getItem('fontSize') || 'normal';
                fontSizeSelect.value = fontSize;
                formattedContent.classList.remove('font-normal', 'font-large', 'font-big');
                formattedContent.classList.add('font-' + fontSize);
            }
        } catch (e) {
            console.error('加载字体大小失败:', e);
        }
    }

    // 键盘快捷键支持
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter 触发排版
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (!inputSection.classList.contains('hidden')) {
                formatBtn.click();
            }
        }
        
        // Esc 键恢复编辑
        if (e.key === 'Escape') {
            if (displaySection.classList.contains('visible')) {
                restoreBtn.click();
            }
        }
    });
});

