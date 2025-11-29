/**
 * ESA Helper - Main Application JavaScript
 */

// Note: expenseCategories and directPayCategories are loaded from Flask in index.html
// They are declared there via: const expenseCategories = {{ expense_categories | tojson }};

const fileLabels = {
    'receipt': 'Receipt/Payment Proof',
    'invoice': 'Invoice',
    'attestation': 'Instructor Attestation',
    'curriculum': 'Curriculum Document'
};

// State
let formData = {};
let selectedFiles = {};
let templates = [];
let vendors = [];

/**
 * Get today's date in local timezone as YYYY-MM-DD format
 */
function getLocalDateString() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Get student name from student ID
 */
function getStudentNameFromId(studentId) {
    if (!studentId || !studentsData) {
        return studentId;
    }
    const student = studentsData.find(s => s.id === studentId);
    return student ? student.name : studentId;
}

/**
 * Get vendor name from vendor ID
 */
async function getVendorNameFromId(vendorId) {
    if (!vendorId) {
        return '';
    }
    try {
        // Check if we have cached vendors data
        if (window.vendorsData) {
            const vendor = window.vendorsData.find(v => v.id === vendorId);
            if (vendor) {
                return vendor.name;
            }
        }
        // Fetch vendor info if not in cache
        const response = await fetch(`/api/vendors-detailed/${vendorId}`);
        if (response.ok) {
            const vendor = await response.json();
            return vendor.name || vendorId;
        }
    } catch (error) {
        console.warn(`Could not find vendor with ID: ${vendorId}`, error);
    }
    return vendorId;
}

/**
 * Auto-detect multi-page PDFs and split them
 * Returns true if splitting was triggered (file handled by this function)
 * Returns false if PDF should be handled normally (single page or error)
 */
function autoDetectAndSplitPdf(fileInput, fileType) {
    const file = fileInput.files[0];

    if (!file || !file.type.includes('pdf')) {
        return false;
    }

    console.log(`🔍 Detected PDF for splitting: ${file.name}`);

    // Create FormData for file upload
    const formData = new FormData();
    formData.append('file', file);

    // Send to split endpoint
    fetch('/api/pdf/split', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.files && data.files.length > 0) {
            console.log(`✓ PDF split into ${data.files.length} page(s)`);

            // Initialize selectedFiles[fileType] if needed
            if (!selectedFiles[fileType]) {
                selectedFiles[fileType] = [];
            } else if (!Array.isArray(selectedFiles[fileType])) {
                selectedFiles[fileType] = [selectedFiles[fileType]];
            }

            // Add all split files to selectedFiles
            data.files.forEach(splitFile => {
                console.log(`  Adding split file: ${splitFile.filename}`);
                selectedFiles[fileType].push({
                    name: splitFile.filename,
                    path: splitFile.path || '',
                    page: splitFile.page_num,
                    totalPages: splitFile.total_pages
                });
            });

            console.log(`  Total files in selectedFiles[${fileType}]:`, selectedFiles[fileType].length);
            console.log('  selectedFiles:', selectedFiles);

            // Update preview with all split files
            updateFilePreview(fileType);

            // Re-validate form
            validateForm();
        } else {
            console.warn('PDF split returned unexpected response:', data);
            // Fall back to adding original file
            addFileToSelectedFiles(file, fileType);
        }
    })
    .catch(error => {
        console.error('Error splitting PDF:', error);
        // Fall back to adding original file
        addFileToSelectedFiles(file, fileType);
    });

    // Return true to indicate we're handling this file
    return true;
}

/**
 * Helper function to add a file to selectedFiles (used as fallback in PDF splitting)
 */
function addFileToSelectedFiles(file, fileType) {
    if (!selectedFiles[fileType]) {
        selectedFiles[fileType] = [];
    } else if (!Array.isArray(selectedFiles[fileType])) {
        selectedFiles[fileType] = [selectedFiles[fileType]];
    }

    selectedFiles[fileType].push({
        name: file.name,
        path: file.path || '',
        size: file.size
    });

    console.log(`  Added file to selectedFiles[${fileType}]`);
    console.log('  selectedFiles:', selectedFiles);

    updateFilePreview(fileType);
    validateForm();
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    // Templates are loaded on-demand when student is selected
    loadVendors();
    checkCredentials();
    initializeLineItems();
});

/**
 * Get the appropriate category configuration based on request type
 */
function getCategoryConfig() {
    const requestType = document.getElementById('requestType').value;
    if (requestType === 'Direct Pay') {
        return directPayCategories;
    }
    return expenseCategories;
}

/**
 * Validate form - check if all required fields are filled
 */
function validateForm() {
    console.log('=== validateForm() called ===');
    console.log('Current selectedFiles state:', JSON.stringify(selectedFiles, null, 2));

    const student = document.getElementById('student').value;
    const requestType = document.getElementById('requestType').value;
    const storeName = document.getElementById('storeName').value;
    const amount = document.getElementById('amount').value;
    const category = document.getElementById('expenseCategory').value;

    // Check all required fields are filled
    // Amount needs special handling because 0 is falsy but we need amount > 0
    let isFormValid = student && requestType && storeName && (parseFloat(amount) > 0) && category;

    // For Direct Pay, vendor must have a classwallet_search_term configured
    if (isFormValid && requestType === 'Direct Pay' && vendorMissingSearchTerm) {
        console.log('⚠️ Direct Pay selected but vendor missing search term - blocking submission');
        isFormValid = false;
    }

    // Check if all required files are uploaded for the selected category
    const categoryConfig = getCategoryConfig();
    // Extract required_fields from the category config object
    const requiredFiles = categoryConfig[category]?.required_fields || [];
    // Convert field names to lowercase for comparison with selectedFiles keys
    const requiredFilesLower = requiredFiles.map(f => f.toLowerCase());
    const allFilesUploaded = requiredFilesLower.every(ft => {
        const hasFile = !!selectedFiles[ft];
        console.log(`    Checking if selectedFiles['${ft}'] exists:`, hasFile);
        return hasFile;
    });

    const submitBtn = document.getElementById('submitBtn');
    const isValid = isFormValid && allFilesUploaded;

    // Debug logging - always show state when validation called
    console.log('Form Validation Debug:');
    console.log('  Student Value:', JSON.stringify(student), student ? '✓ FILLED' : '✗ EMPTY');
    console.log('  RequestType Value:', JSON.stringify(requestType), requestType ? '✓ FILLED' : '✗ EMPTY');
    console.log('  StoreName Value:', JSON.stringify(storeName), storeName ? '✓ FILLED' : '✗ EMPTY');
    console.log('  Amount Value:', amount, amount > 0 ? `✓ VALID (${amount})` : `✗ INVALID (must be > 0, got ${amount})`);
    console.log('  Category Value:', JSON.stringify(category), category ? '✓ FILLED' : '✗ EMPTY');
    if (requestType === 'Direct Pay') {
        console.log('  Direct Pay Check:', vendorMissingSearchTerm ? '✗ VENDOR MISSING SEARCH TERM' : '✓ Vendor has search term');
    }
    console.log('  Form Fields Valid:', isFormValid);
    console.log('  Required Files for', JSON.stringify(category), ':', requiredFilesLower);
    console.log('  Uploaded Files:', Object.keys(selectedFiles).length > 0 ? selectedFiles : '(none)');
    console.log('  All Required Files Uploaded:', allFilesUploaded);
    console.log('  Overall Valid:', isValid);
    console.log('  Button Disabled:', !isValid, '(will be enabled when all conditions met)');

    // Enable/disable button based on validation
    submitBtn.disabled = !isValid;

    return isValid;
}

/**
 * Initialize form event listeners
 */
