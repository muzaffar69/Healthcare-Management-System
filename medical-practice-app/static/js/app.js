// Medical Practice Management - Debug Version
// Added extensive debugging and error handling

console.log('🚀 JavaScript loading...');

class MedicalPracticeApp {
    constructor() {
        console.log('🔧 Initializing MedicalPracticeApp...');
        this.currentTab = 'doctors';
        this.theme = 'dark';
        this.selectedDoctors = new Set();
        this.allData = {
            doctors: [],
            labs: [],
            pharmacies: [],
            subscriptions: []
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Starting initialization...');
        
        try {
            // Force dark theme
            this.applyTheme(this.theme);
            
            // Set up event listeners with error handling
            this.setupEventListeners();
            
            // Load sample data
            this.loadSampleData();
            
            // Check for PyWebView API
            if (window.pywebview && window.pywebview.api) {
                console.log('✅ PyWebView API detected');
                await this.checkAuthentication();
            } else {
                console.warn('⚠️ PyWebView API not available - running in development mode');
                this.showLoginScreen();
            }
            
            console.log('✅ Initialization complete');
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.showMessage('Initialization failed: ' + error.message, 'error');
        }
    }

    setupEventListeners() {
        console.log('🔧 Setting up event listeners...');
        
        try {
            // Login form - with extensive debugging
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                console.log('✅ Login form found');
                loginForm.addEventListener('submit', (e) => {
                    console.log('🔐 Login form submitted');
                    this.handleLogin(e);
                });
            } else {
                console.error('❌ Login form not found');
            }

            // Navigation tabs
            document.querySelectorAll('.tab-link').forEach((link, index) => {
                console.log(`📋 Setting up tab ${index}: ${link.dataset.tab}`);
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('📋 Tab clicked:', link.dataset.tab);
                    this.switchTab(link.dataset.tab);
                });
            });

            // Toolbar buttons
            this.setupButton('refresh-btn', () => this.refreshData());
            this.setupButton('new-doctor-btn', () => this.showNewDoctorModal());
            this.setupButton('export-btn', () => this.exportCurrentView());

