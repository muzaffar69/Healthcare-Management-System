// Medical Practice Management - Frontend JavaScript
// This file handles all UI interactions and communicates with Python backend via PyWebView API

class MedicalPracticeApp {
    constructor() {
        this.currentTab = 'doctors';
        this.theme = localStorage.getItem('theme') || 'light';
        this.selectedDoctors = new Set();
        this.allData = {
            doctors: [],
            labs: [],
            pharmacies: [],
            subscriptions: []
        };
        this.currentFilter = 'all';
        this.sessionTimer = null;
        
        this.init();
    }

    async init() {
        // Apply saved theme
        this.applyTheme(this.theme);
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Check if already authenticated
        if (window.pywebview && window.pywebview.api) {
            await this.checkAuthentication();
        } else {
            // For development/testing without pywebview
            console.warn('PyWebView API not available - running in development mode');
        }
    }

    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Theme toggle
        document.getElementById('theme-toggle')?.addEventListener('click', () => this.toggleTheme());

        // Navigation tabs
        document.querySelectorAll('.tab-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(link.dataset.tab);
            });
        });

        // Toolbar buttons
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.refreshData());
        document.getElementById('new-doctor-btn')?.addEventListener('click', () => this.showNewDoctorModal());
        document.getElementById('export-btn')?.addEventListener('click', () => this.exportCurrentView());

        // Search functionality
        document.getElementById('global-search')?.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                this.performGlobalSearch(e.target.value);
            }
        });

        // Doctors tab controls
        document.getElementById('select-all-doctors')?.addEventListener('change', (e) => {
            this.toggleAllDoctorSelections(e.target.checked);
        });

        document.getElementById('bulk-actions-btn')?.addEventListener('click', () => {
            this.showBulkActionsMenu();
        });

        document.getElementById('doctors-search-btn')?.addEventListener('click', () => {
            this.filterDoctors();
        });

        document.getElementById('doctors-clear-btn')?.addEventListener('click', () => {
            document.getElementById('doctors-search').value = '';
            this.filterDoctors();
        });

        // Subscription filters
        document.getElementById('filter-all')?.addEventListener('click', () => this.filterSubscriptions('all'));
        document.getElementById('filter-active')?.addEventListener('click', () => this.filterSubscriptions('active'));
        document.getElementById('filter-expiring')?.addEventListener('click', () => this.filterSubscriptions('warning'));
        document.getElementById('filter-expired')?.addEventListener('click', () => this.filterSubscriptions('expired'));

        // Settings
        document.getElementById('change-password-btn')?.addEventListener('click', () => this.showChangePasswordModal());
        document.getElementById('export-all-btn')?.addEventListener('click', () => this.exportAllData());

        // User menu
        document.getElementById('user-menu-btn')?.addEventListener('click', () => this.showUserMenu());

        // Context menu
        document.addEventListener('click', () => this.hideContextMenu());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    handleKeyboardShortcuts(e) {
        if (e.ctrlKey) {
            switch(e.key) {
                case 'f':
                case 'F':
                    e.preventDefault();
                    document.getElementById('global-search')?.focus();
                    break;
                case 'n':
                case 'N':
                    e.preventDefault();
                    this.showNewDoctorModal();
                    break;
                case 'r':
                case 'R':
                    e.preventDefault();
                    this.refreshData();
                    break;
                case 'e':
                case 'E':
                    e.preventDefault();
                    this.exportCurrentView();
                    break;
            }
        } else if (e.key === 'F5') {
            e.preventDefault();
            this.refreshData();
        }
    }

    // Theme Management
    applyTheme(theme) {
        const body = document.getElementById('app-body');
        if (theme === 'dark') {
            body.classList.remove('bg-blue-50', 'text-slate-800');
            body.classList.add('dark', 'bg-slate-900', 'text-slate-300');
            document.getElementById('theme-icon').textContent = 'light_mode';
            document.getElementById('theme-text').textContent = 'Light Theme';
        } else {
            body.classList.add('bg-blue-50', 'text-slate-800');
            body.classList.remove('dark', 'bg-slate-900', 'text-slate-300');
            document.getElementById('theme-icon').textContent = 'dark_mode';
            document.getElementById('theme-text').textContent = 'Dark Theme';
        }
        
        // Save theme preference
        localStorage.setItem('theme', theme);
        this.theme = theme;
        
        // Notify backend
        if (window.pywebview?.api) {
            window.pywebview.api.set_theme(theme);
        }
    }

    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    // Authentication
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const loginBtn = document.getElementById('login-btn');
        const loginError = document.getElementById('login-error');
        
        if (!username || !password) {
            loginError.textContent = 'Please enter username and password';
            loginError.classList.remove('hidden');
            return;
        }
        
        loginBtn.disabled = true;
        loginBtn.textContent = 'Authenticating...';
        loginError.classList.add('hidden');
        
        try {
            const result = await this.callAPI('login', username, password);
            
            if (result.success) {
                document.getElementById('login-screen').classList.add('hidden');
                document.getElementById('main-app').classList.remove('hidden');
                document.getElementById('user-name').textContent = result.username;
                
                if (result.requirePasswordChange) {
                    this.showChangePasswordModal(true);
                } else {
                    this.loadInitialData();
                }
                
                // Start session timer
                this.startSessionTimer();
            } else {
                loginError.textContent = result.error || 'Invalid credentials';
                loginError.classList.remove('hidden');
            }
        } catch (error) {
            loginError.textContent = 'Login failed: ' + error.message;
            loginError.classList.remove('hidden');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    }

    async checkAuthentication() {
        // In a real app, you might check if there's a valid session
        // For now, we'll just show the login screen
        document.getElementById('login-screen').classList.remove('hidden');
    }

    startSessionTimer() {
        // Update session timer every minute
        this.sessionTimer = setInterval(async () => {
            const result = await this.callAPI('check_session');
            if (result.valid) {
                document.getElementById('session-timer').textContent = `Session: ${result.remainingMinutes} min`;
            } else {
                clearInterval(this.sessionTimer);
                this.showMessage('Session expired. Please log in again.', 'error');
                this.logout();
            }
        }, 60000);
        
        // Initial update
        this.callAPI('check_session').then(result => {
            if (result.valid) {
                document.getElementById('session-timer').textContent = `Session: ${result.remainingMinutes} min`;
            }
        });
    }

    async logout() {
        await this.callAPI('logout');
        clearInterval(this.sessionTimer);
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    }

    // Tab Management
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-link').forEach(link => {
            if (link.dataset.tab === tabName) {
                link.classList.remove('text-slate-500', 'dark:text-slate-400');
                link.classList.add('text-blue-600', 'border-b-2', 'border-blue-600', 'dark:text-sky-400', 'dark:border-sky-400');
            } else {
                link.classList.add('text-slate-500', 'dark:text-slate-400');
                link.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600', 'dark:text-sky-400', 'dark:border-sky-400');
            }
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const tabContent = document.getElementById(`${tabName}-tab`);
        if (tabContent) {
            tabContent.classList.add('active');
        }
        
        this.currentTab = tabName;
        
        // Load data if needed
        if (!this.allData[tabName] || this.allData[tabName].length === 0) {
            this.loadTabData(tabName);
        }
    }

    // Data Loading
    async loadInitialData() {
        this.showLoading('Loading data...');
        
        try {
            await Promise.all([
                this.loadDoctors(),
                this.loadDashboardStats()
            ]);
            
            this.hideLoading();
        } catch (error) {
            this.hideLoading();
            this.showMessage('Failed to load data: ' + error.message, 'error');
        }
    }

    async loadTabData(tabName) {
        switch(tabName) {
            case 'doctors':
                await this.loadDoctors();
                break;
            case 'laboratories':
                await this.loadLabs();
                break;
            case 'pharmacies':
                await this.loadPharmacies();
                break;
            case 'subscriptions':
                await this.loadSubscriptions();
                break;
            case 'dashboard':
                await this.loadDashboardStats();
                break;
        }
    }

    async loadDoctors() {
        const result = await this.callAPI('get_doctors');
        if (result.success) {
            this.allData.doctors = result.data;
            this.renderDoctorsTable(result.data);
            this.updateRecordCount(result.data.length);
        }
    }

    async loadLabs() {
        const result = await this.callAPI('get_labs');
        if (result.success) {
            this.allData.labs = result.data;
            this.renderLabsTable(result.data);
        }
    }

    async loadPharmacies() {
        const result = await this.callAPI('get_pharmacies');
        if (result.success) {
            this.allData.pharmacies = result.data;
            this.renderPharmaciesTable(result.data);
        }
    }

    async loadSubscriptions() {
        const result = await this.callAPI('get_subscriptions');
        if (result.success) {
            this.allData.subscriptions = result.data;
            this.renderSubscriptionsTable(result.data);
        }
    }

    async loadDashboardStats() {
        const result = await this.callAPI('get_dashboard_stats');
        if (result.success) {
            document.getElementById('total-doctors').textContent = result.stats.totalDoctors;
            document.getElementById('active-subscriptions').textContent = result.stats.activeSubscriptions;
            document.getElementById('expiring-soon').textContent = result.stats.expiringSoon;
            document.getElementById('expired-subscriptions').textContent = result.stats.expired;
            
            // Add activity log entry
            this.addActivityLog(`Data refreshed at ${new Date().toLocaleTimeString()}`);
        }
    }

    // Table Rendering
    renderDoctorsTable(doctors) {
        const tbody = document.getElementById('doctors-table-body');
        tbody.innerHTML = '';
        
        doctors.forEach(doctor => {
            const row = document.createElement('tr');
            row.dataset.doctorId = doctor.id;
            
            // Add context menu listener
            row.addEventListener('contextmenu', (e) => this.showContextMenu(e, doctor));
            
            row.innerHTML = `
                <td>
                    <input type="checkbox" class="doctor-checkbox checkbox" data-id="${doctor.id}">
                </td>
                <td>
                    <span class="id-display">${this.truncateId(doctor.id)}</span>
                </td>
                <td class="font-weight-medium">${doctor.name}</td>
                <td>${this.truncateEmail(doctor.email)}</td>
                <td>${this.renderStatusBadge(doctor.status)}</td>
                <td>${doctor.specialty || ''}</td>
                <td>${doctor.phone || ''}</td>
                <td>${this.renderAccountStatus(doctor.pharmacyStatus)}</td>
                <td>${doctor.labStatus === 'not_assigned' ? 'Not assigned' : this.renderAccountStatus(doctor.labStatus)}</td>
                <td>
                    <div style="font-size: 12px;">
                        ${this.formatSubscriptionDates(doctor.subscriptionStart, doctor.subscriptionEnd)}
                    </div>
                </td>
                <td class="font-mono">${doctor.daysLeft ?? 'N/A'}</td>
            `;
            
            tbody.appendChild(row);
            
            // Add checkbox listener
            row.querySelector('.doctor-checkbox').addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedDoctors.add(doctor.id);
                } else {
                    this.selectedDoctors.delete(doctor.id);
                }
            });
        });
    }
    
    renderLabsTable(labs) {
        const tbody = document.getElementById('labs-table-body');
        tbody.innerHTML = '';
        
        labs.forEach(lab => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>
                    <span class="id-display">${this.truncateId(lab.id)}</span>
                </td>
                <td class="font-weight-medium">${lab.name}</td>
                <td>
                    <span class="id-display">${this.truncateId(lab.doctorId)}</span>
                </td>
                <td>${lab.doctorName}</td>
                <td>${this.renderStatusBadge(lab.status)}</td>
                <td>
                    <span class="font-mono" style="background: rgba(56, 189, 248, 0.1); padding: 4px 8px; border-radius: 4px; color: #38bdf8;">
                        ${lab.accessCode}
                    </span>
                </td>
                <td>${this.formatDate(lab.createdAt)}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    renderPharmaciesTable(pharmacies) {
        const tbody = document.getElementById('pharmacies-table-body');
        tbody.innerHTML = '';
        
        pharmacies.forEach(pharmacy => {
            const row = document.createElement('tr');
            row.className = 'border-b border-blue-200 hover:bg-blue-50 dark:border-slate-700 dark:hover:bg-slate-700/50';
            
            row.innerHTML = `
                <td class="px-4 py-3 text-slate-600 dark:text-slate-500">${this.truncateId(pharmacy.id)}</td>
                <td class="px-4 py-3">${pharmacy.name}</td>
                <td class="px-4 py-3 text-slate-600 dark:text-slate-500">${this.truncateId(pharmacy.doctorId)}</td>
                <td class="px-4 py-3">${pharmacy.doctorName}</td>
                <td class="px-4 py-3">${this.renderStatusBadge(pharmacy.status)}</td>
                <td class="px-4 py-3 font-mono">${pharmacy.accessCode}</td>
                <td class="px-4 py-3">${this.formatDate(pharmacy.createdAt)}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    renderSubscriptionsTable(subscriptions) {
        const tbody = document.getElementById('subscriptions-table-body');
        tbody.innerHTML = '';
        
        const filteredSubs = this.currentFilter === 'all' 
            ? subscriptions 
            : subscriptions.filter(s => s.status === this.currentFilter);
        
        filteredSubs.forEach(sub => {
            const row = document.createElement('tr');
            row.className = 'border-b border-blue-200 hover:bg-blue-50 dark:border-slate-700 dark:hover:bg-slate-700/50';
            
            row.innerHTML = `
                <td class="px-4 py-3 text-slate-600 dark:text-slate-500">${this.truncateId(sub.id)}</td>
                <td class="px-4 py-3">${sub.name}</td>
                <td class="px-4 py-3">${sub.email}</td>
                <td class="px-4 py-3">${this.formatDate(sub.startDate)}</td>
                <td class="px-4 py-3">${this.formatDate(sub.endDate)}</td>
                <td class="px-4 py-3">${sub.daysLeft ?? 'N/A'}</td>
                <td class="px-4 py-3">${this.renderStatusBadge(sub.status)}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    // Helper Methods
    renderStatusBadge(status) {
        const colors = {
            active: 'bg-green-200 text-green-800 dark:bg-green-700 dark:text-green-300',
            inactive: 'bg-red-200 text-red-800 dark:bg-red-700 dark:text-red-300',
            warning: 'bg-yellow-200 text-yellow-800 dark:bg-yellow-700 dark:text-yellow-300',
            expired: 'bg-red-200 text-red-800 dark:bg-red-700 dark:text-red-300'
        };
        
        const color = colors[status] || 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
        return `<span class="${color} text-xs font-semibold px-2.5 py-0.5 rounded-full">${status.charAt(0).toUpperCase() + status.slice(1)}</span>`;
    }

    renderAccountStatus(status) {
        if (status === 'active') {
            return '<span class="text-green-600 dark:text-green-400"><span class="material-icons text-base">check</span> Active</span>';
        } else {
            return '<span class="text-slate-500"><span class="material-icons text-base">close</span> Inactive</span>';
        }
    }

    truncateId(id) {
        return id ? id.substring(0, 12) + '...' : '';
    }

    truncateEmail(email) {
        if (!email) return '';
        if (email.length <= 20) return email;
        return email.substring(0, 17) + '...';
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString();
    }

    formatSubscriptionDates(start, end) {
        if (!start || !end) return 'Not set';
        return `${this.formatDate(start)} to ${this.formatDate(end)}`;
    }

    updateRecordCount(count) {
        document.getElementById('record-count').textContent = `${count} records`;
    }

    addActivityLog(message) {
        const activityLog = document.getElementById('activity-log');
        const entry = document.createElement('div');
        entry.className = 'flex items-center gap-2';
        entry.innerHTML = `
            <span class="material-icons text-base text-blue-500">info</span>
            <span>${message}</span>
        `;
        
        // Add to beginning and limit to 10 entries
        activityLog.insertBefore(entry, activityLog.firstChild);
        while (activityLog.children.length > 10) {
            activityLog.removeChild(activityLog.lastChild);
        }
    }

    // UI Actions
    async refreshData() {
        this.showLoading('Refreshing data...');
        
        try {
            await this.loadTabData(this.currentTab);
            if (this.currentTab === 'doctors') {
                await this.loadDashboardStats();
            }
            this.hideLoading();
            this.showMessage('Data refreshed successfully', 'success');
        } catch (error) {
            this.hideLoading();
            this.showMessage('Failed to refresh data', 'error');
        }
    }

    filterDoctors() {
        const searchText = document.getElementById('doctors-search').value.toLowerCase();
        const searchField = document.getElementById('doctors-search-field').value;
        
        if (!searchText) {
            this.renderDoctorsTable(this.allData.doctors);
            return;
        }
        
        const filtered = this.allData.doctors.filter(doctor => {
            if (searchField === 'All Fields') {
                return Object.values(doctor).some(val => 
                    String(val).toLowerCase().includes(searchText)
                );
            } else {
                const fieldMap = {
                    'Name': 'name',
                    'Email': 'email',
                    'ID': 'id',
                    'Specialty': 'specialty'
                };
                const field = fieldMap[searchField];
                return doctor[field]?.toLowerCase().includes(searchText);
            }
        });
        
        this.renderDoctorsTable(filtered);
    }

    filterSubscriptions(status) {
        this.currentFilter = status;
        
        // Update button styles
        ['all', 'active', 'expiring', 'expired'].forEach(filter => {
            const btn = document.getElementById(`filter-${filter}`);
            if (filter === status || (filter === 'expiring' && status === 'warning')) {
                btn.className = 'px-4 py-2 bg-blue-600 text-white rounded-md text-sm';
            } else {
                btn.className = 'px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600';
            }
        });
        
        this.renderSubscriptionsTable(this.allData.subscriptions);
    }

    toggleAllDoctorSelections(checked) {
        document.querySelectorAll('.doctor-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
            const doctorId = checkbox.dataset.id;
            if (checked) {
                this.selectedDoctors.add(doctorId);
            } else {
                this.selectedDoctors.delete(doctorId);
            }
        });
    }

    performGlobalSearch(searchText) {
        // Implement global search across all tabs
        if (this.currentTab === 'doctors') {
            document.getElementById('doctors-search').value = searchText;
            this.filterDoctors();
        }
        // Add similar logic for other tabs
    }

    // Context Menu
    showContextMenu(e, doctor) {
        e.preventDefault();
        
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = `${e.pageX}px`;
        menu.style.top = `${e.pageY}px`;
        
        // Store current doctor data
        menu.dataset.doctorId = doctor.id;
        
        // Add click handlers
        menu.querySelectorAll('.context-menu-item').forEach(item => {
            item.onclick = () => {
                this.handleContextMenuAction(item.dataset.action, doctor);
                this.hideContextMenu();
            };
        });
    }

    hideContextMenu() {
        document.getElementById('context-menu').style.display = 'none';
    }

    async handleContextMenuAction(action, doctor) {
        switch(action) {
            case 'view':
                this.showDoctorDetails(doctor);
                break;
            case 'edit':
                this.showEditDoctorModal(doctor);
                break;
            case 'reset-password':
                await this.resetDoctorPassword(doctor);
                break;
            case 'toggle-status':
                await this.toggleDoctorStatus(doctor);
                break;
            case 'export':
                await this.exportDoctors([doctor.id]);
                break;
        }
    }

    // Modals
    showModal(title, content, buttons = []) {
        const modalContainer = document.getElementById('modal-container');
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden dark:bg-slate-800">
                <div class="px-6 py-4 border-b border-gray-200 dark:border-slate-700">
                    <h2 class="text-xl font-semibold">${title}</h2>
                </div>
                <div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
                    ${content}
                </div>
                <div class="px-6 py-4 border-t border-gray-200 dark:border-slate-700 flex justify-end gap-3">
                    ${buttons.map(btn => `
                        <button class="${btn.class}" data-action="${btn.action}">
                            ${btn.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Add event listeners to buttons
        modal.querySelectorAll('button[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                if (action === 'close') {
                    modal.remove();
                } else if (buttons.find(b => b.action === action)?.handler) {
                    buttons.find(b => b.action === action).handler(modal);
                }
            });
        });
        
        modalContainer.appendChild(modal);
        return modal;
    }

    showNewDoctorModal() {
        const content = `
            <form id="new-doctor-form" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">First Name *</label>
                        <input type="text" name="first_name" required class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Last Name *</label>
                        <input type="text" name="last_name" required class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Email *</label>
                    <input type="email" name="email" required class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Specialty</label>
                    <input type="text" name="speciality" class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Phone</label>
                    <input type="tel" name="phone_number" class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Address</label>
                    <input type="text" name="address" class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="flex items-center">
                        <input type="checkbox" name="create_lab_account" checked class="mr-2">
                        <span class="text-sm">Create Lab Account</span>
                    </label>
                </div>
            </form>
        `;
        
        const modal = this.showModal('Create New Doctor', content, [
            {
                text: 'Cancel',
                class: 'px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300',
                action: 'close'
            },
            {
                text: 'Create',
                class: 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
                action: 'create',
                handler: async (modal) => {
                    const form = modal.querySelector('#new-doctor-form');
                    const formData = new FormData(form);
                    const data = {};
                    
                    for (const [key, value] of formData) {
                        if (key === 'create_lab_account') {
                            data[key] = form.querySelector(`[name="${key}"]`).checked;
                        } else {
                            data[key] = value;
                        }
                    }
                    
                    try {
                        this.showLoading('Creating doctor account...');
                        const result = await this.callAPI('create_doctor', data);
                        
                        if (result.success) {
                            this.hideLoading();
                            modal.remove();
                            this.showCredentialsModal(result.data);
                            await this.refreshData();
                        } else {
                            this.hideLoading();
                            this.showMessage(result.error || 'Failed to create doctor', 'error');
                        }
                    } catch (error) {
                        this.hideLoading();
                        this.showMessage('Error: ' + error.message, 'error');
                    }
                }
            }
        ]);
    }

    showCredentialsModal(credentials) {
        const content = `
            <div class="space-y-4">
                <div class="bg-green-100 text-green-800 p-4 rounded-md">
                    <p class="font-semibold mb-2">Doctor account created successfully!</p>
                    <p class="text-sm">Please save these credentials securely.</p>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-md space-y-3">
                    <h3 class="font-semibold">Doctor Credentials</h3>
                    <div>
                        <p class="text-sm text-gray-600">Email:</p>
                        <p class="font-mono">${credentials.email}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Password:</p>
                        <p class="font-mono bg-white px-2 py-1 rounded">${credentials.password}</p>
                    </div>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-md space-y-3">
                    <h3 class="font-semibold">Pharmacy Account</h3>
                    <div>
                        <p class="text-sm text-gray-600">Access Code:</p>
                        <p class="font-mono bg-white px-2 py-1 rounded">${credentials.pharmacyCode}</p>
                    </div>
                </div>
                
                ${credentials.labCode ? `
                <div class="bg-gray-50 p-4 rounded-md space-y-3">
                    <h3 class="font-semibold">Laboratory Account</h3>
                    <div>
                        <p class="text-sm text-gray-600">Access Code:</p>
                        <p class="font-mono bg-white px-2 py-1 rounded">${credentials.labCode}</p>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        
        this.showModal('Account Created', content, [
            {
                text: 'Close',
                class: 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
                action: 'close'
            }
        ]);
    }

    showDoctorDetails(doctor) {
        const content = `
            <div class="space-y-4">
                <h3 class="text-lg font-semibold">${doctor.name}</h3>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-sm text-gray-600 dark:text-slate-400">ID</p>
                        <p class="font-mono text-sm">${doctor.id}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600 dark:text-slate-400">Email</p>
                        <p>${doctor.email}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600 dark:text-slate-400">Status</p>
                        <p>${this.renderStatusBadge(doctor.status)}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600 dark:text-slate-400">Specialty</p>
                        <p>${doctor.specialty || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600 dark:text-slate-400">Phone</p>
                        <p>${doctor.phone || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600 dark:text-slate-400">Days Left</p>
                        <p>${doctor.daysLeft ?? 'N/A'}</p>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-2">Subscription</h4>
                    <div class="bg-gray-50 dark:bg-slate-700 p-3 rounded-md">
                        <p class="text-sm">Start: ${this.formatDate(doctor.subscriptionStart) || 'Not set'}</p>
                        <p class="text-sm">End: ${this.formatDate(doctor.subscriptionEnd) || 'Not set'}</p>
                        <p class="text-sm">Status: ${this.renderStatusBadge(doctor.subscriptionStatus || 'unknown')}</p>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-2">Associated Accounts</h4>
                    <div class="space-y-2">
                        <p class="text-sm">Pharmacy: ${this.renderAccountStatus(doctor.pharmacyStatus)}</p>
                        <p class="text-sm">Laboratory: ${doctor.labStatus === 'not_assigned' ? 'Not assigned' : this.renderAccountStatus(doctor.labStatus)}</p>
                    </div>
                </div>
            </div>
        `;
        
        this.showModal('Doctor Details', content, [
            {
                text: 'Close',
                class: 'px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300',
                action: 'close'
            }
        ]);
    }

    showChangePasswordModal(required = false) {
        const content = `
            <form id="change-password-form" class="space-y-4">
                ${required ? `
                <div class="bg-yellow-100 text-yellow-800 p-4 rounded-md mb-4">
                    <p class="font-semibold">Password change required</p>
                    <p class="text-sm mt-1">You must change your password before continuing.</p>
                </div>
                ` : ''}
                
                <div>
                    <label class="block text-sm font-medium mb-1">Current Password</label>
                    <input type="password" name="old_password" required class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">New Password</label>
                    <input type="password" name="new_password" required class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Confirm New Password</label>
                    <input type="password" name="confirm_password" required class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                </div>
                
                <div class="text-sm text-gray-600 dark:text-slate-400">
                    <p class="font-medium mb-1">Password must contain:</p>
                    <ul class="list-disc list-inside space-y-1">
                        <li>At least 12 characters</li>
                        <li>Uppercase and lowercase letters</li>
                        <li>Numbers</li>
                        <li>Special characters (!@#$%^&*)</li>
                    </ul>
                </div>
            </form>
        `;
        
        const modal = this.showModal('Change Password', content, [
            {
                text: required ? 'Cancel' : 'Close',
                class: 'px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300',
                action: required ? 'logout' : 'close',
                handler: required ? () => this.logout() : undefined
            },
            {
                text: 'Change Password',
                class: 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
                action: 'change',
                handler: async (modal) => {
                    const form = modal.querySelector('#change-password-form');
                    const oldPassword = form.querySelector('[name="old_password"]').value;
                    const newPassword = form.querySelector('[name="new_password"]').value;
                    const confirmPassword = form.querySelector('[name="confirm_password"]').value;
                    
                    if (newPassword !== confirmPassword) {
                        this.showMessage('Passwords do not match', 'error');
                        return;
                    }
                    
                    try {
                        const result = await this.callAPI('change_password', oldPassword, newPassword);
                        if (result.success) {
                            modal.remove();
                            this.showMessage('Password changed successfully', 'success');
                            if (required) {
                                this.loadInitialData();
                            }
                        } else {
                            this.showMessage(result.error || 'Failed to change password', 'error');
                        }
                    } catch (error) {
                        this.showMessage('Error: ' + error.message, 'error');
                    }
                }
            }
        ]);
    }

    async resetDoctorPassword(doctor) {
        const confirmed = confirm(`Reset password for ${doctor.name}?`);
        if (!confirmed) return;
        
        try {
            this.showLoading('Resetting password...');
            const result = await this.callAPI('reset_doctor_password', doctor.id);
            
            if (result.success) {
                this.hideLoading();
                this.showPasswordResetModal(doctor.name, result.password);
            } else {
                this.hideLoading();
                this.showMessage('Failed to reset password', 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showMessage('Error: ' + error.message, 'error');
        }
    }

    showPasswordResetModal(doctorName, newPassword) {
        const content = `
            <div class="space-y-4">
                <div class="bg-green-100 text-green-800 p-4 rounded-md">
                    <p class="font-semibold">Password reset successfully!</p>
                    <p class="text-sm mt-1">The password for ${doctorName} has been reset.</p>
                </div>
                
                <div class="bg-gray-50 dark:bg-slate-700 p-4 rounded-md">
                    <p class="text-sm text-gray-600 dark:text-slate-400 mb-1">New Password:</p>
                    <p class="font-mono text-lg bg-white dark:bg-slate-800 px-3 py-2 rounded">${newPassword}</p>
                </div>
                
                <div class="text-sm text-gray-600 dark:text-slate-400">
                    <p>Please save this password securely and provide it to the doctor.</p>
                    <p>They will be required to change it on first login.</p>
                </div>
            </div>
        `;
        
        this.showModal('Password Reset', content, [
            {
                text: 'Close',
                class: 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700',
                action: 'close'
            }
        ]);
    }

    // Export functionality
    async exportCurrentView() {
        switch(this.currentTab) {
            case 'doctors':
                await this.exportDoctors();
                break;
            case 'laboratories':
                await this.exportData('labs');
                break;
            case 'pharmacies':
                await this.exportData('pharmacies');
                break;
            case 'subscriptions':
                await this.exportData('subscriptions');
                break;
            default:
                this.showMessage('Cannot export this view', 'info');
        }
    }

    async exportDoctors(ids = null) {
        try {
            const result = await this.callAPI('export_data', 'doctors', ids);
            if (result.success) {
                this.downloadFile(result.data, result.filename);
            } else {
                this.showMessage('Export failed', 'error');
            }
        } catch (error) {
            this.showMessage('Export error: ' + error.message, 'error');
        }
    }

    async exportData(type) {
        try {
            const result = await this.callAPI('export_data', type);
            if (result.success) {
                this.downloadFile(result.data, result.filename);
            } else {
                this.showMessage('Export failed', 'error');
            }
        } catch (error) {
            this.showMessage('Export error: ' + error.message, 'error');
        }
    }

    downloadFile(base64Data, filename) {
        const link = document.createElement('a');
        link.href = `data:text/csv;base64,${base64Data}`;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        this.showMessage('Export completed', 'success');
    }

    // Utility Methods
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        loadingText.textContent = message;
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showMessage(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
            warning: 'bg-yellow-500'
        };
        
        toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2`;
        toast.innerHTML = `
            <span class="material-icons text-lg">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</span>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    showUserMenu() {
        // Create dropdown menu
        const menu = document.createElement('div');
        menu.className = 'absolute right-6 top-14 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50 dark:bg-slate-800 dark:border-slate-700';
        menu.innerHTML = `
            <a href="#" class="block px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-slate-700" onclick="app.showChangePasswordModal(); return false;">
                <span class="material-icons text-base mr-2">lock</span>
                Change Password
            </a>
            <hr class="my-1 border-gray-200 dark:border-slate-700">
            <a href="#" class="block px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-slate-700" onclick="app.logout(); return false;">
                <span class="material-icons text-base mr-2">logout</span>
                Sign Out
            </a>
        `;
        
        document.body.appendChild(menu);
        
        // Remove menu when clicking outside
        setTimeout(() => {
            document.addEventListener('click', function removeMenu() {
                menu.remove();
                document.removeEventListener('click', removeMenu);
            }, { once: true });
        }, 10);
    }

    // API Communication
    async callAPI(method, ...args) {
        if (window.pywebview && window.pywebview.api) {
            try {
                return await window.pywebview.api[method](...args);
            } catch (error) {
                console.error(`API call failed: ${method}`, error);
                throw error;
            }
        } else {
            // Mock API for development
            console.warn(`Mock API call: ${method}`, args);
            return this.mockAPI(method, ...args);
        }
    }

    // Mock API for development
    mockAPI(method, ...args) {
        // Implement mock responses for testing
        switch(method) {
            case 'login':
                return { success: true, username: args[0], requirePasswordChange: false };
            case 'get_doctors':
                return {
                    success: true,
                    data: [
                        {
                            id: '123e4567-e89b-12d3-a456-426614174000',
                            name: 'Dr. John Smith',
                            email: 'john.smith@example.com',
                            status: 'active',
                            specialty: 'Cardiology',
                            phone: '555-0123',
                            pharmacyStatus: 'active',
                            labStatus: 'active',
                            subscriptionStart: '2024-01-01',
                            subscriptionEnd: '2025-01-01',
                            daysLeft: 200,
                            subscriptionStatus: 'active'
                        }
                    ]
                };
            case 'get_dashboard_stats':
                return {
                    success: true,
                    stats: {
                        totalDoctors: 10,
                        activeSubscriptions: 8,
                        expiringSoon: 2,
                        expired: 0
                    }
                };
            default:
                return { success: true };
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new MedicalPracticeApp();
});