function initializeForm() {
    // Template selection
    document.getElementById('template').addEventListener('change', onTemplateSelected);

    // Student selection
    document.getElementById('student').addEventListener('change', function() {
        updateAvailableTemplates();
        autoFillInvoiceFields();
        validateForm();
    });

    // Request type toggle
    document.getElementById('requestType').addEventListener('change', function() {
        onRequestTypeChange();
        validateForm();
    });

    // Expense category change
    document.getElementById('expenseCategory').addEventListener('change', function() {
        onCategoryChange();
        validateForm();
    });

    // Store name and amount validation on input
    document.getElementById('storeName').addEventListener('input', validateForm);
    document.getElementById('amount').addEventListener('input', validateForm);

    // Clear the default "0" when user focuses on amount field
    const amountField = document.getElementById('amount');
    amountField.addEventListener('focus', function() {
        // If the field still has the default value of "0", clear it
        if (this.value === '0' || this.value === '') {
            this.value = '';
        } else {
            // Otherwise, select all so user can replace the entire value
            this.select();
        }
    });

    // Vendor selection auto-fills store name for Direct Pay
    const vendorSelect = document.getElementById('vendorSelect');
    if (vendorSelect) {
        vendorSelect.addEventListener('change', function() {
            handleVendorSelection(this.value);
        });
    }

    // PO Number generation
    document.getElementById('generatePoBtn').addEventListener('click', generatePoNumber);

    // Form submission
    document.getElementById('submitBtn').addEventListener('click', onSubmit);
    document.getElementById('clearBtn').addEventListener('click', clearForm);

    // Credentials
    document.getElementById('saveCredentialsBtn').addEventListener('click', saveCredentials);

    // Vendor management
    document.getElementById('saveVendorBtn').addEventListener('click', addVendor);

    // Confirmation
    document.getElementById('confirmSubmitBtn').addEventListener('click', confirmSubmit);

    // Reset button state when confirmation modal is dismissed (Cancel button or Close button)
    const confirmationModal = document.getElementById('confirmationModal');
    if (confirmationModal) {
        confirmationModal.addEventListener('hidden.bs.modal', function() {
            const confirmSubmitBtn = document.getElementById('confirmSubmitBtn');
            confirmSubmitBtn.disabled = false;
            confirmSubmitBtn.textContent = 'Submit to ClassWallet';
        });
    }

    // Generate initial PO
    generatePoNumber();

    // Initially disable the submit button until form is valid
    validateForm();
}

/**
 * Load all templates
 */
async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        templates = await response.json();
        updateAvailableTemplates();
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

/**
 * Load all vendors
 */
async function loadVendors() {
    try {
        const response = await fetch('/api/vendors');
        vendors = await response.json();
        updateVendorDropdown();
    } catch (error) {
        console.error('Error loading vendors:', error);
    }
}

/**
 * Check if credentials are configured
 */
async function checkCredentials() {
    try {
        const response = await fetch('/api/config/credentials');
        const data = await response.json();
        console.log('Credentials check response:', data);
        if (data.configured) {
            document.getElementById('credentialsAlert').style.display = 'none';
            console.log('✓ Credentials are configured - hiding alert');
        } else {
            console.log('✗ Credentials NOT configured - showing alert');
        }
    } catch (error) {
        console.error('Error checking credentials:', error);
    }
}

/**
 * Update available templates based on selected student
 */
async function updateAvailableTemplates() {
    const studentId = document.getElementById('student').value;
    const studentName = getStudentNameFromId(studentId);
    const templateSelect = document.getElementById('template');

    // Clear current options (except first placeholder)
    const placeholder = templateSelect.options[0];
    templateSelect.innerHTML = '';
    templateSelect.appendChild(placeholder);

    if (!studentId) {
        return; // No student selected
    }

    try {
        // Fetch templates for the selected student from API
        const response = await fetch(`/api/templates/${encodeURIComponent(studentId)}`);
        const studentTemplates = await response.json();

        // Store in global templates array for use in onTemplateSelected
        templates = studentTemplates;

        if (studentTemplates.length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${studentName}'s Templates`;
            studentTemplates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name || template.id;
                optgroup.appendChild(option);
            });
            templateSelect.appendChild(optgroup);
        }
    } catch (error) {
        console.error('Error loading templates for student:', error);
    }
}

/**
 * Handle template selection
 */
function onTemplateSelected(event) {
    const templateId = event.target.value;
    if (!templateId) return;

    // Find template in the current student's templates
    // (updateAvailableTemplates keeps this array in sync)
    const template = templates.find(t => t.id === templateId);
    if (template) {
        applyTemplate(template);
    }
}

/**
 * Apply template data to form fields
 */
async function applyTemplate(template) {
    // Resolve vendor_id to vendor name
    let vendorName = '';
    if (template.vendor_id) {
        vendorName = await getVendorNameFromId(template.vendor_id);
        // Validate vendor exists
        if (!vendorName || vendorName === template.vendor_id) {
            const confirmed = confirm(`Vendor "${template.vendor_id}" not found. Create it now?`);
            if (confirmed) {
                window.location.href = '/manage-vendors';
                return;
            }
        }
    } else if (template.store_name) {
        // Backward compatibility: support old store_name field
        vendorName = template.store_name;
    }

    // Set request type and category FIRST, before filling store name
    // This ensures the store name field is properly configured (read-only for Direct Pay, etc)
    const storeNameInput = document.getElementById('storeName');
    document.getElementById('requestType').value = template.request_type || '';
    document.getElementById('expenseCategory').value = template.expense_category || '';

    // Trigger category change to update required files
    onCategoryChange();

    // Trigger request type change to show/hide direct pay options
    // This must be called BEFORE setting the store name so the field is properly configured
    onRequestTypeChange();

    // Set the store name value - need to do this even if readOnly is set
    // Temporarily disable readOnly to set the value
    const wasReadOnly = storeNameInput.readOnly;
    storeNameInput.readOnly = false;
    storeNameInput.value = vendorName;
    storeNameInput.readOnly = wasReadOnly;

    // Also select vendor in the vendorSelect dropdown if this template has a vendor_id
    // Call this AFTER onRequestTypeChange() so the store name is set after the UI is configured
    if (template.vendor_id) {
        document.getElementById('vendorSelect').value = template.vendor_id;
        // Manually trigger vendor selection logic since programmatic value changes don't trigger change event
        handleVendorSelection(template.vendor_id);
    }

    if (template.amount) {
        document.getElementById('amount').value = template.amount;
    }

    // Pre-fill comment from template, replacing {yyyy-mm-dd} with today's date
    if (template.comment) {
        const dateStr = getLocalDateString();
        const comment = template.comment.replace('{yyyy-mm-dd}', dateStr);
        document.getElementById('comment').value = comment;
    }

    // Update invoice fields if invoice checkbox is enabled
    if (document.getElementById('generateInvoice').checked) {
        updateInvoiceFieldsFromTemplate(template);
    }

    // Pre-populate files from template if they exist
    if (template.files && typeof template.files === 'object') {
        // Clear old files from file types that the template will populate
        for (const fileType of Object.keys(template.files)) {
            // Normalize to lowercase for consistency with how files are stored
            const fileTypeLower = fileType.toLowerCase();
            delete selectedFiles[fileTypeLower];
            // Clear the file preview display
            const fieldId = `file_${fileTypeLower.replace(/[^a-z0-9]/g, '_')}`;
            const previewContainer = document.getElementById(`${fieldId}_preview`);
            if (previewContainer) {
                previewContainer.innerHTML = '';
            }
        }

        setTimeout(() => {
            populateFilesFromTemplate(template.files);
        }, 500); // Wait for category change to complete
    }

    // Validate form after template values are applied
    // This ensures the button is enabled if all conditions are met
    validateForm();
}

/**
 * Update invoice fields when template is applied
 */
async function updateInvoiceFieldsFromTemplate(template) {
    const student = document.getElementById('student').value;

    // Update vendor - resolve vendor_id to vendor name
    let vendorName = '';
    if (template.vendor_id) {
        vendorName = await getVendorNameFromId(template.vendor_id);
        // Also select in vendorSelect dropdown
        document.getElementById('vendorSelect').value = template.vendor_id;
        // Manually trigger vendor selection logic since programmatic value changes don't trigger change event
        handleVendorSelection(template.vendor_id);
    } else if (template.store_name) {
        // Backward compatibility
        vendorName = template.store_name;
    }
    document.getElementById('invoiceVendor').value = vendorName;

    // Update student - use full name, not ID
    document.getElementById('invoiceStudent').value = getStudentNameFromId(student) || '';

    // Update first line item with comment and amount
    const firstLineRow = document.querySelector('#invoiceLineItems .line-item-row');
    if (firstLineRow) {
        // Update description from comment
        if (template.comment) {
            const dateStr = getLocalDateString();
            const comment = template.comment.replace('{yyyy-mm-dd}', dateStr);
            firstLineRow.querySelector('.line-description').value = comment;
        }

        // Update unit price from amount
        if (template.amount) {
            firstLineRow.querySelector('.line-unit-price').value = template.amount;
        }

        // Recalculate totals
        updateInvoiceTotals();
    }

    // Set date to today
    document.getElementById('invoiceDate').value = getLocalDateString();

    // Quantity defaults to 1 (already set in HTML)
    // Tax rate stays at 0 unless vendor profile has different rate
}

/**
 * Store template file paths (folders, not files)
 */
let templateFilePaths = {};

/**
 * Populate files from template
 */
