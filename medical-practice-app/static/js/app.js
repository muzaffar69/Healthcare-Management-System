// Medical Practice Management - Complete JavaScript Application
// Dark Theme Compatible Version

class MedicalPracticeApp {
    constructor() {
        this.currentTab = 'doctors';
        this.theme = 'dark'; // Default to dark theme
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
        console.log('🚀 Initializing Medical Practice Management App...');
        
        // Force dark theme on startup
        this.applyTheme(this.theme);
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize with sample data
        this.loadSampleData();
        
        // Check authentication
        if (window.pywebview && window.pywebview.api) {
            await this.checkAuthentication();
        } else {
            console.warn('⚠️ PyWebView API not available - running in development mode');
            // Auto-show login for demo
            this.showLoginScreen();
        }
    }

    setupEventListeners() {
        console.log('🔧 Setting up event listeners...');
        
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
        document.getElementById('select-all-btn')?.addEventListener('click', () => {
            this.toggleAllDoctorSelections();
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

        // Settings
        document.getElementById('change-password-btn')?.addEventListener('click', () => {
            this.showMessage('Change password feature - Coming soon', 'info');
        });

        document.getElementById('export-all-btn')?.addEventListener('click', () => {
            this.showMessage('Export all data feature - Coming soon', 'info');
        });

        // User menu
        document.getElementById('user-menu-btn')?.addEventListener('click', () => this.showUserMenu());

        // Context menu
        document.addEventListener('click', () => this.hideContextMenu());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        console.log('✅ Event listeners set up successfully');
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
        console.log('🎨 Applying theme:', theme);
        const body = document.body;
        
        if (theme === 'light') {
            // Light theme
            body.classList.remove('bg-slate-900', 'text-slate-300');
            body.classList.add('bg-blue-50', 'text-slate-800');
            if (document.getElementById('theme-icon')) {
                document.getElementById('theme-icon').textContent = 'dark_mode';
                document.getElementById('theme-text').textContent = 'Dark Theme';
            }
        } else {
            // Dark theme (default)
            body.classList.add('bg-slate-900', 'text-slate-300');
            body.classList.remove('bg-blue-50', 'text-slate-800');
            if (document.getElementById('theme-icon')) {
                document.getElementById('theme-icon').textContent = 'light_mode';
                document.getElementById('theme-text').textContent = 'Light Theme';
            }
        }
        
        this.theme = theme;
        
        // Notify backend if available
        if (window.pywebview?.api) {
            window.pywebview.api.set_theme(theme);
        }
    }

    toggleTheme() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.showMessage(`Switched to ${newTheme} theme`, 'success');
    }

    // Authentication
    showLoginScreen() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
    }

