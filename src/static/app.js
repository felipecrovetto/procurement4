// Procurement Management System - Frontend JavaScript

// Global variables
let currentPage = 1;
let currentSection = 'dashboard';
let charts = {};

// API Base URL
const API_BASE = '/api';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check authentication first
    checkAuthentication();
    
    // Load dashboard by default
    showSection('dashboard');
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Load initial data
    loadDashboardData();
    
    // Check for alerts periodically
    setInterval(updateAlertBadge, 30000); // Every 30 seconds
}

// Authentication Functions
async function checkAuthentication() {
    try {
        const response = await fetch('/api/auth/check');
        const data = await response.json();
        
        if (!data.authenticated) {
            window.location.href = '/login.html';
        }
    } catch (error) {
        console.error('Auth check error:', error);
        window.location.href = '/login.html';
    }
}

async function logout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST'
        });
        
        if (response.ok) {
            window.location.href = '/login.html';
        } else {
            showAlert('Error al cerrar sesión', 'danger');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showAlert('Error de conexión al cerrar sesión', 'danger');
    }
}

function initializeEventListeners() {
    // Excel upload form
    const excelForm = document.getElementById('excelUploadForm');
    if (excelForm) {
        excelForm.addEventListener('submit', handleExcelUpload);
    }
    
    // Search inputs
    const searchInputs = ['processSearch', 'supplierSearch'];
    searchInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('keyup', debounce(function() {
                if (inputId.includes('process')) loadProcesses();
                if (inputId.includes('supplier')) loadSuppliers();
            }, 500));
        }
    });
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showLoading() {
    try {
        const loadingModalEl = document.getElementById('loadingModal');
        if (loadingModalEl) {
            // Cerrar cualquier modal existente primero
            const existingModal = bootstrap.Modal.getInstance(loadingModalEl);
            if (existingModal) {
                existingModal.hide();
            }
            
            // Crear y mostrar nuevo modal
            const modal = new bootstrap.Modal(loadingModalEl, {
                backdrop: 'static',
                keyboard: false
            });
            modal.show();
            
            // Timeout de seguridad para evitar que se quede cargando indefinidamente
            setTimeout(() => {
                hideLoading();
            }, 30000); // 30 segundos máximo
        }
    } catch (error) {
        console.error('Error showing loading modal:', error);
    }
}

