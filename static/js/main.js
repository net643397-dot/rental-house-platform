// 主要JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 价格格式化
    const priceElements = document.querySelectorAll('.price-number');
    priceElements.forEach(element => {
        const price = parseInt(element.textContent);
        if (price) {
            element.textContent = price.toLocaleString();
        }
    });

    // 搜索表单增强
    const searchForm = document.querySelector('form');
    if (searchForm) {
        // 自动保存搜索条件到localStorage
        const inputs = searchForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                localStorage.setItem(this.name, this.value);
            });

            // 恢复之前的搜索条件
            const savedValue = localStorage.getItem(input.name);
            if (savedValue && !input.value) {
                input.value = savedValue;
            }
        });
    }

    // 收藏功能
    window.addToFavorites = function(houseId) {
        fetch('/api/favorites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                house_id: houseId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('收藏成功！');
                updateFavoriteButtons();
            } else {
                alert('收藏失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('操作失败，请稍后重试');
        });
    };

    // 取消收藏功能
    window.removeFavorite = function(houseId) {
        if (confirm('确定要取消收藏这套房源吗？')) {
            fetch('/api/favorites', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    house_id: houseId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('取消收藏成功！');
                    updateFavoriteButtons();
                } else {
                    alert('取消收藏失败：' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('操作失败，请稍后重试');
            });
        }
    };

    // 更新收藏按钮状态
    function updateFavoriteButtons() {
        const favoriteButtons = document.querySelectorAll('[onclick*="addToFavorites"]');

        favoriteButtons.forEach(button => {
            const houseId = button.getAttribute('onclick').match(/\d+/)[0];

            // 从服务器检查收藏状态
            fetch(`/api/favorites/check/${houseId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.is_favorite) {
                        button.classList.remove('btn-outline-danger');
                        button.classList.add('btn-danger');
                        button.innerHTML = '<i class="fas fa-heart"></i> 已收藏';
                        button.setAttribute('onclick', `removeFavorite(${houseId})`);
                    } else {
                        button.classList.remove('btn-danger');
                        button.classList.add('btn-outline-danger');
                        button.innerHTML = '<i class="fas fa-heart"></i> 收藏';
                        button.setAttribute('onclick', `addToFavorites(${houseId})`);
                    }
                })
                .catch(error => {
                    console.error('Error checking favorite status:', error);
                });
        });
    }

    // 页面加载时更新收藏按钮状态
    updateFavoriteButtons();

    // 图片懒加载
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // 搜索建议功能
    const searchInput = document.querySelector('#search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    // 这里可以添加搜索建议的AJAX请求
                    console.log('搜索建议:', query);
                }, 300);
            }
        });
    }
});

// 返回顶部功能
window.addEventListener('scroll', function() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const backToTopBtn = document.querySelector('#backToTop');

    if (!backToTopBtn) {
        // 创建返回顶部按钮
        const btn = document.createElement('button');
        btn.id = 'backToTop';
        btn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        btn.className = 'btn btn-primary position-fixed';
        btn.style.cssText = `
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: none;
        `;
        btn.onclick = function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };
        document.body.appendChild(btn);
    }

    const backToTop = document.querySelector('#backToTop');
    if (scrollTop > 300) {
        backToTop.style.display = 'block';
    } else {
        backToTop.style.display = 'none';
    }
});