function populateFilesFromTemplate(files) {
    /**
     * Handle template file paths - can be either:
     * 1. Direct file paths (e.g., "/path/to/file.pdf") - automatically added to selectedFiles
     * 2. Directory paths (e.g., "/path/to/folder") - used by file browser for browsing
     *
     * IMPORTANT: File types are normalized to lowercase to match validation logic
     */

    const fileExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx'];

    for (const [fileType, filePath] of Object.entries(files)) {
        if (!filePath) continue;

        // Check if this is a direct file path (has file extension)
        const isDirectFile = fileExtensions.some(ext =>
            filePath.toLowerCase().endsWith(ext)
        );

        if (isDirectFile) {
            // This is a direct file path - add it to selectedFiles
            const fileName = filePath.split('/').pop(); // Extract filename from path

            // IMPORTANT: Normalize fileType to lowercase to match validation logic
            // This ensures selectedFiles['attestation'] is used, not selectedFiles['Attestation']
            const fileTypeLower = fileType.toLowerCase();

            // Initialize as array if not already
            if (!selectedFiles[fileTypeLower]) {
                selectedFiles[fileTypeLower] = [];
            } else if (!Array.isArray(selectedFiles[fileTypeLower])) {
                selectedFiles[fileTypeLower] = [selectedFiles[fileTypeLower]];
            }

            // Add the file
            selectedFiles[fileTypeLower].push({
                name: fileName,
                path: filePath,
                size: 0
            });

            console.log(`✓ Auto-loaded ${fileType} (stored as ${fileTypeLower}): ${fileName}`);
        } else {
            // This is a directory path - store for file browser
            // (file browser will use this as the starting location)
            // Normalize to lowercase for consistency
            const fileTypeLower = fileType.toLowerCase();
            if (!templateFilePaths) {
                templateFilePaths = {};
            }
            templateFilePaths[fileTypeLower] = filePath;
        }
    }

    // Update the file preview display for all file types that have files
    Object.keys(selectedFiles).forEach(fileType => {
        if (selectedFiles[fileType] && selectedFiles[fileType].length > 0) {
            updateFilePreview(fileType);
        }
    });

    // Validate form after files are populated
    validateForm();
}

/**
 * Handle request type change (Reimbursement vs Direct Pay)
 */
function onRequestTypeChange() {
    const requestType = document.getElementById('requestType').value;
    const directPayCard = document.getElementById('directPayCard');
    const storeNameInput = document.getElementById('storeName');
    const missingSearchTermWarning = document.getElementById('missingSearchTermWarning');

    if (requestType === 'Direct Pay') {
        directPayCard.style.display = 'block';
        // Keep field enabled so it can be auto-filled from vendor selection
        storeNameInput.disabled = false;
        storeNameInput.value = '';
        storeNameInput.placeholder = 'Will be filled from vendor selection';
        storeNameInput.readOnly = true;  // Make read-only instead of disabled
    } else {
        directPayCard.style.display = 'none';
        storeNameInput.disabled = false;
        storeNameInput.readOnly = false;  // Make editable for Reimbursement
        storeNameInput.placeholder = 'e.g., Ice Skating Instructor';

        // Clear Direct Pay specific state when switching away
        selectedVendorId = null;
        vendorMissingSearchTerm = false;
        if (missingSearchTermWarning) {
            missingSearchTermWarning.style.display = 'none';
        }
    }

    // Clear selected files since required files may have changed
    selectedFiles = {};

    // Re-render file upload UI if category is selected
    const category = document.getElementById('expenseCategory').value;
    if (category) {
        onCategoryChange();
    }

    validateForm();
}

/**
 * Handle expense category change
 */
function onCategoryChange() {
    const category = document.getElementById('expenseCategory').value;
    const container = document.getElementById('fileUploadContainer');

    if (!category) {
        container.innerHTML = '<p class="text-muted">Select an expense category to see required documents</p>';
        selectedFiles = {};
        return;
    }

    const categoryConfig = getCategoryConfig();
    const requiredFiles = categoryConfig[category]?.required_fields || [];
    const requiresCurriculum = requiredFiles.includes('Curriculum');

    let html = '';

    // Add curriculum generator section if curriculum is required
    if (requiresCurriculum) {
        html += `
            <div class="alert alert-info alert-dismissible fade show mb-4" role="alert">
                <strong>📚 Curriculum Document Required</strong><br>
                <small class="d-block mt-2 mb-3">This category requires a curriculum document. If you don't have one yet, you can generate it using ChatGPT with our Curriculum Generator tool.</small>
                <button type="button" class="btn btn-primary btn-sm" onclick="openCurriculumGenerator()">
                    📖 Generate Curriculum with ChatGPT
                </button>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }

    html += '<div class="row">';

    requiredFiles.forEach(fileType => {
        const fileTypeLower = fileType.toLowerCase();
        const label = fileLabels[fileTypeLower] || fileType;
        const fieldId = `file_${fileTypeLower.replace(/[^a-z0-9]/g, '_')}`;
        html += `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">${label} <span class="badge bg-danger">Required</span></h6>
                        <div class="mb-3">
                            <button type="button" class="btn btn-sm btn-outline-primary browse-btn" data-file-type="${fileTypeLower}">
                                📁 Browse Files
                            </button>
                        </div>
                        <div id="${fieldId}_preview" class="mt-2"></div>
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;

    // Attach event listeners to file inputs
    document.querySelectorAll('.file-input').forEach(input => {
        input.addEventListener('change', onFileSelected);
    });

    // Attach event listeners to browse buttons
    document.querySelectorAll('.browse-btn').forEach(btn => {
        btn.addEventListener('click', openFileBrowser);
    });
}

/**
 * Handle file selection
 */
function onFileSelected(event) {
    const fileType = event.target.dataset.fileType;
    const fileInput = event.target;
    const file = fileInput.files[0];

    console.log('=== onFileSelected DEBUG ===');
    console.log('  fileType from dataset:', fileType);
    console.log('  file:', file ? `${file.name} (${file.type})` : 'NO FILE');
    console.log('  autoDetectAndSplitPdf available?:', typeof autoDetectAndSplitPdf === 'function');

    if (file) {
        // Check if it's a PDF and automatically split if multi-page
        if (typeof autoDetectAndSplitPdf === 'function' && file.type.includes('pdf')) {
            console.log('  Detected PDF, calling autoDetectAndSplitPdf()...');
            if (autoDetectAndSplitPdf(fileInput, fileType)) {
                // PDF splitting was triggered, don't add file normally
                console.log('  autoDetectAndSplitPdf returned true, PDF splitting triggered');
                return;
            }
            console.log('  autoDetectAndSplitPdf returned false, continuing with normal file handling');
        }

        // Store as array for consistency with template files
        if (!selectedFiles[fileType]) {
            selectedFiles[fileType] = [];
        } else if (!Array.isArray(selectedFiles[fileType])) {
            selectedFiles[fileType] = [selectedFiles[fileType]];
        }

        // Add the file to the array
        selectedFiles[fileType].push({
            name: file.name,
            path: file.path || '',
            size: file.size
        });

        console.log(`  Added file to selectedFiles[${fileType}]`);
        console.log('  selectedFiles:', selectedFiles);

        // Update preview using the same function as template files
        updateFilePreview(fileType);

        // Re-validate form since files have changed
        validateForm();
    }
}

/**
 * Show file preview
 */
function showFilePreview(fileType, file) {
    const previewId = `file_${fileType.toLowerCase().replace(/[^a-z0-9]/g, '_')}_preview`;
    const previewContainer = document.getElementById(previewId);

    if (!previewContainer) return;

    const fileName = file.name;
    const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB

    previewContainer.innerHTML = `
        <div class="alert alert-success d-flex align-items-center" role="alert">
            <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Success:">
                <use xlink:href="#check-circle-fill"></use>
            </svg>
            <div>
                <strong>${fileName}</strong> (${fileSize} MB)
            </div>
        </div>
    `;
}

/**
 * Generate PO number
 */
async function generatePoNumber() {
    try {
        const response = await fetch('/api/po-number');
        const data = await response.json();
        document.getElementById('poNumber').value = data.po_number;
    } catch (error) {
        console.error('Error generating PO number:', error);
    }
}

/**
 * Update vendor dropdown
 */
function updateVendorDropdown() {
    const select = document.getElementById('vendorSelect');
    select.innerHTML = '<option value="">Search or select vendor...</option>';

    vendors.forEach(vendor => {
        const option = document.createElement('option');
        option.value = vendor.id;
        option.textContent = `${vendor.name}${vendor.location ? ' - ' + vendor.location : ''}`;
        select.appendChild(option);
    });
}

/**
 * Add vendor
 */
async function addVendor() {
    const vendorName = document.getElementById('vendorName').value;
    const vendorLocation = document.getElementById('vendorLocation').value;

    if (!vendorName) {
        alert('Please enter vendor name');
        return;
    }

    try {
        const response = await fetch('/api/vendors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: vendorName,
                location: vendorLocation
            })
        });

        if (response.ok) {
            // Reset form and reload vendors
            document.getElementById('addVendorForm').reset();
            await loadVendors();

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addVendorModal'));
            modal.hide();

            alert('Vendor added successfully!');
        }
    } catch (error) {
        console.error('Error adding vendor:', error);
        alert('Error adding vendor');
    }
}