function hideLoading() {
    try {
        const loadingModalEl = document.getElementById('loadingModal');
        if (loadingModalEl) {
            // Intentar obtener instancia existente
            let modal = bootstrap.Modal.getInstance(loadingModalEl);
            
            if (modal) {
                modal.hide();
            } else {
                // Si no hay instancia, crear una y ocultarla inmediatamente
                modal = new bootstrap.Modal(loadingModalEl);
                modal.hide();
            }
            
            // Forzar ocultación después de un breve delay
            setTimeout(() => {
                loadingModalEl.classList.remove('show');
                loadingModalEl.style.display = 'none';
                document.body.classList.remove('modal-open');
                
                // Remover backdrop si existe
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
            }, 100);
        }
    } catch (error) {
        console.error('Error hiding loading modal:', error);
        // Forzar ocultación en caso de error
        const loadingModalEl = document.getElementById('loadingModal');
        if (loadingModalEl) {
            loadingModalEl.classList.remove('show');
            loadingModalEl.style.display = 'none';
            document.body.classList.remove('modal-open');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the current section
    const currentSectionEl = document.getElementById(currentSection);
    currentSectionEl.insertBefore(alertDiv, currentSectionEl.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP'
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('es-CL');
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('es-CL');
}

// Navigation Functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    const section = document.getElementById(sectionName);
    if (section) {
        section.style.display = 'block';
        currentSection = sectionName;
        
        // Update navbar active state
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Load section-specific data
        switch(sectionName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'processes':
                loadProcesses();
                break;
            case 'suppliers':
                loadSuppliers();
                break;
            case 'bids':
                loadBids();
                break;
            case 'evaluation':
                loadEvaluation();
                break;
            case 'documents':
                loadDocuments();
                break;
            case 'alerts':
                loadAlerts();
                break;
            case 'calendar':
                loadCalendar();
                break;
            case 'excel':
                // Excel section doesn't need initial data load
                break;
            case 'reports':
                loadReports();
                break;
        }
    }
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/reports/dashboard`);
        const data = await response.json();
        
        if (response.ok) {
            updateDashboardCounters(data.counters);
            updateDashboardCharts(data);
            updateRecentProcesses(data.recent_processes);
            updateActiveAlerts(data.alert_priority_distribution);
        } else {
            showAlert('Error cargando datos del dashboard: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar dashboard', 'danger');
        console.error('Dashboard load error:', error);
    }
}

function updateDashboardCounters(counters) {
    document.getElementById('totalProcesses').textContent = counters.total_processes || 0;
    document.getElementById('totalSuppliers').textContent = counters.total_suppliers || 0;
    document.getElementById('totalBids').textContent = counters.total_bids || 0;
    document.getElementById('activeAlerts').textContent = counters.active_alerts || 0;
    
    // Update total savings
    const totalSavingsElement = document.getElementById('totalSavings');
    if (totalSavingsElement) {
        totalSavingsElement.textContent = formatCurrency(counters.total_savings || 0);
    }
    
    // Update alert badge
    updateAlertBadge();
}

function updateDashboardCharts(data) {
    // Status distribution chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx && data.process_status_distribution) {
        if (charts.statusChart) charts.statusChart.destroy();
        
        charts.statusChart = new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: data.process_status_distribution.map(item => item.status),
                datasets: [{
                    data: data.process_status_distribution.map(item => item.count),
                    backgroundColor: [
                        '#6c757d', // draft
                        '#198754', // active
                        '#ffc107', // evaluation
                        '#0dcaf0', // completed
                        '#dc3545'  // cancelled
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Savings chart
    const savingsCtx = document.getElementById('savingsChart');
    if (savingsCtx && data.savings_data && data.savings_data.savings_by_process) {
        if (charts.savingsChart) charts.savingsChart.destroy();
        
        const savingsData = data.savings_data.savings_by_process.slice(0, 10); // Top 10
        
        charts.savingsChart = new Chart(savingsCtx, {
            type: 'bar',
            data: {
                labels: savingsData.map(item => item.process_title.substring(0, 20) + '...'),
                datasets: [{
                    label: 'Ahorro ($)',
                    data: savingsData.map(item => item.saving),
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Ahorro: ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Top suppliers chart
    const topSuppliersCtx = document.getElementById('topSuppliersChart');
    if (topSuppliersCtx && data.top_suppliers) {
        if (charts.topSuppliersChart) charts.topSuppliersChart.destroy();
        
        charts.topSuppliersChart = new Chart(topSuppliersCtx, {
            type: 'bar',
            data: {
                labels: data.top_suppliers.map(item => item.supplier_name),
                datasets: [{
                    label: 'Ofertas',
                    data: data.top_suppliers.map(item => item.bid_count),
                    backgroundColor: '#007bff',
                    borderColor: '#0056b3',
                    borderWidth: 1
                }, {
                    label: 'Adjudicadas',
                    data: data.top_suppliers.map(item => item.awarded_count),
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Monthly trends chart
    const monthlyTrendsCtx = document.getElementById('monthlyTrendsChart');
    if (monthlyTrendsCtx && data.monthly_trends) {
        if (charts.monthlyTrendsChart) charts.monthlyTrendsChart.destroy();
        
        charts.monthlyTrendsChart = new Chart(monthlyTrendsCtx, {
            type: 'line',
            data: {
                labels: data.monthly_trends.map(item => item.month),
                datasets: [{
                    label: 'Procesos Creados',
                    data: data.monthly_trends.map(item => item.count),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

function updateRecentProcesses(processes) {
    const container = document.getElementById('recentProcesses');
    if (!container) return;
    
    if (!processes || processes.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay procesos recientes</p>';
        return;
    }
    
    const html = processes.map(process => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-2">
            <div>
                <h6 class="mb-1">${process.process_number}</h6>
                <p class="mb-0 text-muted small">${process.title}</p>
            </div>
            <span class="badge status-${process.status}">${process.status}</span>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function updateActiveAlerts(alertData) {
    const container = document.getElementById('activeAlertsList');
    if (!container) return;
    
    if (!alertData || alertData.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay alertas activas</p>';
        return;
    }
    
    const html = alertData.map(alert => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-2">
            <div>
                <span class="badge priority-${alert.priority}">${alert.priority}</span>
            </div>
            <span class="fw-bold">${alert.count}</span>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

async function updateAlertBadge() {
    try {
        const response = await fetch(`${API_BASE}/alerts/stats`);
        const data = await response.json();
        
        if (response.ok) {
            const badge = document.getElementById('alertBadge');
            const activeAlerts = data.by_status?.active || 0;
            
            if (activeAlerts > 0) {
                badge.textContent = activeAlerts;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error updating alert badge:', error);
    }
}

// Process Functions
async function loadProcesses(page = 1) {
    try {
        const search = document.getElementById('processSearch')?.value || '';
        const status = document.getElementById('processStatusFilter')?.value || '';
        const type = document.getElementById('processTypeFilter')?.value || '';
        
        const params = new URLSearchParams({
            page: page,
            per_page: 10,
            search: search,
            status: status,
            process_type: type
        });
        
        const response = await fetch(`${API_BASE}/processes?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateProcessesTable(data.processes);
            updatePagination('processes', data.current_page, data.pages);
        } else {
            showAlert('Error cargando procesos: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar procesos', 'danger');
        console.error('Processes load error:', error);
    }
}

function updateProcessesTable(processes) {
    const tbody = document.getElementById('processesTableBody');
    if (!tbody) return;
    
    if (!processes || processes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron procesos</td></tr>';
        return;
    }
    
    const html = processes.map(process => `
        <tr>
            <td>${process.process_number}</td>
            <td>${process.title}</td>
            <td>${process.process_type === 'simple_purchase' ? 'Compra Simple' : 'Licitación Grande'}</td>
            <td><span class="badge status-${process.status}">${process.status}</span></td>
            <td>${process.budget ? formatCurrency(process.budget) : '-'}</td>
            <td>${formatDate(process.end_date)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editProcess(${process.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-info" onclick="showExportModal(${process.id})" title="Exportar Informe">
                        <i class="bi bi-download"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteProcess(${process.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function showProcessModal(processId = null) {
    const modal = new bootstrap.Modal(document.getElementById('processModal'));
    const form = document.getElementById('processForm');
    
    // Reset form
    form.reset();
    document.getElementById('processId').value = '';
    
    if (processId) {
        // Load process data for editing
        loadProcessForEdit(processId);
    }
    
    modal.show();
}

async function loadProcessForEdit(processId) {
    try {
        const response = await fetch(`${API_BASE}/processes/${processId}`);
        const process = await response.json();
        
        if (response.ok) {
            document.getElementById('processId').value = process.id;
            document.getElementById('processNumber').value = process.process_number;
            document.getElementById('processTitle').value = process.title;
            document.getElementById('processDescription').value = process.description || '';
            document.getElementById('processType').value = process.process_type;
            document.getElementById('processStatus').value = process.status;
            document.getElementById('processBudget').value = process.budget || '';
            document.getElementById('processNotes').value = process.notes || '';
            
            if (process.start_date) {
                document.getElementById('processStartDate').value = new Date(process.start_date).toISOString().slice(0, 16);
            }
            if (process.end_date) {
                document.getElementById('processEndDate').value = new Date(process.end_date).toISOString().slice(0, 16);
            }
        } else {
            showAlert('Error cargando proceso: ' + process.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar proceso', 'danger');
        console.error('Process load error:', error);
    }
}

async function saveProcess() {
    const form = document.getElementById('processForm');
    const formData = new FormData(form);
    
    const processData = {
        process_number: document.getElementById('processNumber').value,
        title: document.getElementById('processTitle').value,
        description: document.getElementById('processDescription').value,
        process_type: document.getElementById('processType').value,
        status: document.getElementById('processStatus').value,
        budget: document.getElementById('processBudget').value ? parseFloat(document.getElementById('processBudget').value) : null,
        start_date: document.getElementById('processStartDate').value || null,
        end_date: document.getElementById('processEndDate').value || null,
        notes: document.getElementById('processNotes').value
    };
    
    const processId = document.getElementById('processId').value;
    const isEdit = processId !== '';
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/processes${isEdit ? '/' + processId : ''}`, {
            method: isEdit ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(processData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(`Proceso ${isEdit ? 'actualizado' : 'creado'} exitosamente`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('processModal')).hide();
            loadProcesses();
        } else {
            showAlert('Error guardando proceso: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al guardar proceso', 'danger');
        console.error('Process save error:', error);
    } finally {
        hideLoading();
    }
}

function editProcess(processId) {
    showProcessModal(processId);
}

async function deleteProcess(processId) {
    if (!confirm('¿Está seguro de que desea eliminar este proceso?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/processes/${processId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Proceso eliminado exitosamente', 'success');
            loadProcesses();
        } else {
            showAlert('Error eliminando proceso: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al eliminar proceso', 'danger');
        console.error('Process delete error:', error);
    } finally {
        hideLoading();
    }
}

async function exportProcesses() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/reports/export/processes`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `procesos_${new Date().toISOString().slice(0, 10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Archivo exportado exitosamente', 'success');
        } else {
            const error = await response.json();
            showAlert('Error exportando procesos: ' + error.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al exportar procesos', 'danger');
        console.error('Export error:', error);
    } finally {
        hideLoading();
    }
}

// Supplier Functions
async function loadSuppliers(page = 1) {
    try {
        const search = document.getElementById('supplierSearch')?.value || '';
        const status = document.getElementById('supplierStatusFilter')?.value || '';
        
        const params = new URLSearchParams({
            page: page,
            per_page: 10,
            search: search,
            status: status
        });
        
        const response = await fetch(`${API_BASE}/suppliers?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateSuppliersTable(data.suppliers);
            updatePagination('suppliers', data.current_page, data.pages);
        } else {
            showAlert('Error cargando proveedores: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar proveedores', 'danger');
        console.error('Suppliers load error:', error);
    }
}

function updateSuppliersTable(suppliers) {
    const tbody = document.getElementById('suppliersTableBody');
    if (!tbody) return;
    
    if (!suppliers || suppliers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron proveedores</td></tr>';
        return;
    }
    
    const html = suppliers.map(supplier => `
        <tr>
            <td>${supplier.name}</td>
            <td>${supplier.contact_person || '-'}</td>
            <td>${supplier.email || '-'}</td>
            <td>${supplier.phone || '-'}</td>
            <td>${supplier.rut || '-'}</td>
            <td><span class="badge status-${supplier.status}">${supplier.status}</span></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editSupplier(${supplier.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteSupplier(${supplier.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function showSupplierModal(supplierId = null) {
    const modal = new bootstrap.Modal(document.getElementById('supplierModal'));
    const form = document.getElementById('supplierForm');
    
    // Reset form
    form.reset();
    document.getElementById('supplierId').value = '';
    
    if (supplierId) {
        // Load supplier data for editing
        loadSupplierForEdit(supplierId);
    }
    
    modal.show();
}

async function loadSupplierForEdit(supplierId) {
    try {
        const response = await fetch(`${API_BASE}/suppliers/${supplierId}`);
        const supplier = await response.json();
        
        if (response.ok) {
            document.getElementById('supplierId').value = supplier.id;
            document.getElementById('supplierName').value = supplier.name;
            document.getElementById('supplierContact').value = supplier.contact_person || '';
            document.getElementById('supplierEmail').value = supplier.email || '';
            document.getElementById('supplierPhone').value = supplier.phone || '';
            document.getElementById('supplierAddress').value = supplier.address || '';
            document.getElementById('supplierRut').value = supplier.rut || '';
            document.getElementById('supplierStatus').value = supplier.status;
            document.getElementById('supplierNotes').value = supplier.notes || '';
        } else {
            showAlert('Error cargando proveedor: ' + supplier.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar proveedor', 'danger');
        console.error('Supplier load error:', error);
    }
}

async function saveSupplier() {
    const supplierData = {
        name: document.getElementById('supplierName').value,
        contact_person: document.getElementById('supplierContact').value,
        email: document.getElementById('supplierEmail').value,
        phone: document.getElementById('supplierPhone').value,
        address: document.getElementById('supplierAddress').value,
        rut: document.getElementById('supplierRut').value,
        status: document.getElementById('supplierStatus').value,
        notes: document.getElementById('supplierNotes').value
    };
    
    const supplierId = document.getElementById('supplierId').value;
    const isEdit = supplierId !== '';
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/suppliers${isEdit ? '/' + supplierId : ''}`, {
            method: isEdit ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(supplierData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(`Proveedor ${isEdit ? 'actualizado' : 'creado'} exitosamente`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('supplierModal')).hide();
            loadSuppliers();
        } else {
            showAlert('Error guardando proveedor: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al guardar proveedor', 'danger');
        console.error('Supplier save error:', error);
    } finally {
        hideLoading();
    }
}

function editSupplier(supplierId) {
    showSupplierModal(supplierId);
}

async function deleteSupplier(supplierId) {
    if (!confirm('¿Está seguro de que desea eliminar este proveedor?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/suppliers/${supplierId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Proveedor eliminado exitosamente', 'success');
            loadSuppliers();
        } else {
            showAlert('Error eliminando proveedor: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al eliminar proveedor', 'danger');
        console.error('Supplier delete error:', error);
    } finally {
        hideLoading();
    }
}

async function exportSuppliers() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/reports/export/suppliers`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `proveedores_${new Date().toISOString().slice(0, 10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Archivo exportado exitosamente', 'success');
        } else {
            const error = await response.json();
            showAlert('Error exportando proveedores: ' + error.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al exportar proveedores', 'danger');
        console.error('Export error:', error);
    } finally {
        hideLoading();
    }
}

// Bids Functions
async function loadBids(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 10
        });
        
        const response = await fetch(`${API_BASE}/bids?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateBidsTable(data.bids);
            updatePagination('bids', data.current_page, data.pages);
        } else {
            showAlert('Error cargando ofertas: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar ofertas', 'danger');
        console.error('Bids load error:', error);
    }
}

function updateBidsTable(bids) {
    const tbody = document.getElementById('bidsTableBody');
    if (!tbody) return;
    
    if (!bids || bids.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron ofertas</td></tr>';
        return;
    }
    
    const html = bids.map(bid => `
        <tr>
            <td>${bid.process_title || '-'}</td>
            <td>${bid.supplier_name || '-'}</td>
            <td>${bid.bid_amount ? formatCurrency(bid.bid_amount) : '-'}</td>
            <td>${bid.technical_score || '-'}</td>
            <td>${bid.commercial_score || '-'}</td>
            <td><span class="badge status-${bid.status}">${bid.status}</span></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editBid(${bid.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteBid(${bid.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function showBidModal() {
    // Implementation for bid modal
    showAlert('Funcionalidad de ofertas en desarrollo', 'info');
}

function editBid(bidId) {
    showAlert('Funcionalidad de edición de ofertas en desarrollo', 'info');
}

async function deleteBid(bidId) {
    if (!confirm('¿Está seguro de que desea eliminar esta oferta?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/bids/${bidId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Oferta eliminada exitosamente', 'success');
            loadBids();
        } else {
            showAlert('Error eliminando oferta: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al eliminar oferta', 'danger');
        console.error('Bid delete error:', error);
    } finally {
        hideLoading();
    }
}

// Documents Functions
async function loadDocuments(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 10
        });
        
        const response = await fetch(`${API_BASE}/documents?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateDocumentsTable(data.documents);
            updatePagination('documents', data.current_page, data.pages);
        } else {
            showAlert('Error cargando documentos: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar documentos', 'danger');
        console.error('Documents load error:', error);
    }
}

function updateDocumentsTable(documents) {
    const tbody = document.getElementById('documentsTableBody');
    if (!tbody) return;
    
    if (!documents || documents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron documentos</td></tr>';
        return;
    }
    
    const html = documents.map(doc => `
        <tr>
            <td>${doc.original_filename}</td>
            <td>${doc.document_type || '-'}</td>
            <td>${doc.process_title || '-'}</td>
            <td>${doc.supplier_name || '-'}</td>
            <td>${formatFileSize(doc.file_size)}</td>
            <td>${formatDate(doc.upload_date)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="downloadDocument(${doc.id})">
                        <i class="bi bi-download"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteDocument(${doc.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function formatFileSize(bytes) {
    if (!bytes) return '-';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function showDocumentModal() {
    showAlert('Funcionalidad de subida de documentos en desarrollo', 'info');
}

async function downloadDocument(documentId) {
    try {
        const response = await fetch(`${API_BASE}/documents/${documentId}/download`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = ''; // Filename will be set by server
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const error = await response.json();
            showAlert('Error descargando documento: ' + error.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al descargar documento', 'danger');
        console.error('Download error:', error);
    }
}

async function deleteDocument(documentId) {
    if (!confirm('¿Está seguro de que desea eliminar este documento?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Documento eliminado exitosamente', 'success');
            loadDocuments();
        } else {
            showAlert('Error eliminando documento: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al eliminar documento', 'danger');
        console.error('Document delete error:', error);
    } finally {
        hideLoading();
    }
}

// Alerts Functions
async function loadAlerts(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 10
        });
        
        const response = await fetch(`${API_BASE}/alerts?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateAlertsTable(data.alerts);
            updatePagination('alerts', data.current_page, data.pages);
        } else {
            showAlert('Error cargando alertas: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al cargar alertas', 'danger');
        console.error('Alerts load error:', error);
    }
}

function updateAlertsTable(alerts) {
    const tbody = document.getElementById('alertsTableBody');
    if (!tbody) return;
    
    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No se encontraron alertas</td></tr>';
        return;
    }
    
    const html = alerts.map(alert => `
        <tr>
            <td>${alert.title}</td>
            <td>${alert.alert_type}</td>
            <td><span class="badge priority-${alert.priority}">${alert.priority}</span></td>
            <td><span class="badge status-${alert.status}">${alert.status}</span></td>
            <td>${alert.process_title || '-'}</td>
            <td>${formatDate(alert.created_date)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-warning" onclick="dismissAlert(${alert.id})">
                        <i class="bi bi-x"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="resolveAlert(${alert.id})">
                        <i class="bi bi-check"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function showAlertModal() {
    showAlert('Funcionalidad de creación de alertas en desarrollo', 'info');
}

async function dismissAlert(alertId) {
    try {
        const response = await fetch(`${API_BASE}/alerts/${alertId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'dismissed' })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Alerta descartada', 'success');
            loadAlerts();
            updateAlertBadge();
        } else {
            showAlert('Error descartando alerta: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al descartar alerta', 'danger');
        console.error('Alert dismiss error:', error);
    }
}

async function resolveAlert(alertId) {
    try {
        const response = await fetch(`${API_BASE}/alerts/${alertId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'resolved' })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Alerta resuelta', 'success');
            loadAlerts();
            updateAlertBadge();
        } else {
            showAlert('Error resolviendo alerta: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al resolver alerta', 'danger');
        console.error('Alert resolve error:', error);
    }
}

async function checkDeadlines() {
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/alerts/check-deadlines`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            loadAlerts();
            updateAlertBadge();
        } else {
            showAlert('Error verificando vencimientos: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al verificar vencimientos', 'danger');
        console.error('Check deadlines error:', error);
    } finally {
        hideLoading();
    }
}

// Excel Functions
async function handleExcelUpload(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('excelFile');
    const tableType = document.getElementById('tableType').value;
    
    if (!fileInput.files[0]) {
        showAlert('Seleccione un archivo Excel', 'warning');
        return;
    }
    
    if (!tableType) {
        showAlert('Seleccione el tipo de tabla', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('table_type', tableType);
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/excel/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            document.getElementById('excelUploadForm').reset();
            
            if (result.validation_warnings && result.validation_warnings.length > 0) {
                showAlert('Advertencias: ' + result.validation_warnings.join(', '), 'warning');
            }
        } else {
            showAlert('Error procesando archivo: ' + result.error, 'danger');
            
            if (result.validation_errors) {
                showAlert('Errores de validación: ' + result.validation_errors.join(', '), 'danger');
            }
        }
    } catch (error) {
        showAlert('Error de conexión al subir archivo', 'danger');
        console.error('Excel upload error:', error);
    } finally {
        hideLoading();
    }
}

async function downloadTemplate(tableType) {
    try {
        const response = await fetch(`${API_BASE}/excel/templates/${tableType}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `plantilla_${tableType}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Plantilla descargada exitosamente', 'success');
        } else {
            const error = await response.json();
            showAlert('Error descargando plantilla: ' + error.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al descargar plantilla', 'danger');
        console.error('Template download error:', error);
    }
}

async function loadExcelData() {
    const tableType = document.getElementById('excelDataType').value;
    const container = document.getElementById('excelDataDisplay');
    
    if (!tableType) {
        container.innerHTML = '<p class="text-muted">Selecciona un tipo de datos para visualizar.</p>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/excel/data/${tableType}`);
        const data = await response.json();
        
        if (response.ok) {
            displayExcelData(data.data, tableType);
        } else {
            container.innerHTML = `<p class="text-danger">Error cargando datos: ${data.error}</p>`;
        }
    } catch (error) {
        container.innerHTML = '<p class="text-danger">Error de conexión al cargar datos</p>';
        console.error('Excel data load error:', error);
    }
}

function displayExcelData(data, tableType) {
    const container = document.getElementById('excelDataDisplay');
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay datos disponibles para este tipo.</p>';
        return;
    }
    
    // Create table based on data structure
    const firstItem = data[0];
    const columns = Object.keys(firstItem).filter(key => key !== 'id' && key !== 'upload_date');
    
    const html = `
        <div class="table-responsive">
            <table class="table table-striped table-sm">
                <thead>
                    <tr>
                        ${columns.map(col => `<th>${col}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.slice(0, 20).map(item => `
                        <tr>
                            ${columns.map(col => `<td>${item[col] || '-'}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        ${data.length > 20 ? `<p class="text-muted">Mostrando 20 de ${data.length} registros</p>` : ''}
    `;
    
    container.innerHTML = html;
}

// Reports Functions
async function loadReports() {
    // Load process trends chart
    loadProcessTrendsChart();
    
    // Load process list for analysis
    loadProcessesForAnalysis();
}

async function loadProcessTrendsChart() {
    try {
        const response = await fetch(`${API_BASE}/reports/chart/process-trends`);
        const data = await response.json();
        
        if (response.ok) {
            const ctx = document.getElementById('trendsChart');
            if (ctx && data.data) {
                if (charts.trendsChart) charts.trendsChart.destroy();
                
                charts.trendsChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.data.map(item => item.month),
                        datasets: [{
                            label: 'Procesos Creados',
                            data: data.data.map(item => item.count),
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        } else {
            console.error('Error loading trends chart:', data.error);
        }
    } catch (error) {
        console.error('Trends chart load error:', error);
    }
}

async function loadProcessesForAnalysis() {
    try {
        const response = await fetch(`${API_BASE}/processes?per_page=100`);
        const data = await response.json();
        
        if (response.ok) {
            const select = document.getElementById('processAnalysisSelect');
            select.innerHTML = '<option value="">Seleccionar proceso...</option>';
            
            data.processes.forEach(process => {
                const option = document.createElement('option');
                option.value = process.id;
                option.textContent = `${process.process_number} - ${process.title}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading processes for analysis:', error);
    }
}

async function generateProcessAnalysis() {
    const processId = document.getElementById('processAnalysisSelect').value;
    const container = document.getElementById('processAnalysisResult');
    
    if (!processId) {
        showAlert('Seleccione un proceso para analizar', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/reports/process/${processId}/analysis`);
        const data = await response.json();
        
        if (response.ok) {
            displayProcessAnalysis(data, container);
        } else {
            container.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
        }
    } catch (error) {
        container.innerHTML = '<p class="text-danger">Error de conexión</p>';
        console.error('Process analysis error:', error);
    } finally {
        hideLoading();
    }
}

function displayProcessAnalysis(data, container) {
    const analysis = data.analysis;
    
    let html = `
        <div class="card">
            <div class="card-header">
                <h6>Análisis del Proceso: ${data.process.process_number}</h6>
            </div>
            <div class="card-body">
    `;
    
    if (analysis.message) {
        html += `<p class="text-muted">${analysis.message}</p>`;
    } else {
        html += `<p><strong>Total de ofertas:</strong> ${analysis.total_bids}</p>`;
        
        if (analysis.financial_analysis && Object.keys(analysis.financial_analysis).length > 0) {
            html += `
                <h6>Análisis Financiero</h6>
                <ul>
                    <li>Promedio: ${formatCurrency(analysis.financial_analysis.average_amount)}</li>
                    <li>Oferta más baja: ${formatCurrency(analysis.financial_analysis.lowest_bid)}</li>
                    <li>Oferta más alta: ${formatCurrency(analysis.financial_analysis.highest_bid)}</li>
                    ${analysis.financial_analysis.savings_vs_budget ? 
                        `<li>Ahorro vs presupuesto: ${formatCurrency(analysis.financial_analysis.savings_vs_budget)} (${analysis.financial_analysis.savings_percentage.toFixed(1)}%)</li>` 
                        : ''}
                </ul>
            `;
        }
        
        if (analysis.technical_analysis && Object.keys(analysis.technical_analysis).length > 0) {
            html += `
                <h6>Análisis Técnico</h6>
                <ul>
                    <li>Puntuación promedio: ${analysis.technical_analysis.average_score.toFixed(2)}</li>
                    <li>Puntuación más alta: ${analysis.technical_analysis.highest_score}</li>
                    <li>Puntuación más baja: ${analysis.technical_analysis.lowest_score}</li>
                </ul>
            `;
        }
    }
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Pagination Functions
function updatePagination(section, currentPage, totalPages) {
    const container = document.getElementById(`${section}Pagination`);
    if (!container || totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<ul class="pagination justify-content-center">';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="load${section.charAt(0).toUpperCase() + section.slice(1)}(${currentPage - 1})">
                Anterior
            </a>
        </li>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="load${section.charAt(0).toUpperCase() + section.slice(1)}(${i})">
                    ${i}
                </a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="load${section.charAt(0).toUpperCase() + section.slice(1)}(${currentPage + 1})">
                Siguiente
            </a>
        </li>
    `;
    
    html += '</ul>';
    container.innerHTML = html;
}



// Evaluation Functions
let currentEvaluationProcess = null;

async function loadEvaluation() {
    try {
        // Load processes for evaluation
        await loadEvaluationProcesses();
        
        // Load evaluation data if a process is selected
        const processSelect = document.getElementById('evaluationProcessSelect');
        if (processSelect.value) {
            await loadEvaluationData(processSelect.value);
        }
    } catch (error) {
        showAlert('Error cargando módulo de evaluación', 'danger');
        console.error('Evaluation load error:', error);
    }
}

async function loadEvaluationProcesses() {
    try {
        const response = await fetch(`${API_BASE}/processes`);
        const data = await response.json();
        
        if (response.ok) {
            const select = document.getElementById('evaluationProcessSelect');
            select.innerHTML = '<option value="">Seleccionar Proceso</option>';
            
            data.processes.forEach(process => {
                const option = document.createElement('option');
                option.value = process.id;
                option.textContent = `${process.process_number} - ${process.title}`;
                select.appendChild(option);
            });
            
            // Add event listener for process selection
            select.addEventListener('change', function() {
                if (this.value) {
                    loadEvaluationData(this.value);
                } else {
                    clearEvaluationData();
                }
            });
        }
    } catch (error) {
        console.error('Error loading evaluation processes:', error);
    }
}

async function loadEvaluationData(processId) {
    currentEvaluationProcess = processId;
    
    try {
        // Load criteria, bids, and ranking for the selected process
        await Promise.all([
            loadEvaluationCriteria(processId),
            loadProcessBids(processId),
            loadBidRanking(processId)
        ]);
    } catch (error) {
        console.error('Error loading evaluation data:', error);
    }
}

async function loadEvaluationCriteria(processId) {
    try {
        const response = await fetch(`${API_BASE}/evaluation/criteria/${processId}`);
        const criteria = await response.json();
        
        const container = document.getElementById('criteriaList');
        
        if (!criteria || criteria.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    No hay criterios definidos para este proceso.
                    <button class="btn btn-primary btn-sm ms-2" onclick="showCriteriaModal()">
                        Crear Criterio
                    </button>
                </div>
            `;
            return;
        }
        
        const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);
        
        const html = `
            <div class="row mb-3">
                <div class="col-md-6">
                    <div class="alert ${totalWeight === 100 ? 'alert-success' : 'alert-warning'}">
                        <strong>Peso Total: ${totalWeight}%</strong>
                        ${totalWeight !== 100 ? ' (Debe sumar 100%)' : ' ✓'}
                    </div>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Criterio</th>
                            <th>Tipo</th>
                            <th>Peso (%)</th>
                            <th>Puntaje Máximo</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${criteria.map(criterion => `
                            <tr>
                                <td>
                                    <strong>${criterion.name}</strong>
                                    ${criterion.description ? `<br><small class="text-muted">${criterion.description}</small>` : ''}
                                </td>
                                <td>
                                    <span class="badge bg-${getCriteriaTypeColor(criterion.criteria_type)}">
                                        ${getCriteriaTypeLabel(criterion.criteria_type)}
                                    </span>
                                </td>
                                <td>${criterion.weight}%</td>
                                <td>${criterion.max_score}</td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="editCriteria(${criterion.id})">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="deleteCriteria(${criterion.id})">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading evaluation criteria:', error);
    }
}

async function loadProcessBids(processId) {
    try {
        const response = await fetch(`${API_BASE}/bids?process_id=${processId}`);
        const data = await response.json();
        
        const container = document.getElementById('evaluationList');
        
        if (!data.bids || data.bids.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    No hay ofertas para evaluar en este proceso.
                </div>
            `;
            return;
        }
        
        const html = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Proveedor</th>
                            <th>Monto</th>
                            <th>Puntaje Total</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.bids.map(bid => `
                            <tr>
                                <td>${bid.supplier_name}</td>
                                <td>${bid.bid_amount ? formatCurrency(bid.bid_amount) : '-'}</td>
                                <td>
                                    ${bid.total_score ? 
                                        `<span class="badge bg-success">${bid.total_score}</span>` : 
                                        '<span class="text-muted">Sin evaluar</span>'
                                    }
                                </td>
                                <td>
                                    <span class="badge status-${bid.status}">${bid.status}</span>
                                </td>
                                <td>
                                    <button class="btn btn-primary btn-sm" onclick="showEvaluationModal(${bid.id})">
                                        <i class="bi bi-clipboard-check"></i> Evaluar
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading process bids:', error);
    }
}

async function loadBidRanking(processId) {
    try {
        const response = await fetch(`${API_BASE}/evaluation/ranking/${processId}`);
        const rankings = await response.json();
        
        const container = document.getElementById('rankingList');
        
        if (!rankings || rankings.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    No hay ranking generado para este proceso.
                    <button class="btn btn-success btn-sm ms-2" onclick="generateRanking()">
                        Generar Ranking
                    </button>
                </div>
            `;
            return;
        }
        
        const html = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Posición</th>
                            <th>Proveedor</th>
                            <th>Monto</th>
                            <th>Puntaje Técnico</th>
                            <th>Puntaje Comercial</th>
                            <th>Puntaje Financiero</th>
                            <th>Puntaje Total</th>
                            <th>Recomendación</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rankings.map(ranking => `
                            <tr class="${ranking.ranking_position === 1 ? 'table-success' : ''}">
                                <td>
                                    <strong>${ranking.ranking_position}</strong>
                                    ${ranking.ranking_position === 1 ? '<i class="bi bi-trophy text-warning ms-1"></i>' : ''}
                                </td>
                                <td>${ranking.supplier_name}</td>
                                <td>${ranking.bid_amount ? formatCurrency(ranking.bid_amount) : '-'}</td>
                                <td>${ranking.technical_score || 0}</td>
                                <td>${ranking.commercial_score || 0}</td>
                                <td>${ranking.financial_score || 0}</td>
                                <td><strong>${ranking.weighted_total_score}</strong></td>
                                <td>
                                    <span class="badge bg-${getRecommendationColor(ranking.recommendation)}">
                                        ${getRecommendationLabel(ranking.recommendation)}
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading bid ranking:', error);
    }
}

function clearEvaluationData() {
    document.getElementById('criteriaList').innerHTML = '<p class="text-muted">Seleccione un proceso para ver los criterios</p>';
    document.getElementById('evaluationList').innerHTML = '<p class="text-muted">Seleccione un proceso para evaluar ofertas</p>';
    document.getElementById('rankingList').innerHTML = '<p class="text-muted">Seleccione un proceso para ver el ranking</p>';
    currentEvaluationProcess = null;
}

async function generateRanking() {
    if (!currentEvaluationProcess) {
        showAlert('Seleccione un proceso primero', 'warning');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/evaluation/ranking/${currentEvaluationProcess}/generate`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Ranking generado exitosamente', 'success');
            await loadBidRanking(currentEvaluationProcess);
        } else {
            showAlert('Error generando ranking: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al generar ranking', 'danger');
        console.error('Generate ranking error:', error);
    } finally {
        hideLoading();
    }
}

function getCriteriaTypeColor(type) {
    const colors = {
        'technical': 'primary',
        'commercial': 'success',
        'financial': 'warning'
    };
    return colors[type] || 'secondary';
}

function getCriteriaTypeLabel(type) {
    const labels = {
        'technical': 'Técnico',
        'commercial': 'Comercial',
        'financial': 'Financiero'
    };
    return labels[type] || type;
}

function getRecommendationColor(recommendation) {
    const colors = {
        'award': 'success',
        'conditional': 'warning',
        'reject': 'danger'
    };
    return colors[recommendation] || 'secondary';
}

function getRecommendationLabel(recommendation) {
    const labels = {
        'award': 'Adjudicar',
        'conditional': 'Condicional',
        'reject': 'Rechazar'
    };
    return labels[recommendation] || recommendation;
}

function showCriteriaModal() {
    if (!currentEvaluationProcess) {
        showAlert('Seleccione un proceso primero', 'warning');
        return;
    }
    
    // TODO: Implement criteria modal
    showAlert('Modal de criterios en desarrollo', 'info');
}

function showEvaluationModal(bidId) {
    // TODO: Implement evaluation modal
    showAlert('Modal de evaluación en desarrollo', 'info');
}


// Export Functions
async function exportProcessPDF(processId) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/export/process/${processId}/pdf`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `proceso_${processId}_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showAlert('PDF exportado exitosamente', 'success');
        } else {
            const error = await response.json();
            showAlert('Error exportando PDF: ' + error.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al exportar PDF', 'danger');
        console.error('Export PDF error:', error);
    } finally {
        hideLoading();
    }
}

async function exportProcessExcel(processId) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/export/process/${processId}/excel`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `proceso_${processId}_${new Date().toISOString().slice(0, 10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showAlert('Excel exportado exitosamente', 'success');
        } else {
            const error = await response.json();
            showAlert('Error exportando Excel: ' + error.error, 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión al exportar Excel', 'danger');
        console.error('Export Excel error:', error);
    } finally {
        hideLoading();
    }
}

function showExportModal(processId) {
    const modalHtml = `
        <div class="modal fade" id="exportModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Exportar Informe</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Seleccione el formato de exportación para el informe completo del proceso:</p>
                        <div class="d-grid gap-2">
                            <button class="btn btn-danger btn-lg" onclick="exportProcessPDF(${processId}); bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();">
                                <i class="bi bi-file-earmark-pdf"></i> Exportar como PDF
                            </button>
                            <button class="btn btn-success btn-lg" onclick="exportProcessExcel(${processId}); bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();">
                                <i class="bi bi-file-earmark-excel"></i> Exportar como Excel
                            </button>
                        </div>
                        <hr>
                        <small class="text-muted">
                            El informe incluirá información general, ofertas, ranking, criterios de evaluación y documentos asociados.
                        </small>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('exportModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('exportModal'));
    modal.show();
}


// Calendar Functions
let calendar = null;
let calendarFilters = {
    process_id: '',
    milestone_type: '',
    status: ''
};

async function loadCalendar() {
    try {
        // Load processes for filter
        await loadCalendarProcesses();
        
        // Initialize FullCalendar
        initializeCalendar();
        
        // Load upcoming and overdue milestones
        await loadUpcomingMilestones();
        await loadOverdueMilestones();
        
        // Update stats
        await updateCalendarStats();
    } catch (error) {
        showAlert('Error cargando calendario', 'danger');
        console.error('Calendar load error:', error);
    }
}

async function loadCalendarProcesses() {
    try {
        const response = await fetch(`${API_BASE}/processes`);
        const data = await response.json();
        
        if (response.ok) {
            const select = document.getElementById('calendarProcessFilter');
            select.innerHTML = '<option value="">Todos los procesos</option>';
            
            data.processes.forEach(process => {
                const option = document.createElement('option');
                option.value = process.id;
                option.textContent = `${process.process_number} - ${process.title}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading calendar processes:', error);
    }
}

function initializeCalendar() {
    const calendarEl = document.getElementById('calendar-container');
    
    if (calendar) {
        calendar.destroy();
    }
    
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        buttonText: {
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            list: 'Lista'
        },
        height: 'auto',
        events: function(fetchInfo, successCallback, failureCallback) {
            loadCalendarEvents(fetchInfo, successCallback, failureCallback);
        },
        eventClick: function(info) {
            showMilestoneDetails(info.event);
        },
        eventDidMount: function(info) {
            // Add tooltip
            info.el.setAttribute('title', info.event.extendedProps.description || '');
            
            // Add overdue styling
            if (info.event.extendedProps.is_overdue) {
                info.el.classList.add('overdue-event');
            }
        }
    });
    
    calendar.render();
}

async function loadCalendarEvents(fetchInfo, successCallback, failureCallback) {
    try {
        const params = new URLSearchParams({
            start: fetchInfo.startStr,
            end: fetchInfo.endStr,
            ...calendarFilters
        });
        
        // Remove empty filters
        Object.keys(calendarFilters).forEach(key => {
            if (!calendarFilters[key]) {
                params.delete(key);
            }
        });
        
        const response = await fetch(`${API_BASE}/calendar/events?${params}`);
        const events = await response.json();
        
        if (response.ok) {
            successCallback(events);
        } else {
            failureCallback(events.error || 'Error loading events');
        }
    } catch (error) {
        console.error('Error loading calendar events:', error);
        failureCallback(error.message);
    }
}

async function loadUpcomingMilestones() {
    try {
        const response = await fetch(`${API_BASE}/calendar/upcoming`);
        const milestones = await response.json();
        
        const container = document.getElementById('upcomingMilestones');
        const countBadge = document.getElementById('upcomingCount');
        
        countBadge.textContent = milestones.length;
        
        if (milestones.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay vencimientos próximos</p>';
            return;
        }
        
        const html = milestones.map(milestone => `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <div>
                    <h6 class="mb-1">${milestone.process_number}</h6>
                    <p class="mb-0 text-muted small">${milestone.description}</p>
                </div>
                <div class="text-end">
                    <span class="badge bg-${getMilestoneTypeColor(milestone.milestone_type)}">${getMilestoneTypeLabel(milestone.milestone_type)}</span>
                    <br>
                    <small class="text-muted">${formatDate(milestone.date)}</small>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading upcoming milestones:', error);
    }
}

async function loadOverdueMilestones() {
    try {
        const response = await fetch(`${API_BASE}/calendar/overdue`);
        const milestones = await response.json();
        
        const container = document.getElementById('overdueMilestones');
        const countBadge = document.getElementById('overdueCount');
        
        countBadge.textContent = milestones.length;
        
        if (milestones.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay hitos vencidos</p>';
            return;
        }
        
        const html = milestones.map(milestone => `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <div>
                    <h6 class="mb-1">${milestone.process_number}</h6>
                    <p class="mb-0 text-muted small">${milestone.description}</p>
                </div>
                <div class="text-end">
                    <span class="badge bg-${getMilestoneTypeColor(milestone.milestone_type)}">${getMilestoneTypeLabel(milestone.milestone_type)}</span>
                    <br>
                    <small class="text-danger">${formatDate(milestone.date)}</small>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading overdue milestones:', error);
    }
}

async function updateCalendarStats() {
    try {
        const response = await fetch(`${API_BASE}/calendar/stats`);
        const stats = await response.json();
        
        if (response.ok) {
            document.getElementById('upcomingCount').textContent = stats.upcoming_count;
            document.getElementById('overdueCount').textContent = stats.overdue_count;
        }
    } catch (error) {
        console.error('Error updating calendar stats:', error);
    }
}

function applyCalendarFilters() {
    calendarFilters.process_id = document.getElementById('calendarProcessFilter').value;
    calendarFilters.milestone_type = document.getElementById('calendarMilestoneFilter').value;
    calendarFilters.status = document.getElementById('calendarStatusFilter').value;
    
    if (calendar) {
        calendar.refetchEvents();
    }
    
    // Reload milestone lists with filters
    loadUpcomingMilestones();
    loadOverdueMilestones();
}

function refreshCalendar() {
    if (calendar) {
        calendar.refetchEvents();
    }
    
    loadUpcomingMilestones();
    loadOverdueMilestones();
    updateCalendarStats();
    
    showAlert('Calendario actualizado', 'success');
}

function showMilestoneDetails(event) {
    const props = event.extendedProps;
    
    const modalHtml = `
        <div class="modal fade" id="milestoneModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Detalles del Hito</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-sm-4"><strong>Proceso:</strong></div>
                            <div class="col-sm-8">${props.process_number}</div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-sm-4"><strong>Tipo de Hito:</strong></div>
                            <div class="col-sm-8">
                                <span class="badge bg-${getMilestoneTypeColor(props.milestone_type)}">
                                    ${getMilestoneTypeLabel(props.milestone_type)}
                                </span>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-sm-4"><strong>Fecha:</strong></div>
                            <div class="col-sm-8">${formatDate(event.startStr)}</div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-sm-4"><strong>Estado:</strong></div>
                            <div class="col-sm-8">
                                <span class="badge bg-${props.is_overdue ? 'danger' : 'success'}">
                                    ${props.is_overdue ? 'Vencido' : 'Activo'}
                                </span>
                            </div>
                        </div>
                        ${props.description ? `
                        <div class="row mt-2">
                            <div class="col-sm-4"><strong>Descripción:</strong></div>
                            <div class="col-sm-8">${props.description}</div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <button type="button" class="btn btn-primary" onclick="viewProcess(${props.process_id})">Ver Proceso</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('milestoneModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('milestoneModal'));
    modal.show();
}

function getMilestoneTypeColor(type) {
    const colors = {
        'start': 'primary',
        'end': 'danger',
        'award': 'success',
        'delivery': 'warning',
        'evaluation': 'info',
        'other': 'secondary'
    };
    return colors[type] || 'secondary';
}

function getMilestoneTypeLabel(type) {
    const labels = {
        'start': 'Inicio',
        'end': 'Fin',
        'award': 'Adjudicación',
        'delivery': 'Entrega',
        'evaluation': 'Evaluación',
        'other': 'Otro'
    };
    return labels[type] || 'Hito';
}

function viewProcess(processId) {
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('milestoneModal'));
    if (modal) {
        modal.hide();
    }
    
    // Switch to processes section and highlight the process
    showSection('processes');
    // TODO: Implement process highlighting/filtering
    showAlert(`Mostrando proceso ID: ${processId}`, 'info');
}

function showMilestoneModal() {
    // TODO: Implement milestone creation modal
    showAlert('Funcionalidad de creación de hitos en desarrollo', 'info');
}

