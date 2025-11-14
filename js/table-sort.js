// Table sorting functionality
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('board-games-table');
    if (!table) return;

    const headers = table.querySelectorAll('thead th');
    let currentSort = {
        column: null,
        direction: 'asc'
    };

    headers.forEach((header, index) => {
        // Add sortable class to all headers
        header.classList.add('sortable');
        
        header.addEventListener('click', function() {
            const column = index;
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Determine sort direction
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.direction = 'asc';
            }

            // Remove sort classes from all headers
            headers.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            // Add sort class to current header
            header.classList.add(currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');

            // Sort rows
            rows.sort((a, b) => {
                const aCell = a.cells[column];
                const bCell = b.cells[column];
                
                let aText = aCell ? aCell.textContent.trim() : '';
                let bText = bCell ? bCell.textContent.trim() : '';

                // Try to parse as number
                const aNum = parseFloat(aText.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bText.replace(/[^0-9.-]/g, ''));
                
                let comparison = 0;
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    // Both are numbers
                    comparison = aNum - bNum;
                } else {
                    // String comparison
                    comparison = aText.localeCompare(bText, undefined, { 
                        numeric: true, 
                        sensitivity: 'base' 
                    });
                }

                return currentSort.direction === 'asc' ? comparison : -comparison;
            });

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
});