/**
 * Save credentials
 */
async function saveCredentials() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email || !password) {
        alert('Please enter email and password');
        return;
    }

    try {
        const response = await fetch('/api/config/credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                password: password,
                student_a_id: 'student_a_id',
                student_b_id: 'student_b_id',
                student_c_id: 'student_c_id'
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            document.getElementById('credentialsAlert').style.display = 'none';
            document.getElementById('credentialsForm').reset();

            const modal = bootstrap.Modal.getInstance(document.getElementById('credentialsModal'));
            if (modal) {
                modal.hide();
            }

            alert('✓ Credentials saved successfully!');
        } else {
            alert('Error saving credentials: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving credentials:', error);
        alert('Error saving credentials: ' + error.message);
    }
}

/**
 * Handle form submission
 */
function onSubmit(event) {
    event.preventDefault();

    // Validate form
    const student = document.getElementById('student').value;
    const requestType = document.getElementById('requestType').value;
    const storeName = document.getElementById('storeName').value;
    const amount = document.getElementById('amount').value;
    const category = document.getElementById('expenseCategory').value;

    if (!student || !requestType || !storeName || !amount || !category) {
        alert('Please fill in all required fields');
        return;
    }

    // Validate required files
    const categoryConfig = getCategoryConfig();
    const requiredFiles = categoryConfig[category]?.required_fields || [];
    const requiredFilesLower = requiredFiles.map(f => f.toLowerCase());
    const missingFiles = requiredFilesLower.filter(ft => !selectedFiles[ft]);

    if (missingFiles.length > 0) {
        alert(`Please upload required files: ${missingFiles.join(', ')}`);
        return;
    }

    // Show confirmation
    showConfirmation();
}

/**
 * Show confirmation modal
 */
function showConfirmation() {
    const student = document.getElementById('student').value;
    const requestType = document.getElementById('requestType').value;
    const storeName = document.getElementById('storeName').value;
    const amount = document.getElementById('amount').value;
    const category = document.getElementById('expenseCategory').value;
    const poNumber = document.getElementById('poNumber').value;
    const comment = document.getElementById('comment').value;

    let html = `
        <div class="row mb-3">
            <div class="col-md-6">
                <p><strong>Student:</strong> ${student}</p>
                <p><strong>Request Type:</strong> ${requestType}</p>
                <p><strong>Store/Vendor:</strong> ${storeName}</p>
                <p><strong>Amount:</strong> $${parseFloat(amount).toFixed(2)}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Expense Category:</strong> ${category}</p>
                <p><strong>PO Number:</strong> ${poNumber}</p>
                <p><strong>Comment:</strong> ${comment}</p>
            </div>
        </div>

        <h6>Files to Upload:</h6>
        <ul>
    `;

    Object.entries(selectedFiles).forEach(([fileType, files]) => {
        // Handle both array and single file formats
        const fileArray = Array.isArray(files) ? files : [files];
        fileArray.forEach(file => {
            html += `<li>${fileLabels[fileType]}: <strong>${file.name}</strong></li>`;
        });
    });

    html += `
        </ul>

        <div class="alert alert-info">
            <strong>Note:</strong> This will open ClassWallet in your browser and automatically fill in the form.
            The automation will then upload the files and submit the request.
        </div>
    `;

    document.getElementById('confirmationContent').innerHTML = html;

    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();
}

/**
 * Confirm and submit
 */
async function confirmSubmit() {
    // Disable the submit button immediately to prevent duplicate submissions
    const confirmSubmitBtn = document.getElementById('confirmSubmitBtn');
    confirmSubmitBtn.disabled = true;
    const originalBtnText = confirmSubmitBtn.textContent;
    confirmSubmitBtn.textContent = 'Submitting...';

    const studentId = document.getElementById('student').value;
    const studentName = getStudentNameFromId(studentId);
    const requestType = document.getElementById('requestType').value;
    const storeName = document.getElementById('storeName').value;
    let amount = document.getElementById('amount').value;
    const category = document.getElementById('expenseCategory').value;
    const poNumber = document.getElementById('poNumber').value;
    const comment = document.getElementById('comment').value;

    // Ensure amount always has 2 decimal places (e.g., 100 becomes 100.00)
    amount = parseFloat(amount).toFixed(2);

    const submitData = {
        student: studentName,
        request_type: requestType,
        amount: amount,
        expense_category: category,
        po_number: poNumber,
        comment: comment,
        files: selectedFiles
    };

    // Handle store_name vs vendor_name based on request type
    if (requestType === 'Direct Pay') {
        // For Direct Pay, send vendor_name (populated from vendor selection)
        submitData.vendor_name = storeName;

        // Add vendor search term for Direct Pay if available
        if (selectedVendorId) {
            const vendor = vendors.find(v => v.id === selectedVendorId);
            if (vendor && vendor.classwallet_search_term) {
                submitData.classwallet_search_term = vendor.classwallet_search_term;
                console.log('Including search term in submission:', vendor.classwallet_search_term);
            }
        }
    } else {
        // For Reimbursement, send store_name (entered by user)
        submitData.store_name = storeName;
    }

    try {
        const response = await fetch('/api/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submitData)
        });

        const result = await response.json();

        if (response.ok) {
            console.log('Submission successful, response:', result);

            // Hide confirmation modal
            const confirmationModal = bootstrap.Modal.getInstance(document.getElementById('confirmationModal'));
            if (confirmationModal) {
                confirmationModal.hide();
            }

            // Show success modal
            document.getElementById('successPoNumber').textContent = result.po_number || poNumber;
            new bootstrap.Modal(document.getElementById('successModal')).show();

            // Re-enable button since submission is complete
            confirmSubmitBtn.disabled = false;
            confirmSubmitBtn.textContent = originalBtnText;

            // Refresh recent submissions (wait longer since ClassWallet automation may be running)
            if (typeof window.loadRecentSubmissions === 'function') {
                console.log('Scheduling submission history refresh...');
                // Wait longer (3 seconds) for ClassWallet automation to complete and log results
                setTimeout(() => {
                    console.log('Calling loadRecentSubmissions()...');
                    window.loadRecentSubmissions();
                }, 3000);
            } else {
                console.warn('loadRecentSubmissions function not available');
            }

            // Trigger ClassWallet automation in the background
            triggerClassWalletAutomation(submitData);
        } else {
            // Hide confirmation modal before showing error modal
            bootstrap.Modal.getInstance(document.getElementById('confirmationModal')).hide();

            // Show error modal with specific error code for context-aware suggestions
            const errorMessage = result.message || 'Unknown error occurred during submission';
            const errorCode = result.error_code || 'SUBMISSION_ERROR';
            showErrorModal(errorMessage, errorCode);

            // Re-enable button on error so user can try again
            confirmSubmitBtn.disabled = false;
            confirmSubmitBtn.textContent = originalBtnText;
        }
    } catch (error) {
        console.error('Error submitting form:', error);

        // Hide confirmation modal before showing error modal
        const confirmationModal = bootstrap.Modal.getInstance(document.getElementById('confirmationModal'));
        if (confirmationModal) {
            confirmationModal.hide();
        }

        // Show error modal with generic error
        showErrorModal(
            'Network error: ' + (error.message || 'Could not reach the server'),
            'NETWORK_ERROR'
        );

        // Re-enable button on error so user can try again
        confirmSubmitBtn.disabled = false;
        confirmSubmitBtn.textContent = originalBtnText;
    }
}

/**
 * Trigger ClassWallet automation (placeholder)
 */
function triggerClassWalletAutomation(submitData) {
    console.log('Triggering ClassWallet automation with:', submitData);
    // TODO: Call backend endpoint to start ClassWallet automation
    // This should use Selenium to automate the submission process
}

/**
 * Clear form
 */
