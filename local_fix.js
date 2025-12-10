(function () {
    console.log("Local Archiver V54 Running (Parasite Mode)...");
    window.scrollBy(0, 100); setTimeout(() => window.scrollBy(0, -100), 500);

    function queryAllDeep(selector, root = document) {
        let elements = Array.from(root.querySelectorAll(selector));
        const hosts = Array.from(root.querySelectorAll('*')).filter(e => e.shadowRoot);
        for (const host of hosts) {
            elements = elements.concat(queryAllDeep(selector, host.shadowRoot));
        }
        return elements;
    }

    function fixAll() {
        const targets = [
            ...queryAllDeep('iframe'),
            ...queryAllDeep('video'),
            ...queryAllDeep('a[href*="youtube.com"], a[href*="youtu.be"], a[href*="vimeo.com"]')
        ];

        const blockedKeywords = ['googlesyndication', 'doubleclick', 'googleads', 'safeframe', 'adservice', 'adnxs', 'ads', 'ad-'];

        targets.forEach(el => {
            if (el.dataset.patched === "true") return;

            let tagName = el.tagName.toLowerCase();
            let src = "";

            if (tagName === 'iframe') src = el.src || el.dataset.src || "";
            else if (tagName === 'video') src = el.currentSrc || el.src || "";
            else if (tagName === 'a') {
                src = el.href;
                // 檢查 <a> 裡面有沒有圖片，如果沒有，跳過 (避免殺到普通文字連結)
                if (!el.querySelector('img') && el.offsetWidth < 100) return;
            }

            if (!src || src === "about:blank") return;
            if (el.offsetWidth < 30) return;
            if (blockedKeywords.some(keyword => src.includes(keyword))) return;

            let bg = 'rgba(0,0,0,0.8)', icon = '🔗', txt = '開啟內容', col = '#007bff', url = src;

            if (src.includes('youtube') || src.includes('youtu.be')) {
                let m = src.match(/([a-zA-Z0-9_-]{11})/);
                if (m) { bg = 'url(https://img.youtube.com/vi/' + m[1] + '/hqdefault.jpg)'; col = '#c00'; icon = '▶'; txt = 'YouTube'; url = 'https://www.youtube.com/watch?v=' + m[1]; }
            } else if (src.includes('vimeo')) {
                let m = src.match(/video\/(\d+)/);
                if (m) { bg = 'url(https://vumbnail.com/' + m[1] + '.jpg)'; col = '#1ab7ea'; icon = '▶'; txt = 'Vimeo'; url = 'https://vimeo.com/' + m[1]; }
            } else if (tagName === 'video') {
                icon = '🎬'; txt = '原始檔'; col = '#28a745'; bg = 'rgba(0,0,0,0.5)';
            }

            // --- V54 策略分支 ---

            if (tagName === 'a') {
                // 策略 A: 針對原本就是 <a> 的元素 (Facade)
                // 我們不替換它，而是清空它的肚子，直接把按鈕樣式「寄生」給它
                console.log("寄生目標:", el);

                // 1. 清空原本內容 (圖片、圖示)
                el.innerHTML = '';

                // 2. 注入我們的按鈕內容 (作為子 DIV)
                let innerBtn = document.createElement('div');
                innerBtn.style.cssText = `width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;`;
                innerBtn.innerHTML = `<div style="background:rgba(0,0,0,0.7);padding:5px 15px;border-radius:20px;text-align:center;color:white;font-weight:bold;font-size:14px;box-shadow:0 2px 5px rgba(0,0,0,0.5);">${icon} ${txt}</div>`;
                el.appendChild(innerBtn);

                // 3. 強制賦予樣式 (寄生)
                el.style.background = `${bg} center/cover no-repeat`;
                el.style.border = `2px solid ${col}`;
                el.style.boxSizing = 'border-box';
                el.style.display = 'flex'; // 確保 flex 生效
                el.style.textDecoration = 'none';
                el.target = "_blank"; // 確保開新視窗

                // 4. 移除原本可能有的 class 干擾 (選擇性)
                // el.className = 'my-fix-card'; 

            } else {
                // 策略 B: 針對 iframe/video (標準處理)
                // 這些不是連結，所以我們要在外面包一個連結，或覆蓋一個連結

                // 先處理父層連結干擾
                let parentLink = el.closest('a');
                if (parentLink) {
                    parentLink.removeAttribute('href');
                    parentLink.style.cursor = 'default';
                    parentLink.onclick = (e) => e.preventDefault();
                }

                let card = document.createElement('a');
                card.className = 'my-fix-card';
                card.href = url;
                card.target = "_blank";
                card.rel = "noopener noreferrer";

                card.style.cssText = `position:absolute;top:0;left:0;width:100%;height:100%;background:${bg} center/cover no-repeat;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:2147483647 !important;cursor:pointer;border:2px solid ${col};box-sizing:border-box;border-radius:inherit;text-decoration:none;`;
                card.innerHTML = `<div style="background:rgba(0,0,0,0.7);padding:5px 15px;border-radius:20px;text-align:center;color:white;font-weight:bold;font-size:14px;box-shadow:0 2px 5px rgba(0,0,0,0.5);">${icon} ${txt}</div>`;

                if (el.parentNode) {
                    let p = el.parentNode;
                    if (getComputedStyle(p).position === 'static') p.style.position = 'relative';
                    p.insertBefore(card, el);
                    el.style.opacity = '0';
                    el.style.pointerEvents = 'none';
                }
            }

            el.dataset.patched = "true";
        });
    }
    setInterval(fixAll, 1000);
})();
