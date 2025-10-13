/**
 * Font Awesome 图标加载检测和备用方案
 */

(function() {
    'use strict';

    // 图标映射表 - 将Font Awesome图标映射到Unicode符号或Emoji
    const iconFallbackMap = {
        'fa-search-location': '🔍',
        'fa-location-dot': '📍',
        'fa-expand-arrows-alt': '⇔',
        'fa-undo': '↶',
        'fa-refresh': '↻',
        'fa-home': '🏠',
        'fa-building': '🏢',
        'fa-university': '🏛️',
        'fa-city': '🌆',
        'fa-search': '🔍',
        'fa-map-marker-alt': '📌',
        'fa-info-circle': 'ℹ️',
        'fa-check-circle': '✓',
        'fa-eye': '👁️',
        'fa-star': '⭐',
        'fa-heart': '❤️'
    };

    // 检测Font Awesome是否成功加载
    function checkFontAwesome() {
        // 创建一个测试元素
        const testElement = document.createElement('i');
        testElement.className = 'fas fa-home';
        testElement.style.position = 'absolute';
        testElement.style.left = '-9999px';
        testElement.style.fontSize = '16px';
        document.body.appendChild(testElement);

        // 获取元素的计算样式
        const computedStyle = window.getComputedStyle(testElement, ':before');
        const content = computedStyle.getPropertyValue('content');

        // 清理测试元素
        document.body.removeChild(testElement);

        // 检查是否有Font Awesome的内容
        return content && content !== 'none' && content !== '""';
    }

    // 替换图标为备用文本
    function replaceIconsWithFallback() {
        const icons = document.querySelectorAll('.fas, .far, .fab, .fa');

        icons.forEach(icon => {
            // 获取图标类名
            const classList = Array.from(icon.classList);
            let fallbackText = '•'; // 默认回退符号

            // 查找匹配的图标类
            for (const className of classList) {
                if (iconFallbackMap[className]) {
                    fallbackText = iconFallbackMap[className];
                    break;
                }
            }

            // 替换图标内容
            if (!icon.textContent || icon.textContent.trim() === '') {
                icon.textContent = fallbackText;
                icon.style.fontFamily = '"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif';
                icon.style.fontStyle = 'normal';
            }
        });
    }

    // DOM加载完成后检测
    function initIconFallback() {
        if (!checkFontAwesome()) {
            console.log('Font Awesome未加载，启用备用图标');
            document.body.classList.add('icon-fallback');

            // 添加备用图标样式
            const style = document.createElement('style');
            style.textContent = `
                .icon-fallback .fas,
                .icon-fallback .far,
                .icon-fallback .fab,
                .icon-fallback .fa {
                    font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
                    font-weight: normal !important;
                    font-style: normal !important;
                    display: inline-block;
                }

                /* 确保图标容器正确显示 */
                .icon-fallback .no-results-enhanced i,
                .icon-fallback .empty-icon i,
                .icon-fallback .no-houses-icon i {
                    font-size: 4rem !important;
                    line-height: 1 !important;
                }
            `;
            document.head.appendChild(style);

            // 替换现有图标
            replaceIconsWithFallback();

            // 监听DOM变化，替换动态添加的图标
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        replaceIconsWithFallback();
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        } else {
            console.log('Font Awesome加载成功');
        }
    }

    // 等待DOM和字体加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // 延迟检测以确保字体加载完成
            setTimeout(initIconFallback, 100);
        });
    } else {
        setTimeout(initIconFallback, 100);
    }

    // 监听字体加载事件（如果支持）
    if ('fonts' in document) {
        document.fonts.ready.then(function() {
            setTimeout(initIconFallback, 50);
        });
    }
})();