function clearForm(event) {
    event.preventDefault();
    document.getElementById('reimbursementForm').reset();
    selectedFiles = {};
    document.getElementById('fileUploadContainer').innerHTML = '<p class="text-muted">Select an expense category to see required documents</p>';
    generatePoNumber();

    // Reset the confirm submit button state if it was disabled
    const confirmSubmitBtn = document.getElementById('confirmSubmitBtn');
    if (confirmSubmitBtn) {
        confirmSubmitBtn.disabled = false;
        confirmSubmitBtn.textContent = 'Submit to ClassWallet';
    }
}

/**
 * Selected Vendor State (for Direct Pay search term)
 */
let selectedVendorId = null;
let vendorMissingSearchTerm = false;  // Flag to track if vendor is missing search term

/**
 * Handle vendor selection - updates store name, search term display, and validation
 * This function is called both from the change event listener and from template application
 */
function handleVendorSelection(vendorId) {
    if (vendorId) {
        // Find the vendor and get its name
        const vendor = vendors.find(v => v.id === vendorId);
        if (vendor) {
            document.getElementById('storeName').value = vendor.name;
            selectedVendorId = vendorId;  // Store vendor ID for later use
            console.log('Vendor selected:', vendorId, 'Search term:', vendor.classwallet_search_term);

            // Show and populate the search term field
            const searchTermContainer = document.getElementById('searchTermContainer');
            const searchTermDisplay = document.getElementById('classwalletSearchTermDisplay');
            const missingSearchTermWarning = document.getElementById('missingSearchTermWarning');

            if (searchTermContainer && searchTermDisplay && missingSearchTermWarning) {
                if (vendor.classwallet_search_term) {
                    searchTermDisplay.value = vendor.classwallet_search_term;
                    searchTermContainer.style.display = 'block';
                    missingSearchTermWarning.style.display = 'none';
                    vendorMissingSearchTerm = false;
                    console.log('✓ Vendor has search term configured');
                } else {
                    searchTermContainer.style.display = 'none';
                    missingSearchTermWarning.style.display = 'block';
                    vendorMissingSearchTerm = true;
                    console.log('⚠️ Vendor is missing search term - form submission will be blocked');
                }
            }

            validateForm();
        }
    } else {
        selectedVendorId = null;
        vendorMissingSearchTerm = false;
        // Hide the search term field when vendor is deselected
        const searchTermContainer = document.getElementById('searchTermContainer');
        const missingSearchTermWarning = document.getElementById('missingSearchTermWarning');
        if (searchTermContainer) {
            searchTermContainer.style.display = 'none';
        }
        if (missingSearchTermWarning) {
            missingSearchTermWarning.style.display = 'none';
        }
    }
}

/**
 * File Browser State
 */
let currentFileBrowserState = {
    fileType: null,
    currentPath: null
};

// Get student-specific base path
function getStudentBasePath() {
    // Get the student's configured folder path from their profile
    const studentId = document.getElementById('student').value;

    if (!studentId || !studentsData) {
        return '';
    }

    const student = studentsData.find(s => s.id === studentId);
    if (student && student.folder) {
        // Use the student's configured folder path
        return student.folder;
    }

    // Fallback: placeholder path (should not reach here if student is properly configured)
    console.warn(`No folder path configured for student: ${studentId}`);
    return `/path/to/esa/${studentId.toLowerCase()}`;
}

/**
 * Open file browser modal
 * Can be called two ways:
 * 1. From event listener: openFileBrowser(event) - gets fileType from event.target.dataset.fileType
 * 2. From onclick handler: openFileBrowser('receipt') - fileType passed directly as string
 */
function openFileBrowser(eventOrFileType) {
    let fileType;

    // Determine if we received an event object or a string
    if (typeof eventOrFileType === 'string') {
        // Called from onclick handler with fileType string
        fileType = eventOrFileType;
    } else if (eventOrFileType && eventOrFileType.target) {
        // Called from event listener with event object
        fileType = eventOrFileType.target.dataset.fileType;
    } else {
        console.error('openFileBrowser: Invalid parameter - expected event or string', eventOrFileType);
        return;
    }

    if (!fileType) {
        console.error('openFileBrowser: fileType could not be determined');
        return;
    }

    // Normalize fileType to lowercase for consistency
    const fileTypeLower = fileType.toLowerCase();
    currentFileBrowserState.fileType = fileTypeLower;

    // Check if template has a custom path for this file type
    let startPath = templateFilePaths[fileTypeLower] || getStudentBasePath();
    currentFileBrowserState.currentPath = startPath;

    // Open modal
    const modal = new bootstrap.Modal(document.getElementById('fileBrowserModal'));
    modal.show();

    // Load files for this path
    loadFilesForPath(startPath);
}

/**
 * Load files for a given path
 */
async function loadFilesForPath(path) {
    try {
        document.getElementById('fileList').innerHTML = '<p class="text-muted">Loading...</p>';
        document.getElementById('currentPath').value = path;

        const response = await fetch('/api/browser/list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load files');
        }

        currentFileBrowserState.currentPath = data.path;
        document.getElementById('currentPath').value = data.path;

        let html = '';

        // Add folders
        if (data.folders && data.folders.length > 0) {
            html += '<div class="mb-2"><strong>Folders:</strong></div>';
            data.folders.forEach(folder => {
                html += `
                    <div class="list-group-item cursor-pointer d-flex justify-content-between align-items-center" style="cursor: pointer;" onclick="loadFilesForPath('${folder.path}')">
                        <span>
                            <i class="bi bi-folder"></i> ${folder.name}
                        </span>
                        <small class="text-muted">→</small>
                    </div>
                `;
            });
            html += '<hr>';
        }

        // Add files
        if (data.files && data.files.length > 0) {
            html += '<div class="mb-2"><strong>Files:</strong></div>';
            data.files.forEach(file => {
                html += `
                    <div class="list-group-item d-flex justify-content-between align-items-center" style="cursor: pointer;" onclick="selectFile('${file.path}', '${file.name}')">
                        <span>
                            <i class="bi bi-file"></i> ${file.name}
                        </span>
                        <small class="text-muted">${file.ext}</small>
                    </div>
                `;
            });
        } else if (!data.folders || data.folders.length === 0) {
            html += '<p class="text-muted">No files or folders found</p>';
        }

        document.getElementById('fileList').innerHTML = html;

    } catch (error) {
        console.error('Error loading files:', error);
        document.getElementById('fileList').innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
    }
}

/**
 * Select a file from browser
 */
function selectFile(filePath, fileName) {
    const fileType = currentFileBrowserState.fileType;
    // Ensure fileType is lowercase for consistency
    const fileTypeLower = fileType.toLowerCase();

    // Check if it's a PDF and try to split it
    if (fileName.toLowerCase().endsWith('.pdf')) {
        console.log(`🔍 PDF selected from file browser: ${fileName}`);
        console.log(`   Path: ${filePath}`);

        // Send to backend to check if it's multi-page and split if needed
        fetch('/api/pdf/split-by-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.files && data.files.length > 0) {
                console.log(`✓ PDF processed: ${data.files.length} file(s)`);

                // Initialize as array if not already
                if (!selectedFiles[fileTypeLower]) {
                    selectedFiles[fileTypeLower] = [];
                } else if (!Array.isArray(selectedFiles[fileTypeLower])) {
                    selectedFiles[fileTypeLower] = [selectedFiles[fileTypeLower]];
                }

                // Add all split/processed files
                data.files.forEach(file => {
                    console.log(`  Adding: ${file.filename}`);
                    selectedFiles[fileTypeLower].push({
                        name: file.filename,
                        path: file.path,
                        size: 0,
                        page: file.page_num,
                        totalPages: file.total_pages
                    });
                });

                console.log(`  Total ${fileTypeLower} files: ${selectedFiles[fileTypeLower].length}`);

                // Update form display and validate
                updateFilePreview(fileTypeLower);
                validateForm();

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('fileBrowserModal'));
                if (modal) {
                    modal.hide();
                }
            } else {
                // If split endpoint failed, fall back to adding original file
                console.warn('PDF split failed, using original file:', data);
                addFileDirectly(filePath, fileName, fileTypeLower);
            }
        })
        .catch(error => {
            console.error('Error splitting PDF:', error);
            // Fall back to adding original file on error
            addFileDirectly(filePath, fileName, fileTypeLower);
        });
    } else {
        // Not a PDF, add directly
        addFileDirectly(filePath, fileName, fileTypeLower);
    }
}

/**
 * Helper function to add a file directly (used as fallback when PDF splitting isn't needed)
 */