    async handleLogin(e) {
        e.preventDefault();
        console.log('🔐 Handling login...');
        
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
            let result;
            if (window.pywebview?.api) {
                result = await this.callAPI('login', username, password);
            } else {
                // Demo mode
                await new Promise(resolve => setTimeout(resolve, 1000));
                result = { success: username === 'admin' && password === 'admin', username: username };
            }
            
            if (result.success) {
                document.getElementById('login-screen').classList.add('hidden');
                document.getElementById('main-app').classList.remove('hidden');
                document.getElementById('user-name').textContent = result.username || username;
                
                if (result.requirePasswordChange) {
                    this.showMessage('Password change required on first login', 'warning');
                } else {
                    this.loadInitialData();
                }
                
                this.startSessionTimer();
                this.showMessage('Welcome to Medical Practice Management!', 'success');
            } else {
                loginError.textContent = result.error || 'Invalid credentials. Try admin/admin for demo';
                loginError.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Login error:', error);
            loginError.textContent = 'Login failed: ' + error.message;
            loginError.classList.remove('hidden');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    }

    async checkAuthentication() {
        console.log('🔍 Checking authentication...');
        // In production, this would check for valid session
        // For now, show login screen
        this.showLoginScreen();
    }

    startSessionTimer() {
        // Update session timer every minute
        this.sessionTimer = setInterval(async () => {
            const result = await this.callAPI('check_session');
            if (result && result.valid) {
                document.getElementById('session-timer').textContent = `Session: ${result.remainingMinutes} min`;
            } else {
                clearInterval(this.sessionTimer);
                this.showMessage('Session expired. Please log in again.', 'warning');
                this.logout();
            }
        }, 60000);
        
        // Initial update
        this.callAPI('check_session').then(result => {
            if (result && result.valid) {
                document.getElementById('session-timer').textContent = `Session: ${result.remainingMinutes} min`;
            }
        }).catch(() => {
            // Ignore errors in demo mode
        });
    }

    async logout() {
        await this.callAPI('logout').catch(() => {});
        clearInterval(this.sessionTimer);
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        this.showMessage('Logged out successfully', 'info');
    }

    // Tab Management
    switchTab(tabName) {
        console.log('📋 Switching to tab:', tabName);
        
        // Update tab buttons
        document.querySelectorAll('.tab-link').forEach(link => {
            if (link.dataset.tab === tabName) {
                link.classList.remove('text-slate-400');
                link.classList.add('text-sky-400', 'border-b-2', 'border-sky-400');
            } else {
                link.classList.add('text-slate-400');
                link.classList.remove('text-sky-400', 'border-b-2', 'border-sky-400');
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
        this.loadTabData(tabName);
    }

    // Data Loading
    async loadInitialData() {
        console.log('📊 Loading initial data...');
        this.showLoading('Loading dashboard data...');
        
        try {
            await Promise.all([
                this.loadDoctors(),
                this.loadDashboardStats()
            ]);
            
            this.hideLoading();
            this.addActivityLog('Application data loaded successfully');
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
        try {
            const result = await this.callAPI('get_doctors');
            if (result && result.success) {
                this.allData.doctors = result.data;
                this.renderDoctorsTable(result.data);
                this.updateRecordCount(result.data.length);
            }
        } catch (error) {
            console.error('Failed to load doctors:', error);
            // Use sample data in demo mode
            this.renderDoctorsTable(this.allData.doctors);
        }
    }

    async loadLabs() {
        try {
            const result = await this.callAPI('get_labs');
            if (result && result.success) {
                this.allData.labs = result.data;
                // Render labs table when implemented
            }
        } catch (error) {
            console.error('Failed to load labs:', error);
        }
    }

    async loadPharmacies() {
        try {
            const result = await this.callAPI('get_pharmacies');
            if (result && result.success) {
                this.allData.pharmacies = result.data;
                // Render pharmacies table when implemented
            }
        } catch (error) {
            console.error('Failed to load pharmacies:', error);
        }
    }

    async loadSubscriptions() {
        try {
            const result = await this.callAPI('get_subscriptions');
            if (result && result.success) {
                this.allData.subscriptions = result.data;
                // Render subscriptions table when implemented
            }
        } catch (error) {
            console.error('Failed to load subscriptions:', error);
        }
    }

    async loadDashboardStats() {
        try {
            const result = await this.callAPI('get_dashboard_stats');
            if (result && result.success) {
                document.getElementById('total-doctors').textContent = result.stats.totalDoctors;
                document.getElementById('active-subscriptions').textContent = result.stats.activeSubscriptions;
                document.getElementById('expiring-soon').textContent = result.stats.expiringSoon;
                document.getElementById('expired-subscriptions').textContent = result.stats.expired;
                
                this.addActivityLog(`Dashboard updated: ${result.stats.totalDoctors} doctors total`);
            }
        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
            // Use sample data
            document.getElementById('total-doctors').textContent = '8';
            document.getElementById('active-subscriptions').textContent = '6';
            document.getElementById('expiring-soon').textContent = '2';
            document.getElementById('expired-subscriptions').textContent = '0';
        }
    }

    loadSampleData() {
        // Load sample data for demo
        this.allData.doctors = [
            {
                id: 'cd12efc0-7dc6-4b8e-9f2a-1234567890ab',
                name: 'Dr Test',
                email: 'test2@example.com',
                status: 'active',
                specialty: '',
                phone: '',
                pharmacyStatus: 'inactive',
                labStatus: 'not_assigned',
                subscriptionStart: '',
                subscriptionEnd: '',
                daysLeft: null,
                subscriptionStatus: 'unknown'
            },
            {
                id: '6e54d09b-281c-4f3e-8a1b-abcdef123456',
                name: 'Alawi The big',
                email: 'brokenshower@example.com',
                status: 'active',
                specialty: 'love <3',
                phone: '07769969696',
                pharmacyStatus: 'active',
                labStatus: 'active',
                subscriptionStart: '2025-05-26',
                subscriptionEnd: '2026-05-26',
                daysLeft: 362,
                subscriptionStatus: 'active'
            }
        ];
    }

    // Table Rendering
    renderDoctorsTable(doctors) {
        const tbody = document.getElementById('doctors-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        doctors.forEach(doctor => {
            const row = document.createElement('tr');
            row.className = 'border-b border-slate-700 hover:bg-slate-700/50 transition-colors duration-150 ease-in-out';
            row.dataset.doctorId = doctor.id;
            
            // Add context menu listener
            row.addEventListener('contextmenu', (e) => this.showContextMenu(e, doctor));
            
            row.innerHTML = `
                <td class="px-4 py-3 text-slate-500">${this.truncateId(doctor.id)}</td>
                <td class="px-4 py-3">${doctor.name}</td>
                <td class="px-4 py-3">${this.truncateEmail(doctor.email)}</td>
                <td class="px-4 py-3">${this.renderStatusBadge(doctor.status)}</td>
                <td class="px-4 py-3">${doctor.specialty || ''}</td>
                <td class="px-4 py-3">${doctor.phone || ''}</td>
                <td class="px-4 py-3">${this.renderAccountStatus(doctor.pharmacyStatus)}</td>
                <td class="px-4 py-3">${doctor.labStatus === 'not_assigned' ? 'Not assigned' : this.renderAccountStatus(doctor.labStatus)}</td>
                <td class="px-4 py-3">${this.formatSubscriptionInfo(doctor)}</td>
                <td class="px-4 py-3">${doctor.daysLeft ?? 'N/A'}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    // Helper Methods
    renderStatusBadge(status) {
        const badges = {
            active: 'bg-green-700 text-green-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full',
            inactive: 'bg-red-700 text-red-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full',
            warning: 'bg-yellow-700 text-yellow-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full',
            expired: 'bg-red-700 text-red-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full'
        };
        
        const badgeClass = badges[status] || 'bg-slate-700 text-slate-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full';
        return `<span class="${badgeClass}">${status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown'}</span>`;
    }

    renderAccountStatus(status) {
        if (status === 'active') {
            return '<span class="text-green-400"><span class="material-icons text-base">check</span> Active</span>';
        } else {
            return '<span class="text-slate-500"><span class="material-icons text-base">close</span> Inactive</span>';
        }
    }

    truncateId(id) {
        return id ? id.substring(0, 12) + '...' : '';
    }

    truncateEmail(email) {
        if (!email) return '';
        if (email.length <= 15) return email;
        return email.substring(0, 12) + '...';
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString();
    }

    formatSubscriptionInfo(doctor) {
        if (!doctor.subscriptionStart || !doctor.subscriptionEnd) {
            return 'Not Set';
        }
        
        const startDate = this.formatDate(doctor.subscriptionStart);
        const endDate = this.formatDate(doctor.subscriptionEnd);
        return `${startDate} to...`;
    }

    updateRecordCount(count) {
        const recordCountEl = document.getElementById('record-count');
        if (recordCountEl) {
            recordCountEl.textContent = `${count} records`;
        }
    }

    addActivityLog(message) {
        const activityLog = document.getElementById('activity-log');
        if (!activityLog) return;
        
        const entry = document.createElement('div');
        entry.className = 'flex items-center gap-2 text-sm text-slate-400';
        entry.innerHTML = `
            <span class="material-icons text-base text-sky-500">info</span>
            <span>${message} - ${new Date().toLocaleTimeString()}</span>
        `;
        
        // Add to beginning and limit to 10 entries
        activityLog.insertBefore(entry, activityLog.firstChild);
        while (activityLog.children.length > 10) {
            activityLog.removeChild(activityLog.lastChild);
        }
    }

    // UI Actions
    async refreshData() {
        console.log('🔄 Refreshing data...');
        this.showLoading('Refreshing data...');
        
        try {
            await this.loadTabData(this.currentTab);
            if (this.currentTab === 'doctors') {
                await this.loadDashboardStats();
            }
            this.hideLoading();
            this.showMessage('Data refreshed successfully', 'success');
            this.addActivityLog('Data refreshed by user');
        } catch (error) {
            this.hideLoading();
            this.showMessage('Failed to refresh data', 'error');
        }
    }

    filterDoctors() {
        const searchText = document.getElementById('doctors-search')?.value.toLowerCase() || '';
        const searchField = document.getElementById('doctors-search-field')?.value || 'All Fields';
        
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
        this.showMessage(`Found ${filtered.length} matching doctors`, 'info');
    }

    toggleAllDoctorSelections() {
        const allSelected = this.selectedDoctors.size === this.allData.doctors.length;
        
        if (allSelected) {
            this.selectedDoctors.clear();
            this.showMessage('All doctors deselected', 'info');
        } else {
            this.allData.doctors.forEach(doctor => {
                this.selectedDoctors.add(doctor.id);
            });
            this.showMessage('All doctors selected', 'success');
        }
    }

    performGlobalSearch(searchText) {
        console.log('🔍 Performing global search:', searchText);
        if (this.currentTab === 'doctors') {
            const searchInput = document.getElementById('doctors-search');
            if (searchInput) {
                searchInput.value = searchText;
                this.filterDoctors();
            }
        }
        this.showMessage(`Searching for: "${searchText}"`, 'info');
    }

    // Context Menu
    showContextMenu(e, doctor) {
        e.preventDefault();
        
        const menu = document.getElementById('context-menu');
        if (!menu) return;
        
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
        const menu = document.getElementById('context-menu');
        if (menu) {
            menu.style.display = 'none';
        }
    }

    async handleContextMenuAction(action, doctor) {
        switch(action) {
            case 'view':
                this.showMessage(`Viewing details for ${doctor.name}`, 'info');
                break;
            case 'edit':
                this.showMessage(`Edit mode for ${doctor.name} - Feature coming soon`, 'info');
                break;
            case 'reset-password':
                this.showMessage(`Password reset for ${doctor.name} - Feature coming soon`, 'info');
                break;
            case 'toggle-status':
                this.showMessage(`Status toggle for ${doctor.name} - Feature coming soon`, 'info');
                break;
            case 'export':
                this.showMessage(`Exporting data for ${doctor.name} - Feature coming soon`, 'info');
                break;
        }
    }

    // Modal and UI Methods
    showNewDoctorModal() {
        console.log('➕ Show new doctor modal');
        this.showMessage('New doctor creation - Feature coming soon', 'info');
    }

    exportCurrentView() {
        console.log('📤 Export current view');
        this.showMessage('Export functionality - Feature coming soon', 'info');
    }

    showBulkActionsMenu() {
        this.showMessage(`Bulk actions for ${this.selectedDoctors.size} selected doctors - Feature coming soon`, 'info');
    }

    showUserMenu() {
        const menu = document.createElement('div');
        menu.className = 'absolute right-6 top-14 bg-slate-800 rounded-lg shadow-lg border border-slate-700 py-2 z-50';
        menu.innerHTML = `
            <a href="#" class="block px-4 py-2 text-sm text-slate-300 hover:bg-slate-700" onclick="app.showMessage('Change password - Feature coming soon', 'info'); return false;">
                <span class="material-icons text-base mr-2">lock</span>
                Change Password
            </a>
            <hr class="my-1 border-slate-700">
            <a href="#" class="block px-4 py-2 text-sm text-slate-300 hover:bg-slate-700" onclick="app.logout(); return false;">
                <span class="material-icons text-base mr-2">logout</span>
                Sign Out
            </a>
        `;
        
        document.body.appendChild(menu);
        
        setTimeout(() => {
            document.addEventListener('click', function removeMenu() {
                menu.remove();
                document.removeEventListener('click', removeMenu);
            }, { once: true });
        }, 10);
    }

    // Utility Methods
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        if (overlay && loadingText) {
            loadingText.textContent = message;
            overlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    showMessage(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Create toast notification
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            info: 'bg-sky-600',
            warning: 'bg-yellow-600'
        };
        
        const icons = {
            success: 'check_circle',
            error: 'error',
            info: 'info',
            warning: 'warning'
        };
        
        toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2 transform translate-x-full opacity-0 transition-all duration-300`;
        toast.innerHTML = `
            <span class="material-icons text-lg">${icons[type]}</span>
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
        const delay = () => new Promise(resolve => setTimeout(resolve, 500));
        
        switch(method) {
            case 'login':
                return delay().then(() => ({ success: args[0] === 'admin' && args[1] === 'admin', username: args[0] }));
            case 'get_doctors':
                return delay().then(() => ({
                    success: true,
                    data: this.allData.doctors
                }));
            case 'get_dashboard_stats':
                return delay().then(() => ({
                    success: true,
                    stats: {
                        totalDoctors: this.allData.doctors.length,
                        activeSubscriptions: this.allData.doctors.filter(d => d.status === 'active').length,
                        expiringSoon: 1,
                        expired: 0
                    }
                }));
            case 'check_session':
                return Promise.resolve({ valid: true, remainingMinutes: 29 });
            default:
                return Promise.resolve({ success: true });
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 DOM loaded, initializing Medical Practice App...');
    window.app = new MedicalPracticeApp();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Application error:', e.error);
});

// Prevent context menu on production
if (window.pywebview) {
    document.addEventListener('contextmenu', (e) => {
        if (!e.target.closest('tr')) {
            e.preventDefault();
        }
    });
}