            console.log('✅ Event listeners set up successfully');
        } catch (error) {
            console.error('❌ Error setting up event listeners:', error);
        }
    }

    setupButton(id, handler) {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', handler);
            console.log(`✅ Button ${id} set up`);
        } else {
            console.warn(`⚠️ Button ${id} not found`);
        }
    }

    showLoginScreen() {
        console.log('🔐 Showing login screen...');
        try {
            const loginScreen = document.getElementById('login-screen');
            const mainApp = document.getElementById('main-app');
            
            if (loginScreen && mainApp) {
                loginScreen.classList.remove('hidden');
                mainApp.classList.add('hidden');
                console.log('✅ Login screen displayed');
            } else {
                console.error('❌ Login screen or main app elements not found');
            }
        } catch (error) {
            console.error('❌ Error showing login screen:', error);
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        console.log('🔐 Processing login...');
        
        try {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const loginBtn = document.getElementById('login-btn');
            const loginError = document.getElementById('login-error');
            
            console.log('🔐 Login data:', { username: username, passwordLength: password.length });
            
            if (!username || !password) {
                this.showLoginError('Please enter username and password');
                return;
            }
            
            // Update UI
            loginBtn.disabled = true;
            loginBtn.textContent = 'Authenticating...';
            loginError.classList.add('hidden');
            
            console.log('🔐 Attempting authentication...');
            
            let result;
            if (window.pywebview?.api) {
                console.log('🔐 Using PyWebView API for login');
                result = await this.callAPI('login', username, password);
            } else {
                console.log('🔐 Using demo login');
                await new Promise(resolve => setTimeout(resolve, 1000));
                result = { 
                    success: username === 'admin' && password === 'admin', 
                    username: username 
                };
            }
            
            console.log('🔐 Login result:', result);
            
            if (result.success) {
                console.log('✅ Login successful - switching to main app');
                this.showMainApp(result.username || username);
                
                if (result.requirePasswordChange) {
                    this.showMessage('Password change required on first login', 'warning');
                } else {
                    await this.loadInitialData();
                }
                
                this.showMessage('Welcome to Medical Practice Management!', 'success');
            } else {
                console.log('❌ Login failed:', result.error);
                this.showLoginError(result.error || 'Invalid credentials. Try admin/admin for demo');
            }
        } catch (error) {
            console.error('❌ Login error:', error);
            this.showLoginError('Login failed: ' + error.message);
        } finally {
            // Reset button
            const loginBtn = document.getElementById('login-btn');
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login';
            }
        }
    }

    showMainApp(username) {
        console.log('🏠 Showing main application for user:', username);
        
        try {
            const loginScreen = document.getElementById('login-screen');
            const mainApp = document.getElementById('main-app');
            const userNameEl = document.getElementById('user-name');
            
            if (loginScreen && mainApp) {
                loginScreen.classList.add('hidden');
                mainApp.classList.remove('hidden');
                
                if (userNameEl) {
                    userNameEl.textContent = username;
                }
                
                console.log('✅ Main app displayed successfully');
                
                // Ensure the doctors tab is active
                this.switchTab('doctors');
            } else {
                console.error('❌ Required elements not found for main app display');
                throw new Error('Main app elements not found');
            }
        } catch (error) {
            console.error('❌ Error showing main app:', error);
            this.showMessage('Error displaying main application', 'error');
        }
    }

    showLoginError(message) {
        console.log('❌ Showing login error:', message);
        const loginError = document.getElementById('login-error');
        if (loginError) {
            loginError.textContent = message;
            loginError.classList.remove('hidden');
        }
    }

    switchTab(tabName) {
        console.log('📋 Switching to tab:', tabName);
        
        try {
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
                console.log('✅ Tab switched successfully to:', tabName);
            } else {
                console.error('❌ Tab content not found for:', tabName);
            }
            
            this.currentTab = tabName;
        } catch (error) {
            console.error('❌ Error switching tabs:', error);
        }
    }

    async loadInitialData() {
        console.log('📊 Loading initial data...');
        
        try {
            await this.loadDoctors();
            console.log('✅ Initial data loaded');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
        }
    }

    async loadDoctors() {
        console.log('👨‍⚕️ Loading doctors...');
        
        try {
            // Use sample data for now
            this.renderDoctorsTable(this.allData.doctors);
            this.updateRecordCount(this.allData.doctors.length);
            console.log('✅ Doctors loaded and rendered');
        } catch (error) {
            console.error('❌ Error loading doctors:', error);
        }
    }

    loadSampleData() {
        console.log('📝 Loading sample data...');
        
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
        
        console.log('✅ Sample data loaded:', this.allData.doctors.length, 'doctors');
    }

    renderDoctorsTable(doctors) {
        console.log('📊 Rendering doctors table with', doctors.length, 'doctors');
        
        try {
            const tbody = document.getElementById('doctors-table-body');
            if (!tbody) {
                console.error('❌ Doctors table body not found');
                return;
            }
            
            tbody.innerHTML = '';
            
            doctors.forEach((doctor, index) => {
                console.log(`👨‍⚕️ Rendering doctor ${index + 1}:`, doctor.name);
                
                const row = document.createElement('tr');
                row.className = 'border-b border-slate-700 hover:bg-slate-700/50 transition-colors duration-150 ease-in-out';
                row.dataset.doctorId = doctor.id;
                
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
            
            console.log('✅ Doctors table rendered successfully');
        } catch (error) {
            console.error('❌ Error rendering doctors table:', error);
        }
    }

    // Helper methods
    renderStatusBadge(status) {
        const badges = {
            active: 'bg-green-700 text-green-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full',
            inactive: 'bg-red-700 text-red-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full'
        };
        
        const badgeClass = badges[status] || 'bg-slate-700 text-slate-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full';
        return `<span class="${badgeClass}">${status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown'}</span>`;
    }

    renderAccountStatus(status) {
        if (status === 'active') {
            return '<span class="text-green-400">✓ Active</span>';
        } else {
            return '<span class="text-slate-500">✗ Inactive</span>';
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

    formatSubscriptionInfo(doctor) {
        if (!doctor.subscriptionStart || !doctor.subscriptionEnd) {
            return 'Not Set';
        }
        
        const startDate = this.formatDate(doctor.subscriptionStart);
        return `${startDate} to...`;
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString();
        } catch {
            return dateStr;
        }
    }

    updateRecordCount(count) {
        const recordCountEl = document.getElementById('record-count');
        if (recordCountEl) {
            recordCountEl.textContent = `${count} records`;
        }
    }

    // Placeholder methods
    applyTheme(theme) {
        console.log('🎨 Applying theme:', theme);
        this.theme = theme;
    }

    async checkAuthentication() {
        console.log('🔍 Checking authentication...');
        this.showLoginScreen();
    }

    refreshData() {
        console.log('🔄 Refresh data requested');
        this.showMessage('Refresh functionality - Coming soon', 'info');
    }

    showNewDoctorModal() {
        console.log('➕ New doctor modal requested');
        this.showMessage('New doctor creation - Coming soon', 'info');
    }

    exportCurrentView() {
        console.log('📤 Export requested');
        this.showMessage('Export functionality - Coming soon', 'info');
    }

    showMessage(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Simple alert for now
        if (type === 'error') {
            alert('Error: ' + message);
        } else if (type === 'warning') {
            alert('Warning: ' + message);
        } else {
            console.log('INFO:', message);
        }
    }

    async callAPI(method, ...args) {
        console.log('📡 API call:', method, args);
        
        if (window.pywebview && window.pywebview.api) {
            try {
                const result = await window.pywebview.api[method](...args);
                console.log('📡 API result:', result);
                return result;
            } catch (error) {
                console.error('📡 API error:', error);
                throw error;
            }
        } else {
            console.log('📡 Mock API call');
            return this.mockAPI(method, ...args);
        }
    }

    mockAPI(method, ...args) {
        const delay = () => new Promise(resolve => setTimeout(resolve, 500));
        
        switch(method) {
            case 'login':
                return delay().then(() => ({ 
                    success: args[0] === 'admin' && args[1] === 'admin', 
                    username: args[0] 
                }));
            default:
                return Promise.resolve({ success: true });
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 DOM loaded, initializing Medical Practice App...');
    try {
        window.app = new MedicalPracticeApp();
        console.log('✅ App initialized successfully');
    } catch (error) {
        console.error('❌ App initialization failed:', error);
        alert('Application failed to initialize: ' + error.message);
    }
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('💥 Global error:', e.error);
    alert('Application error: ' + e.error.message);
});

console.log('✅ JavaScript file loaded completely');

// Prevent context menu on production
if (window.pywebview) {
    document.addEventListener('contextmenu', (e) => {
        if (!e.target.closest('tr')) {
            e.preventDefault();
        }
    });
}