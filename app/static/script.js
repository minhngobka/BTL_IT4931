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
    
    // Xử lý NaN price
    const price = isNaN(product.price) ? 0 : product.price;
    
    card.innerHTML = `
        <img src="${product.image_url || 'https://via.placeholder.com/200'}" alt="${product.product_name}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;">
        <div class="product-name">${product.product_name || 'Sản phẩm'}</div>
        <div class="product-category">${product.category_name || 'Chưa phân loại'}</div>
        <div class="product-price">${price.toLocaleString()}₫</div>
    `;

    // Click để vào trang chi tiết
    card.addEventListener('click', () => {
        window.location.href = `/product/${product.product_id}`;
    });

    return card;
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

    if (current <= 3) {
        endPage = Math.min(5, totalPages);
    }

    if (current >= totalPages - 2) {
        startPage = Math.max(totalPages - 4, 1);
    }

    if (startPage > 1) {
        addPageButton(container, 1);
        if (startPage > 2) {
            container.appendChild(createEllipsis());
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        addPageButton(container, i, i === current);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            container.appendChild(createEllipsis());
        }
        addPageButton(container, totalPages);
    }

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