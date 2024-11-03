

const loadingSpinner = document.getElementById('loading-spinner');

document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    const checkboxes = filterForm.querySelectorAll('input[type="checkbox"]');
    const loadingSpinner = document.getElementById('loading-spinner');

    function updateURL(formData) {
        const params = new URLSearchParams(formData);
        const newURL = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({}, '', newURL);
    }

    function updateContent(formData) {
        loadingSpinner.classList.remove('d-none');
        const searchParams = new URLSearchParams(formData);
        fetch(`${window.location.pathname}?${new URLSearchParams(formData)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            

            const contentContainer = document.querySelector('.row.row-cols-1');
            const newContent = doc.querySelector('.row.row-cols-1');
            contentContainer.innerHTML = newContent.innerHTML;
            

            const paginationContainer = document.querySelector('nav .pagination');
            const newPagination = doc.querySelector('nav .pagination');
            
            

            updateFilters(doc);
            initializeFavoriteButtons(document.querySelector('.row.row-cols-1'));
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            loadingSpinner.classList.add('d-none');
        });
    }

    function updateFilters(doc) {

        const categoriesContainer = document.querySelector('.categories-container');
        const newCategoriesContainer = doc.querySelector('.categories-container');
        if (categoriesContainer && newCategoriesContainer) {

            const expandedAccordions = Array.from(categoriesContainer.querySelectorAll('.accordion-collapse.show'))
                .map(accordion => accordion.id);
            
            categoriesContainer.innerHTML = newCategoriesContainer.innerHTML;
            

            expandedAccordions.forEach(id => {
                const accordion = categoriesContainer.querySelector(`#${id}`);
                if (accordion) {
                    accordion.classList.add('show');
                }
            });
        }


        const familiesContainer = document.querySelector('.families-container');
        const newFamiliesContainer = doc.querySelector('.families-container');
        if (familiesContainer && newFamiliesContainer) {

            const expandedAccordions = Array.from(familiesContainer.querySelectorAll('.accordion-collapse.show'))
                .map(accordion => accordion.id);
            
            familiesContainer.innerHTML = newFamiliesContainer.innerHTML;
            

            expandedAccordions.forEach(id => {
                const accordion = familiesContainer.querySelector(`#${id}`);
                if (accordion) {
                    accordion.classList.add('show');
                }
            });
        }
                
    const newCheckboxes = doc.querySelectorAll('input[type="checkbox"]');
    newCheckboxes.forEach(newCheckbox => {
        const existingCheckbox = document.querySelector(
            `input[type="checkbox"][name="${newCheckbox.name}"][value="${newCheckbox.value}"]`
        );
        if (existingCheckbox) {
            const newCount = newCheckbox.parentElement.querySelector('small').textContent;
            existingCheckbox.parentElement.querySelector('small').textContent = newCount;
        }
    });

      
        initializeCheckboxHandlers();
    }

    function initializeCheckboxHandlers() {
        const checkboxes = filterForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const formData = new FormData(filterForm);
                updateURL(formData);
                updateContent(formData);
            });
        });
    }

   
    initializeCheckboxHandlers();

});
document.addEventListener('DOMContentLoaded', function() {
    const filterSidebar = document.getElementById('filterSidebar');
    const showFiltersBtn = document.getElementById('showFilters');
    const closeFiltersBtn = document.getElementById('closeFilters');

    if (showFiltersBtn) {
        showFiltersBtn.addEventListener('click', function() {
            filterSidebar.classList.add('show');
            document.body.style.overflow = 'hidden';
        });
    }

    if (closeFiltersBtn) {
        closeFiltersBtn.addEventListener('click', function() {
            filterSidebar.classList.remove('show');
            document.body.style.overflow = '';
        });
    }

  
    document.addEventListener('click', function(event) {
        if (window.innerWidth < 992) {
            if (!filterSidebar.contains(event.target) && 
                !showFiltersBtn.contains(event.target) && 
                filterSidebar.classList.contains('show')) {
                filterSidebar.classList.remove('show');
                document.body.style.overflow = '';
            }
        }
    });

   
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            filterSidebar.classList.remove('show');
            document.body.style.overflow = '';
        }
    });
    initializeFavoriteButtons(document.querySelector('.row.row-cols-1'));
});