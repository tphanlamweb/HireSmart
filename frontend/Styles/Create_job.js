
    window.addEventListener('load', function () {
        const user = localStorage.getItem('loggedInUser');
        if (!user) {
            alert('Bạn cần đăng nhập HR để truy cập Dashboard!');
            window.location.href = '../html/Login.html';
            return;
        }
        console.log('HR Dashboard accessed by:', user);
        updateStats(); // Initial stats update
        updateLanguageUI(); // Initial language setup
        initActionButtons();
        initDragAndDrop();
        initModalHandlers();
    });

    // --- DOM ELEMENTS ---
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const jobForm = document.getElementById('jobForm');
    let sidebarOpen = false;
    let selectedRequirements = []; // Used for Drag & Drop logic

    // Jobs data (Initial set)
    let jobs = [
        { id: 1, title: 'Senior Developer', status: 'active', cvs: 5 },
        { id: 2, title: 'Marketing Manager', status: 'active', cvs: 3 },
        { id: 3, title: 'HR Specialist', status: 'active', cvs: 2 }
    ];

    // --- SIDEBAR TOGGLE & NAVIGATION ---

    menuToggle.addEventListener('click', function () {
        sidebarOpen = !sidebarOpen;
        if (sidebarOpen) {
            sidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
            // Only shift content on desktop
            if (window.innerWidth > 768) {
                mainContent.classList.add('with-sidebar');
            }
        } else {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            mainContent.classList.remove('with-sidebar');
        }
    });

    sidebarOverlay.addEventListener('click', function () {
        sidebarOpen = false;
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        mainContent.classList.remove('with-sidebar');
    });

    // Menu item click handler (Simple active state toggle)
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function () {
            document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Logout functionality
    document.querySelector('.logout-btn').addEventListener('click', function () {
        localStorage.removeItem('loggedInUser');
        window.location.href = '../html/Login.html';
    });

    function handleHRLogin(event) {
        event.preventDefault();
        window.location.href = "../html/Login.html";
    }

    // --- JOB STATS & FORM MANAGEMENT ---

    function updateStats() {
        const totalJobs = jobs.length;
        const activeJobs = jobs.filter(j => j.status === 'active').length;
        const totalCVs = jobs.reduce((sum, j) => sum + j.cvs, 0);
        const avgCVs = totalJobs > 0 ? Math.round(totalCVs / totalJobs) : 0;

        document.getElementById('totalJobs').textContent = totalJobs;
        document.getElementById('activeJobs').textContent = activeJobs;
        document.getElementById('totalCVs').textContent = totalCVs;
        document.getElementById('avgCVs').textContent = avgCVs;
    }

    // Toggle form visibility (This function is likely not needed if the form is always visible)
    function toggleForm() {
        // Since jobForm is already a fixed element, this function seems redundant 
        // unless you intend to hide the form content entirely.
        // If the 'Create new JD' button is meant to switch views, 
        // this function should handle the logic for displaying the form.
        jobForm.classList.toggle('active'); 
        // Note: The form-section CSS does not define 'active' behavior, 
        // only 'display: block' which is default.
    }

    function updateJobDescription() {
        // Collects all selected requirements into a hidden input field
        const items = Array.from(document.getElementById('droppedItems').children);
        const requirementsText = items.map(item => item.querySelector('.dropped-item-text').textContent).join(' | ');
        document.getElementById('jobDescription').value = requirementsText;
    }

    // Handle form submission
    function handleSubmit(event) {
        event.preventDefault();

        if (selectedRequirements.length === 0) {
            alert('Please select at least one requirement');
            return;
        }

        updateJobDescription();

        const newJob = {
            id: jobs.length + 1,
            title: document.getElementById('jobTitle').value,
            department: document.getElementById('department').value,
            location: document.getElementById('location').value,
            salary: document.getElementById('salary').value,
            status: document.getElementById('status').value,
            cvs: parseInt(document.getElementById('cvsPaid').value),
            requirements: selectedRequirements,
            description: document.getElementById('jobDescription').value
        };

        jobs.push(newJob);
        
        // Persist to localStorage
        try {
            const storageKey = 'createdJobs';
            const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
            existing.push({
                title: newJob.title,
                department: newJob.department,
                location: newJob.location,
                salary: newJob.salary,
                status: newJob.status,
                requirements: newJob.requirements,
                description: newJob.description
            });
            localStorage.setItem(storageKey, JSON.stringify(existing));
            alert('Job posting created successfully!\n\nJob Title: ' + newJob.title + '\nRequirements: ' + newJob.requirements.length);
        } catch (e) {
            console.error('Failed to save job to localStorage', e);
            alert('Error saving job');
        }

        // Reset form and UI states
        event.target.reset();
        selectedRequirements = [];
        document.getElementById('droppedItems').innerHTML = '';
        document.getElementById('emptyState').style.display = 'flex';
        document.getElementById('droppedItems').style.display = 'none';
        
        updateStats();
    }

    // --- ACTION BUTTONS (Create / Job List / News) ---
    function initActionButtons() {
        const container = document.querySelector('.action-buttons');
        if (!container) return;
        const saved = localStorage.getItem('selectedAction');

        // restore saved active state
        if (saved) {
            container.querySelectorAll('button').forEach(b => {
                if (b.classList.contains(saved)) {
                    b.classList.add('active');
                } else {
                    b.classList.remove('active');
                }
            });
        }

        container.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', function (e) {
                // Toggle active class locally
                container.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                // persist the clicked button's identifying class so other pages can restore
                // prefer known classes: 'btn-create', 'btn-list', 'btn-news'
                if (this.classList.contains('btn-create')) localStorage.setItem('selectedAction', 'btn-create');
                else if (this.classList.contains('btn-list')) localStorage.setItem('selectedAction', 'btn-list');
                else if (this.classList.contains('btn-news')) localStorage.setItem('selectedAction', 'btn-news');

                // If the button navigates, do that after setting active state
                if (this.classList.contains('btn-list')) {
                    // small delay to allow visual feedback before navigation
                    setTimeout(() => { window.location.href = 'Job_list.html'; }, 120);
                }
                if (this.classList.contains('btn-news')) {
                    // Navigate to news page if exists; placeholder behavior otherwise
                    setTimeout(() => { 
                        // update this path if you have a news page
                        // window.location.href = 'news.html';
                    }, 120);
                }
                if (this.classList.contains('btn-create')) {
                    // Ensure the form is visible and focused
                    const form = document.getElementById('jobForm');
                    if (form) form.classList.add('active');
                }
            });
        });
    }

    // --- MODAL HANDLERS (Add Custom Requirement) ---
    function initModalHandlers() {
        window.openCustomModal = function () {
            const modal = document.getElementById('customModal');
            if (modal) modal.classList.add('active');
        };

        window.closeCustomModal = function () {
            const modal = document.getElementById('customModal');
            if (modal) modal.classList.remove('active');
            const input = document.getElementById('customRequirement');
            if (input) input.value = '';
        };

        window.addCustomRequirement = function () {
            const input = document.getElementById('customRequirement');
            if (!input) return;
            const text = input.value.trim();
            if (!text) { alert('Please enter a requirement'); return; }

            const pool = document.getElementById('requirementsPool');
            if (!pool) return;

            // Create a new requirement item in pool
            const item = document.createElement('div');
            item.className = 'requirement-item';
            item.setAttribute('draggable', 'true');
            item.innerHTML = `<span class="requirement-icon">✳️</span><span class="requirement-text"></span>`;
            item.querySelector('.requirement-text').textContent = text;

            pool.appendChild(item);
            // Re-initialize drag listeners for the new item
            attachDragSourceListeners(item);

            closeCustomModal();
        };
    }

    // --- DRAG & DROP IMPLEMENTATION ---
    function initDragAndDrop() {
        const pool = document.getElementById('requirementsPool');
        const dropZone = document.getElementById('dropZone');
        const droppedItems = document.getElementById('droppedItems');
        const emptyState = document.getElementById('emptyState');

        if (!pool || !dropZone || !droppedItems || !emptyState) return;

        // Attach to all current source items
        pool.querySelectorAll('.requirement-item').forEach(attachDragSourceListeners);

        // Make drop zone accept drops
        dropZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', function () {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', function (e) {
            e.preventDefault();
            dropZone.classList.remove('drag-over');

            const text = e.dataTransfer.getData('text/plain');
            if (!text) return;

            // Create dropped item
            const droppedEl = createDroppedItemElement(text);
            droppedItems.appendChild(droppedEl);

            // Update UI
            emptyState.style.display = 'none';
            droppedItems.style.display = 'flex';
            selectedRequirements.push(text);
            updateSelectedCount();
            updateJobDescription();
        });

        // Reordering within droppedItems
        let draggedDroppedEl = null;
        droppedItems.addEventListener('dragstart', function (e) {
            const target = e.target.closest('.dropped-item');
            if (!target) return;
            draggedDroppedEl = target;
            e.dataTransfer.effectAllowed = 'move';
        });

        droppedItems.addEventListener('dragover', function (e) {
            e.preventDefault();
            const target = e.target.closest('.dropped-item');
            if (!target || target === draggedDroppedEl) return;
            const bounding = target.getBoundingClientRect();
            const offset = e.clientY - bounding.top;
            if (offset > bounding.height / 2) {
                target.parentNode.insertBefore(draggedDroppedEl, target.nextSibling);
            } else {
                target.parentNode.insertBefore(draggedDroppedEl, target);
            }
        });

        droppedItems.addEventListener('drop', function (e) {
            e.preventDefault();
            // update selectedRequirements order
            refreshSelectedRequirementsFromDOM();
            updateSelectedCount();
            updateJobDescription();
        });
    }

    function attachDragSourceListeners(item) {
        item.addEventListener('dragstart', function (e) {
            const textEl = item.querySelector('.requirement-text');
            const text = textEl ? textEl.textContent : item.textContent;
            e.dataTransfer.setData('text/plain', text);
            // set a custom drag image to avoid odd ghosting behavior
            if (item.cloneNode) {
                const crt = item.cloneNode(true);
                crt.style.position = 'absolute';
                crt.style.top = '-9999px';
                crt.style.left = '-9999px';
                document.body.appendChild(crt);
                e.dataTransfer.setDragImage(crt, 10, 10);
                setTimeout(() => document.body.removeChild(crt), 0);
            }
            item.classList.add('dragging');
        });
        item.addEventListener('dragend', function () {
            item.classList.remove('dragging');
        });
    }

    function createDroppedItemElement(text) {
        const el = document.createElement('div');
        el.className = 'dropped-item';
        el.setAttribute('draggable', 'true');
        el.innerHTML = `
            <div class="dropped-item-content">
                <div class="dropped-item-index"></div>
                <div class="dropped-item-text"></div>
            </div>
            <div class="dropped-item-actions">
                <button class="remove-btn">Remove</button>
            </div>
        `;
        el.querySelector('.dropped-item-text').textContent = text;

        // Remove handler
        el.querySelector('.remove-btn').addEventListener('click', function () {
            el.parentNode.removeChild(el);
            refreshSelectedRequirementsFromDOM();
            updateSelectedCount();
            updateJobDescription();
            const droppedItems = document.getElementById('droppedItems');
            const emptyState = document.getElementById('emptyState');
            if (droppedItems.children.length === 0) {
                droppedItems.style.display = 'none';
                emptyState.style.display = 'flex';
            }
        });

        return el;
    }

    function refreshSelectedRequirementsFromDOM() {
        const droppedItems = document.getElementById('droppedItems');
        selectedRequirements = [];
        if (!droppedItems) return;
        Array.from(droppedItems.children).forEach((child, idx) => {
            const text = child.querySelector('.dropped-item-text')?.textContent || '';
            selectedRequirements.push(text);
            const idxEl = child.querySelector('.dropped-item-index');
            if (idxEl) idxEl.textContent = (idx + 1) + '.';
        });
    }

    function updateSelectedCount() {
        const el = document.getElementById('selectedCount');
        if (el) el.textContent = selectedRequirements.length;
    }

    // Update hidden jobDescription input based on selected items
    function updateJobDescription() {
        const jobDescEl = document.getElementById('jobDescription');
        if (!jobDescEl) return;
        jobDescEl.value = selectedRequirements.join(' | ');
    }

    // --- LANGUAGE MANAGEMENT (Partial Code Provided) ---

    let currentLanguage = localStorage.getItem('language') || 'vi';

    function setLanguage(lang) {
        currentLanguage = lang;
        localStorage.setItem('language', lang);
        updateLanguageUI();
        translatePage();
    }

    function updateLanguageUI() {
        const currentLangSpan = document.getElementById('currentLang');
        if (currentLangSpan) {
            currentLangSpan.textContent = currentLanguage === 'vi' ? '🇻🇳' : '🇺🇸';
        }
        // Set event listeners for language options
        document.querySelectorAll('.lang-option').forEach(option => {
            option.addEventListener('click', function() {
                setLanguage(this.getAttribute('data-lang'));
            });
        });
    }

    function translatePage() {
        // The translations object (translations) is missing in the provided code snippet
        if (typeof translations === 'undefined') {
            console.warn("Translation object 'translations' is missing.");
            return;
        }
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (translations[currentLanguage] && translations[currentLanguage][key]) {
                // The loop was cut off here, assuming it sets text content
                // element.textContent = translations[currentLanguage][key]; 
            }
        });
    }

    // --- DRAG & DROP LOGIC (Missing Implementation for brevity, but variables are set) ---
    // Note: The actual Drag & Drop logic (dragstart, dragover, drop, addCustomRequirement, openCustomModal, closeCustomModal) 
    // needs to be fully implemented separately for the UI to be fully functional.
    