function addFileDirectly(filePath, fileName, fileTypeLower) {
    // Initialize as array if not already
    if (!selectedFiles[fileTypeLower]) {
        selectedFiles[fileTypeLower] = [];
    } else if (!Array.isArray(selectedFiles[fileTypeLower])) {
        // Convert old format to array format
        selectedFiles[fileTypeLower] = [selectedFiles[fileTypeLower]];
    }

    // Add the new file to the array
    selectedFiles[fileTypeLower].push({
        name: fileName,
        path: filePath,
        size: 0
    });

    // Update form display
    updateFilePreview(fileTypeLower);

    // Validate form since files have changed
    validateForm();

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('fileBrowserModal'));
    if (modal) {
        modal.hide();
    }
}

/**
 * Remove a file from the selected files
 */
function removeFile(fileType, index) {
    // Normalize to lowercase for consistency
    const fileTypeLower = fileType.toLowerCase();
    if (Array.isArray(selectedFiles[fileTypeLower])) {
        selectedFiles[fileTypeLower].splice(index, 1);
        if (selectedFiles[fileTypeLower].length === 0) {
            delete selectedFiles[fileTypeLower];
        }
        updateFilePreview(fileTypeLower);
        // Validate form since files have changed
        validateForm();
    }
}

/**
 * Update the file preview display for a file type
 */
function updateFilePreview(fileType) {
    // Normalize to lowercase for consistency
    const fileTypeLower = fileType.toLowerCase();
    const fieldId = `file_${fileTypeLower.replace(/[^a-z0-9]/g, '_')}`;
    const previewContainer = document.getElementById(`${fieldId}_preview`);

    if (!previewContainer) return;

    // Look up files using lowercase key
    const files = selectedFiles[fileTypeLower];

    if (!files || files.length === 0) {
        previewContainer.innerHTML = '';
        return;
    }

    // Convert single file object to array for backward compatibility
    const fileList = Array.isArray(files) ? files : [files];

    let html = '<div class="file-selection-list">';

    fileList.forEach((file, index) => {
        html += `
            <div class="alert alert-success d-flex align-items-center justify-content-between mb-2" role="alert">
                <div class="d-flex align-items-center" style="flex: 1;">
                    <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Success:">
                        <use xlink:href="#check-circle-fill"></use>
                    </svg>
                    <div style="min-width: 0;">
                        <strong>${file.name}</strong>
                        <br>
                        <small class="text-muted" style="word-break: break-all;">${file.path}</small>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger flex-shrink-0 ms-2"
                        onclick="removeFile('${fileTypeLower}', ${index})"
                        title="Remove this file">
                    ✕ Remove
                </button>
            </div>
        `;
    });

    html += '</div>';

    // Add button to add more files
    html += `
        <button type="button" class="btn btn-sm btn-outline-primary mt-2"
                onclick="openFileBrowser('${fileTypeLower}')"
                title="Add another file">
            + Add Another ${fileType}
        </button>
    `;

    previewContainer.innerHTML = html;
}

/**
 * Navigate to path from input
 */
function setupFileBrowserEvents() {
    document.getElementById('navigateBtn')?.addEventListener('click', () => {
        const path = document.getElementById('pathInput').value;
        if (path) {
            loadFilesForPath(path);
        }
    });

    document.getElementById('goUpBtn')?.addEventListener('click', () => {
        const path = currentFileBrowserState.currentPath;
        if (path && path !== '/') {
            const parent = path.substring(0, path.lastIndexOf('/'));
            loadFilesForPath(parent || '/');
        }
    });
}

// Initialize file browser events when modal is shown
document.getElementById('fileBrowserModal')?.addEventListener('show.bs.modal', setupFileBrowserEvents);

/**
 * =====================================================================
 * INVOICE GENERATION FEATURE
 * =====================================================================
 */

// Invoice state
let invoiceData = {
    vendor: null,
    student: null,
    excelPath: null,
    pdfPath: null
};

/**
 * Initialize invoice event listeners
 */
function initializeInvoiceFeature() {
    // Invoice checkbox toggle
    document.getElementById('generateInvoice')?.addEventListener('change', (e) => {
        document.getElementById('invoiceSection').style.display = e.target.checked ? 'block' : 'none';
        if (e.target.checked) {
            autoFillInvoiceFields();
        }
    });

    // Generate invoice button
    document.getElementById('generateInvoiceBtn')?.addEventListener('click', generateInvoice);

    // Edit vendor/student buttons
    document.getElementById('saveVendorProfileBtn')?.addEventListener('click', saveVendorProfile);
    document.getElementById('applyVendorBtn')?.addEventListener('click', applyVendorChanges);
    document.getElementById('saveStudentProfileBtn')?.addEventListener('click', saveStudentProfile);
    document.getElementById('applyStudentBtn')?.addEventListener('click', applyStudentChanges);

    // Continue button in preview modal
    document.getElementById('continueInvoiceBtn')?.addEventListener('click', continueToFileUpload);
}

/**
 * Auto-fill invoice fields from form data
 */
async function autoFillInvoiceFields() {
    const student = document.getElementById('student').value;
    const storeName = document.getElementById('storeName').value;
    const amount = document.getElementById('amount').value;
    const poNumber = document.getElementById('poNumber').value;
    const comment = document.getElementById('comment').value;

    // Set invoice fields
    document.getElementById('invoiceVendor').value = storeName;
    document.getElementById('invoiceStudent').value = getStudentNameFromId(student);
    document.getElementById('invoiceNumber').value = poNumber || generatePoNumber();

    // Set date to today
    document.getElementById('invoiceDate').value = getLocalDateString();

    // Fill first line item with comment and amount
    const firstLineRow = document.querySelector('#invoiceLineItems .line-item-row');
    if (firstLineRow) {
        firstLineRow.querySelector('.line-description').value = comment;
        firstLineRow.querySelector('.line-unit-price').value = amount || 0;
        // Quantity already defaults to 1
        updateInvoiceTotals();
    }

    // Load vendor profile to populate tax rate (and other fields)
    if (storeName) {
        await loadVendorProfile(storeName);
    }
}

/**
 * Load vendor profile into edit modal
 */
async function loadVendorProfile(vendorName) {
    try {
        // Try to find vendor in system
        const allVendors = await fetch('/api/vendors-detailed').then(r => r.json());

        // Try exact match first
        let vendor = allVendors.find(v => v.name.toLowerCase() === vendorName.toLowerCase());

        // If no exact match, try first name match (e.g., "Ice" matches "Ice Skating Rink")
        if (!vendor) {
            vendor = allVendors.find(v =>
                v.name.toLowerCase().split()[0] === vendorName.toLowerCase() ||
                v.name.toLowerCase().startsWith(vendorName.toLowerCase())
            );
        }

        if (vendor) {
            invoiceData.vendor = vendor;
            document.getElementById('editVendorName').value = vendor.name;
            document.getElementById('editVendorBusinessName').value = vendor.business_name;
            document.getElementById('editVendorAddress1').value = vendor.address_line_1;
            document.getElementById('editVendorAddress2').value = vendor.address_line_2;
            document.getElementById('editVendorPhone').value = vendor.phone || '';
            document.getElementById('editVendorEmail').value = vendor.email || '';
            document.getElementById('editVendorTaxRate').value = vendor.tax_rate || 0;

            // Auto-populate invoice tax rate from vendor profile
            // Note: vendor.tax_rate is stored as decimal (0.02 = 2%), but field expects percentage (2 = 2%)
            const invoiceTaxRateField = document.getElementById('invoiceTaxRate');
            if (invoiceTaxRateField) {
                const taxRatePercentage = (vendor.tax_rate || 0) * 100;
                invoiceTaxRateField.value = taxRatePercentage;
                console.log(`✓ Auto-populated invoice tax rate: ${taxRatePercentage}%`);
                // Recalculate totals with new tax rate
                if (typeof updateInvoiceTotals === 'function') {
                    updateInvoiceTotals();
                }
            }
        } else {
            // Create temporary vendor from form data
            invoiceData.vendor = {
                id: vendorName.toLowerCase().replace(/\s+/g, '_'),
                name: vendorName,
                business_name: vendorName,
                address_line_1: '',
                address_line_2: '',
                phone: '',
                email: '',
                tax_rate: 0
            };

            document.getElementById('editVendorName').value = vendorName;
            document.getElementById('editVendorBusinessName').value = vendorName;
            document.getElementById('editVendorAddress1').value = '';
            document.getElementById('editVendorAddress2').value = '';
            document.getElementById('editVendorPhone').value = '';
            document.getElementById('editVendorEmail').value = '';
            document.getElementById('editVendorTaxRate').value = 0;

            // Clear invoice tax rate for unknown vendors
            const invoiceTaxRateField = document.getElementById('invoiceTaxRate');
            if (invoiceTaxRateField) {
                invoiceTaxRateField.value = 0;
                console.log('Unknown vendor - cleared invoice tax rate to 0%');
                if (typeof updateInvoiceTotals === 'function') {
                    updateInvoiceTotals();
                }
            }
        }
    } catch (error) {
        console.error('Error loading vendor profile:', error);
    }
}

