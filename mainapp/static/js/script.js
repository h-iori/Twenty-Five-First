document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navbar = document.querySelector('.navbar');
    const closeMenu = document.querySelector('#close-menu');
    const dropdowns = document.querySelectorAll('.dropdown-menu');
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    const searchToggle = document.querySelector('.search-toggle');
    const searchContainer = document.querySelector('.search-container');
    const closeSearch = document.querySelector('.close-search');

    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Bootstrap dropdown instance handling
    const closeAllDropdowns = () => {
        dropdownToggles.forEach(toggle => {
            const dropdownInstance = bootstrap.Dropdown.getInstance(toggle);
            if (dropdownInstance) {
                dropdownInstance.hide();
            }
        });
    };

    // Toggle menu on button click
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const isActive = navLinks.classList.toggle('active');
            menuToggle.setAttribute('aria-expanded', isActive ? 'true' : 'false');
            // Close search when menu opens
            if (searchContainer.classList.contains('active')) {
                searchContainer.classList.remove('active');
                navbar.classList.remove('expanded');
            }
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
        if (navLinks.classList.contains('active') &&
            !navLinks.contains(event.target) &&
            !menuToggle.contains(event.target)) {
            navLinks.classList.remove('active');
            menuToggle.setAttribute('aria-expanded', 'false');
            closeAllDropdowns();
        }
    });

    // Close menu and submenu when clicking back
    if (closeMenu) {
        closeMenu.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();

            // Close the main menu
            navLinks.classList.remove('active');
            menuToggle.setAttribute('aria-expanded', 'false');

            // Close any open dropdown
            closeAllDropdowns();
        });
    }

    // Prevent clicks inside nav-links from closing it
    if (navLinks) {
        navLinks.addEventListener('click', (event) => {
            event.stopPropagation();
        });
    }

    // Search functionality
    if (searchToggle && searchContainer) {
        searchToggle.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            searchContainer.classList.toggle('active');
            navbar.classList.toggle('expanded');
            
            // Focus on input when opened
            if (searchContainer.classList.contains('active')) {
                searchContainer.querySelector('.search-input').focus();
            }
            // Close menu when search opens
            if (navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });

        // Close search when clicking outside
        document.addEventListener('click', (event) => {
            if (searchContainer.classList.contains('active') &&
                !navbar.contains(event.target)) {
                searchContainer.classList.remove('active');
                navbar.classList.remove('expanded');
            }
        });

        // Close search with close button
        if (closeSearch) {
            closeSearch.addEventListener('click', () => {
                searchContainer.classList.remove('active');
                navbar.classList.remove('expanded');
            });
        }
    }
});