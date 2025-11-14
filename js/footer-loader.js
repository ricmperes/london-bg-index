// Load footer
document.addEventListener('DOMContentLoaded', function() {
    const footerContainer = document.getElementById('footer-container');
    if (!footerContainer) return;

    // Check if we're using file:// protocol (fetch won't work)
    const isFileProtocol = window.location.protocol === 'file:';
    
    if (isFileProtocol) {
        // For local file viewing, use fallback footer directly
        footerContainer.innerHTML = `
            <footer class="site-footer">
                <div class="footer-container">
                    <div class="footer-left">K&S Libraries BG Index</div>
                    <div class="footer-center"></div>
                    <div class="footer-right">by Ricardo Peres, 2025</div>
                </div>
            </footer>
        `;
        return;
    }

    // Fetch and load footer (works on GitHub Pages and local servers)
    const isInPages = window.location.pathname.includes('/pages/');
    const footerPath = isInPages ? '../components/footer.html' : 'components/footer.html';
    fetch(footerPath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            footerContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading footer:', error);
            // Fallback footer if fetch fails
            footerContainer.innerHTML = `
                <footer class="site-footer">
                    <div class="footer-container">
                        <div class="footer-left"></div>
                        <div class="footer-center">K&S Libraries BG Index</div>
                        <div class="footer-right">by Ricardo Peres, 2025</div>
                    </div>
                </footer>
            `;
        });
});