/**
 * Load student profile into edit modal
 */
async function loadStudentProfile(studentName) {
    try {
        const allStudents = await fetch('/api/students-detailed').then(r => r.json());

        // Try exact match first
        let student = allStudents.find(s => s.name.toLowerCase() === studentName.toLowerCase());

        // If no exact match, try first name match (e.g., "Student" matches "Student One")
        if (!student) {
            student = allStudents.find(s =>
                s.name.toLowerCase().split()[0] === studentName.toLowerCase() ||
                s.name.toLowerCase().startsWith(studentName.toLowerCase())
            );
        }

        if (student) {
            invoiceData.student = student;
            document.getElementById('editStudentName').value = student.name;
            document.getElementById('editStudentAddress1').value = student.address_line_1;
            document.getElementById('editStudentAddress2').value = student.address_line_2;
        } else {
            // No default student info if not found
            invoiceData.student = {
                id: studentName.toLowerCase(),
                name: studentName,
                address_line_1: '',
                address_line_2: ''
            };

            document.getElementById('editStudentName').value = studentName;
            document.getElementById('editStudentAddress1').value = '';
            document.getElementById('editStudentAddress2').value = '';
        }
    } catch (error) {
        console.error('Error loading student profile:', error);
    }
}

/**
 * Save vendor profile permanently
 */
async function saveVendorProfile() {
    try {
        const vendorData = {
            id: invoiceData.vendor.id,
            name: document.getElementById('editVendorName').value,
            business_name: document.getElementById('editVendorBusinessName').value,
            address_line_1: document.getElementById('editVendorAddress1').value,
            address_line_2: document.getElementById('editVendorAddress2').value,
            phone: document.getElementById('editVendorPhone').value,
            email: document.getElementById('editVendorEmail').value,
            tax_rate: parseFloat(document.getElementById('editVendorTaxRate').value) / 100
        };

        const response = await fetch('/api/vendors-detailed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(vendorData)
        });

        if (response.ok) {
            alert('Vendor profile saved!');
            applyVendorChanges();
        } else {
            alert('Error saving vendor profile');
        }
    } catch (error) {
        console.error('Error saving vendor:', error);
        alert('Error saving vendor profile');
    }
}

/**
 * Apply vendor changes to this invoice
 */
function applyVendorChanges() {
    invoiceData.vendor = {
        id: invoiceData.vendor.id,
        name: document.getElementById('editVendorName').value,
        business_name: document.getElementById('editVendorBusinessName').value,
        address_line_1: document.getElementById('editVendorAddress1').value,
        address_line_2: document.getElementById('editVendorAddress2').value,
        phone: document.getElementById('editVendorPhone').value,
        email: document.getElementById('editVendorEmail').value,
        tax_rate: parseFloat(document.getElementById('editVendorTaxRate').value) / 100
    };

    document.getElementById('invoiceVendor').value = invoiceData.vendor.name;
}

/**
 * Save student profile permanently
 */
async function saveStudentProfile() {
    try {
        const studentData = {
            id: invoiceData.student.id,
            name: document.getElementById('editStudentName').value,
            address_line_1: document.getElementById('editStudentAddress1').value,
            address_line_2: document.getElementById('editStudentAddress2').value,
            folder: invoiceData.student.folder || ''
        };

        const response = await fetch('/api/students-detailed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(studentData)
        });

        if (response.ok) {
            alert('Student profile saved!');
            applyStudentChanges();
        } else {
            alert('Error saving student profile');
        }
    } catch (error) {
        console.error('Error saving student:', error);
        alert('Error saving student profile');
    }
}

/**
 * Apply student changes to this invoice
 */
function applyStudentChanges() {
    invoiceData.student = {
        id: invoiceData.student.id,
        name: document.getElementById('editStudentName').value,
        address_line_1: document.getElementById('editStudentAddress1').value,
        address_line_2: document.getElementById('editStudentAddress2').value,
        folder: invoiceData.student.folder
    };

    document.getElementById('invoiceStudent').value = invoiceData.student.name;
}

/**
 * Generate invoice
 */
async function generateInvoice() {
    try {
        // Save current tax rate in case user has manually customized it
        const userCustomTaxRate = document.getElementById('invoiceTaxRate').value;

        // Load profiles first
        await loadVendorProfile(document.getElementById('invoiceVendor').value);
        await loadStudentProfile(document.getElementById('invoiceStudent').value);

        // Restore user's custom tax rate if they had changed it from the vendor default
        document.getElementById('invoiceTaxRate').value = userCustomTaxRate;
        console.log(`✓ Preserved user's custom tax rate: ${userCustomTaxRate}%`);

        // Recalculate totals with the restored tax rate
        updateInvoiceTotals();

        // Validate required fields
        const invoiceNumber = document.getElementById('invoiceNumber').value;
        const invoiceDate = document.getElementById('invoiceDate').value;
        const lineItems = getLineItemsFromForm();

        if (!invoiceNumber || !invoiceDate || lineItems.length === 0) {
            alert('Please fill in invoice number, date, and at least one line item');
            return;
        }

        // Show loading status
        const statusDiv = document.getElementById('invoiceStatus');
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<strong>Generating invoice...</strong>';
        statusDiv.className = 'alert alert-info';

        // Prepare request data
        // Use student ID (from form), not the display name
        const studentId = document.getElementById('student').value;
        // Use business_name if available, otherwise use vendor name
        const displayBusinessName = invoiceData.vendor.business_name || invoiceData.vendor.name || '';
        const requestData = {
            student: studentId,
            vendor_name: document.getElementById('invoiceVendor').value,
            invoice_number: invoiceNumber,
            date: invoiceDate,
            line_items: lineItems,
            tax_rate: parseFloat(document.getElementById('invoiceTaxRate').value) / 100,
            vendor_business_name: displayBusinessName,
            vendor_address_1: invoiceData.vendor.address_line_1,
            vendor_address_2: invoiceData.vendor.address_line_2,
            vendor_phone: invoiceData.vendor.phone,
            vendor_email: invoiceData.vendor.email
        };

        // Call API
        const response = await fetch('/api/invoice/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (result.success) {
            // Prepare data for preview with all form fields and file paths
            const previewData = {
                ...requestData,  // Include all form data
                student: getStudentNameFromId(requestData.student), // Use full name for display
                excelPath: result.excel_path,
                pdfPath: result.pdf_path,
                vendor_name: requestData.vendor_name,
                vendor_business_name: requestData.vendor_business_name
            };

            // Show success status
            statusDiv.innerHTML = '<strong>✓ Invoice generated successfully!</strong>';
            statusDiv.className = 'alert alert-success';

            // Show preview modal with complete data
            showInvoicePreview(previewData);

            // Auto-populate the Amount field with the invoice total
            const totalAmount = parseFloat(document.getElementById('totalAmount').textContent) || 0;
            if (totalAmount > 0) {
                document.getElementById('amount').value = totalAmount.toFixed(2);
                console.log(`✓ Auto-populated Amount field with invoice total: $${totalAmount.toFixed(2)}`);
            }

            // Add invoice file to selectedFiles if PDF was generated
            if (result.pdf_path) {
                // Initialize as array if not already (use lowercase 'invoice' for consistency)
                if (!selectedFiles['invoice']) {
                    selectedFiles['invoice'] = [];
                } else if (!Array.isArray(selectedFiles['invoice'])) {
                    selectedFiles['invoice'] = [selectedFiles['invoice']];
                }

                // Add the PDF to the array
                selectedFiles['invoice'].push({
                    name: result.pdf_path.split('/').pop(),
                    path: result.pdf_path,
                    size: 0
                });

                // Update the file preview to show the newly added invoice
                updateFilePreview('invoice');
                console.log(`✓ Added generated invoice PDF to selectedFiles and updated preview`);

                // Re-validate form now that invoice file has been added
                validateForm();
            }
        } else {
            statusDiv.innerHTML = `<strong>Error:</strong> ${result.message}`;
            statusDiv.className = 'alert alert-danger';
        }

    } catch (error) {
        console.error('Error generating invoice:', error);
        const statusDiv = document.getElementById('invoiceStatus');
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
        statusDiv.className = 'alert alert-danger';
    }
}

