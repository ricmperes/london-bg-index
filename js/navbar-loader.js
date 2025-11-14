// Load navbar and set active state based on current page
document.addEventListener('DOMContentLoaded', function() {
    const navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) return;

    // Determine current page from the HTML file name
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    let pageKey = 'index';
    
    if (currentPage.includes('index') || currentPage === '' || currentPage === '/') {
        pageKey = 'index';
    } else if (currentPage.includes('table')) {
        pageKey = 'table';
    } else if (currentPage.includes('about')) {
        pageKey = 'about';
    }

    // Check if we're using file:// protocol (fetch won't work)
    const isFileProtocol = window.location.protocol === 'file:';
    
    if (isFileProtocol) {
        // For local file viewing, use fallback navbar directly
        console.warn('Opening files locally (file:// protocol). Fetch API is not available. Using fallback navbar.');
        const isInPages = window.location.pathname.includes('/pages/') || window.location.pathname.includes('\\pages\\');
        const homeLink = isInPages ? '../index.html' : 'index.html';
        const tableLink = isInPages ? 'table.html' : 'pages/table.html';
        const aboutLink = isInPages ? 'about.html' : 'pages/about.html';
        const logoText = 'K&S Libraries BG Index';
        
        navbarContainer.innerHTML = `
            <nav class="navbar">
                <div class="nav-container">
                    <a href="${homeLink}" class="nav-logo">${logoText}</a>
                    <ul class="nav-menu">
                        <li><a href="${homeLink}" ${pageKey === 'index' ? 'class="active"' : ''}>Home</a></li>
                        <li><a href="${tableLink}" ${pageKey === 'table' ? 'class="active"' : ''}>Catalogue</a></li>
                        <li><a href="${aboutLink}" ${pageKey === 'about' ? 'class="active"' : ''}>About</a></li>
                    </ul>
                </div>
            </nav>
        `;
        return;
    }

    // Fetch and load navbar (works on GitHub Pages and local servers)
    const isInPages = window.location.pathname.includes('/pages/');
    const navbarPath = isInPages ? '../components/navbar.html' : 'components/navbar.html';
    fetch(navbarPath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            navbarContainer.innerHTML = html;
            
            // Adjust paths based on current location (isInPages already defined above)
            const allLinks = navbarContainer.querySelectorAll('a[data-nav-href]');
            allLinks.forEach(link => {
                const targetPath = link.getAttribute('data-nav-href');
                if (isInPages) {
                    // If we're in /pages, adjust paths
                    if (targetPath === 'index.html') {
                        link.href = '../index.html';
                    } else if (targetPath.startsWith('pages/')) {
                        link.href = targetPath.replace('pages/', '');
                    } else {
                        link.href = targetPath;
                    }
                } else {
                    // If we're in root, use paths as-is
                    link.href = targetPath;
                }
            });
            
            // Set active class on the current page link
            const activeLink = navbarContainer.querySelector(`a[data-page="${pageKey}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        })
        .catch(error => {
            console.error('Error loading navbar:', error);
            console.error('Using fallback navbar.');
            // Fallback navbar if fetch fails
            const isInPages = window.location.pathname.includes('/pages/');
            const homeLink = isInPages ? '../index.html' : 'index.html';
            const tableLink = isInPages ? 'table.html' : 'pages/table.html';
            const aboutLink = isInPages ? 'about.html' : 'pages/about.html';
            const logoText = 'K&S Libraries BG Index';
            
            navbarContainer.innerHTML = `
                <nav class="navbar">
                    <div class="nav-container">
                        <a href="${homeLink}" class="nav-logo">${logoText}</a>
                        <ul class="nav-menu">
                            <li><a href="${homeLink}" ${pageKey === 'index' ? 'class="active"' : ''}>Home</a></li>
                            <li><a href="${tableLink}" ${pageKey === 'table' ? 'class="active"' : ''}>Catalogue</a></li>
                            <li><a href="${aboutLink}" ${pageKey === 'about' ? 'class="active"' : ''}>About</a></li>
                        </ul>
                    </div>
                </nav>
            `;
        });
});

