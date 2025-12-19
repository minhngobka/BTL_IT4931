let selectedProduct = null;
let currentPage = 1;
const limit = 20;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', () => {
    loadPage(currentPage);
});

// Load sản phẩm theo trang
async function loadPage(page) {
    const skip = (page - 1) * limit;
    try {
        const response = await fetch(`/api/products?skip=${skip}&limit=${limit}`);
        const result = await response.json();

        const products = result.products || [];
        const total = result.total || 0;
        totalPages = Math.ceil(total / limit);

        const grid = document.getElementById('productGrid');
        grid.innerHTML = '';

        products.forEach(product => {
            const card = createProductCard(product);
            grid.appendChild(card);
        });

        renderPaginationControls(page);
    } catch (error) {
        console.error('Lỗi load sản phẩm:', error);
    }
}

// Tạo thẻ hiển thị sản phẩm
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
        <div class="product-name">${product.product_name || 'Sản phẩm'}</div>
        <div class="product-price">${(product.price || 0).toLocaleString()}₫</div>
    `;

    card.addEventListener('click', () => selectProduct(product, card));
    return card;
}

// Xử lý chọn sản phẩm để lấy gợi ý
function selectProduct(product, element) {
    document.querySelectorAll('.product-card').forEach(el => {
        el.classList.remove('selected');
    });

    element.classList.add('selected');
    selectedProduct = product;
    getRecommendations(product._id || product.product_id);
}

// Gọi API lấy gợi ý sản phẩm
async function getRecommendations(productId) {
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId })
        });

        const data = await response.json();
        displayRecommendations(data.recommendations);
    } catch (error) {
        console.error('Lỗi lấy gợi ý:', error);
    }
}

// Hiển thị các sản phẩm được gợi ý
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="empty-state">Không có gợi ý nào</p>';
        return;
    }

    container.innerHTML = recommendations.map(rec => `
        <div class="recommendation-card">
            <div class="product-name">${rec.product_name}</div>
            <div class="product-price">${(rec.price || 0).toLocaleString()}₫</div>
            <div class="confidence-badge">Độ phù hợp: ${rec.confidence}</div>
        </div>
    `).join('');
}

// Hiển thị các nút phân trang
function renderPaginationControls(current) {
    const container = document.getElementById('paginationControls');
    container.innerHTML = '';

    // « Previous button
    if (current > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '«';
        prevBtn.addEventListener('click', () => {
            currentPage--;
            loadPage(currentPage);
        });
        container.appendChild(prevBtn);
    }

    const maxPagesToShow = 5;
    let startPage = Math.max(1, current - 2);
    let endPage = Math.min(totalPages, current + 2);

    // Adjust if at start
    if (current <= 3) {
        endPage = Math.min(5, totalPages);
    }

    // Adjust if at end
    if (current >= totalPages - 2) {
        startPage = Math.max(totalPages - 4, 1);
    }

    // Always show first page
    if (startPage > 1) {
        addPageButton(container, 1);
        if (startPage > 2) {
            container.appendChild(createEllipsis());
        }
    }

    // Middle pages
    for (let i = startPage; i <= endPage; i++) {
        addPageButton(container, i, i === current);
    }

    // Always show last page
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            container.appendChild(createEllipsis());
        }
        addPageButton(container, totalPages);
    }

    // » Next button
    if (current < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '»';
        nextBtn.addEventListener('click', () => {
            currentPage++;
            loadPage(currentPage);
        });
        container.appendChild(nextBtn);
    }
}

function addPageButton(container, page, isActive = false) {
    const btn = document.createElement('button');
    btn.textContent = page;
    if (isActive) btn.classList.add('active');
    btn.addEventListener('click', () => {
        currentPage = page;
        loadPage(currentPage);
    });
    container.appendChild(btn);
}

function createEllipsis() {
    const span = document.createElement('span');
    span.textContent = '...';
    span.className = 'ellipsis';
    return span;
}