/**
 * =====================================================================
 * LINE ITEM MANAGEMENT
 * =====================================================================
 */

/**
 * Add a new line item row to the invoice table
 */
function addLineItem() {
    const tbody = document.getElementById('invoiceLineItems');
    const newRow = document.createElement('tr');
    newRow.className = 'line-item-row';
    newRow.innerHTML = `
        <td><input type="text" class="form-control form-control-sm line-description" placeholder="e.g., Ice skating lesson"></td>
        <td><input type="number" class="form-control form-control-sm line-quantity" value="1" min="1" step="1" onchange="updateInvoiceTotals()"></td>
        <td><input type="number" class="form-control form-control-sm line-unit-price" step="0.01" min="0" onchange="updateInvoiceTotals()"></td>
        <td><input type="number" class="form-control form-control-sm line-total" readonly style="background-color: #f0f0f0;"></td>
        <td><button type="button" class="btn btn-sm btn-outline-danger remove-line-item" onclick="removeLineItem(this)">×</button></td>
    `;
    tbody.appendChild(newRow);
    // Add change listeners to new inputs
    newRow.querySelectorAll('.line-quantity, .line-unit-price').forEach(input => {
        input.addEventListener('change', updateInvoiceTotals);
    });
    updateInvoiceTotals();
}

/**
 * Remove a line item row
 */
function removeLineItem(button) {
    const row = button.closest('tr');
    const tbody = document.getElementById('invoiceLineItems');
    // Only allow removal if there's more than one row
    if (tbody.querySelectorAll('tr').length > 1) {
        row.remove();
        updateInvoiceTotals();
    } else {
        alert('You must have at least one line item');
    }
}

/**
 * Update invoice totals based on line items
 */
function updateInvoiceTotals() {
    const rows = document.querySelectorAll('#invoiceLineItems .line-item-row');
    let subtotal = 0;

    // Calculate subtotal from all line items
    rows.forEach(row => {
        const quantity = parseFloat(row.querySelector('.line-quantity').value) || 0;
        const unitPrice = parseFloat(row.querySelector('.line-unit-price').value) || 0;
        const lineTotal = quantity * unitPrice;

        // Update line total field
        row.querySelector('.line-total').value = lineTotal.toFixed(2);

        // Add to subtotal
        subtotal += lineTotal;
    });

    // Calculate tax
    const taxRate = parseFloat(document.getElementById('invoiceTaxRate').value) || 0;
    const tax = subtotal * (taxRate / 100);
    const total = subtotal + tax;

    // Update display
    document.getElementById('subtotalAmount').textContent = subtotal.toFixed(2);
    document.getElementById('taxAmount').textContent = tax.toFixed(2);
    document.getElementById('totalAmount').textContent = total.toFixed(2);
}

/**
 * Get all line items from the form as an array
 */
function getLineItemsFromForm() {
    const rows = document.querySelectorAll('#invoiceLineItems .line-item-row');
    const lineItems = [];

    rows.forEach(row => {
        const description = row.querySelector('.line-description').value;
        const quantity = parseFloat(row.querySelector('.line-quantity').value) || 0;
        const unitPrice = parseFloat(row.querySelector('.line-unit-price').value) || 0;

        if (description.trim()) { // Only add non-empty line items
            lineItems.push({
                description: description.trim(),
                quantity: quantity,
                unit_price: unitPrice
            });
        }
    });

    return lineItems;
}

/**
 * Initialize line items on page load with event listeners
 */
function initializeLineItems() {
    // Add initial event listeners
    document.querySelectorAll('.line-quantity, .line-unit-price').forEach(input => {
        input.addEventListener('change', updateInvoiceTotals);
    });

    // Calculate initial totals
    updateInvoiceTotals();
}

/**
 * Show invoice preview modal
 */
function showInvoicePreview(invoiceData) {
    // Calculate subtotal from line items
    let subtotal = 0;
    let lineItemsHtml = '';

    if (invoiceData.line_items && Array.isArray(invoiceData.line_items)) {
        invoiceData.line_items.forEach((item, idx) => {
            const lineTotal = item.quantity * item.unit_price;
            subtotal += lineTotal;
            lineItemsHtml += `
                <tr>
                    <td>${idx + 1}. ${item.description}</td>
                    <td>${item.quantity} × $${parseFloat(item.unit_price).toFixed(2)} = $${lineTotal.toFixed(2)}</td>
                </tr>
            `;
        });
    }

    const tax = subtotal * invoiceData.tax_rate;
    const total = subtotal + tax;

    const previewHtml = `
        <div class="card mb-3">
            <div class="card-body">
                <h6>Invoice Summary</h6>
                <table class="table table-sm">
                    <tr>
                        <td><strong>Invoice #:</strong></td>
                        <td>${invoiceData.invoice_number}</td>
                    </tr>
                    <tr>
                        <td><strong>Date:</strong></td>
                        <td>${invoiceData.date}</td>
                    </tr>
                    <tr>
                        <td><strong>From:</strong></td>
                        <td>${invoiceData.vendor_business_name && invoiceData.vendor_business_name !== invoiceData.vendor_name ? invoiceData.vendor_business_name + ' (' + invoiceData.vendor_name + ')' : invoiceData.vendor_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Bill To:</strong></td>
                        <td>${invoiceData.student}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><hr></td>
                    </tr>
                    <tr>
                        <td colspan="2"><strong>Line Items:</strong></td>
                    </tr>
                    ${lineItemsHtml}
                    <tr>
                        <td colspan="2"><hr></td>
                    </tr>
                    <tr>
                        <td><strong>Subtotal:</strong></td>
                        <td>$${subtotal.toFixed(2)}</td>
                    </tr>
                    <tr>
                        <td><strong>Tax (${(invoiceData.tax_rate * 100).toFixed(1)}%):</strong></td>
                        <td>$${tax.toFixed(2)}</td>
                    </tr>
                    <tr style="background-color: #f0f0f0;">
                        <td><strong>Total:</strong></td>
                        <td><strong>$${total.toFixed(2)}</strong></td>
                    </tr>
                </table>
            </div>
        </div>
    `;

    document.getElementById('invoicePreviewContent').innerHTML = previewHtml;

    // Show PDF path if available - make it clickable
    if (invoiceData.pdfPath) {
        document.getElementById('pdfPathInfo').style.display = 'list-item';
        const pdfPathElement = document.getElementById('pdfPath');
        pdfPathElement.innerHTML = `<a href="#" onclick="openFile('${invoiceData.pdfPath.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer; text-decoration: underline; color: #0d6efd;">📄 ${invoiceData.pdfPath}</a>`;
    } else {
        document.getElementById('pdfPathInfo').style.display = 'none';
    }

    // Make Excel path clickable
    const excelPathElement = document.getElementById('excelPath');
    excelPathElement.innerHTML = `<a href="#" onclick="openFile('${invoiceData.excelPath.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer; text-decoration: underline; color: #0d6efd;">📊 ${invoiceData.excelPath}</a>`;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('invoicePreviewModal'));
    modal.show();
}

/**
 * Open a file in the default application
 */
async function openFile(filePath) {
    try {
        const response = await fetch('/api/open-file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: filePath })
        });
        if (!response.ok) {
            const error = await response.json();
            alert('Error opening file: ' + (error.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error opening file:', error);
        alert('Error opening file: ' + error.message);
    }
}

/**
 * Continue to file upload after invoice generation
 */
function continueToFileUpload() {
    // Scroll to file upload section
    document.getElementById('fileUploadContainer').scrollIntoView({ behavior: 'smooth' });
}

/**
 * =====================================================================
 * CURRICULUM GENERATOR INTEGRATION
 * =====================================================================
 */

/**
 * Open curriculum generator in a new window/tab
 */
function openCurriculumGenerator() {
    const studentId = document.getElementById('student').value;

    if (!studentId) {
        alert('Please select a student first');
        return;
    }

    // Open curriculum generator in new window with student pre-selected
    const url = `/curriculum-generator?student=${encodeURIComponent(studentId)}`;
    window.open(url, 'curriculum-generator', 'width=1200,height=900,scrollbars=yes');
}

// Initialize invoice feature when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeInvoiceFeature();

    // Add event listeners for edit vendor/student modals
    document.getElementById('editVendorModal')?.addEventListener('show.bs.modal', function() {
        loadVendorProfile(document.getElementById('invoiceVendor').value);
    });

    document.getElementById('editStudentModal')?.addEventListener('show.bs.modal', function() {
        loadStudentProfile(document.getElementById('invoiceStudent').value);
    });
});
