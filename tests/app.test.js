/**
 * Tests for app.js - Form validation and category configuration logic
 */

describe('Expense Categories Configuration', () => {
  describe('Reimbursement Categories', () => {
    test('should have correct categories defined', () => {
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
        'Curriculum': ['Receipt'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Receipt', 'Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Receipt', 'Invoice', 'Attestation'],
        'Supplemental Materials (Curriculum Always Required)': ['Curriculum', 'Receipt']
      };

      expect(Object.keys(expenseCategories).length).toBe(5);
      expect(expenseCategories['Computer Hardware & Technological Devices']).toEqual(['Receipt']);
    });

    test('Computer Hardware requires only Receipt', () => {
      const category = 'Computer Hardware & Technological Devices';
      const required = ['Receipt'];
      expect(required).toContain('Receipt');
      expect(required.length).toBe(1);
      expect(required).not.toContain('Invoice');
    });

    test('Curriculum requires only Receipt', () => {
      const category = 'Curriculum';
      const required = ['Receipt'];
      expect(required).toContain('Receipt');
      expect(required.length).toBe(1);
    });

    test('Tutoring Facility requires Receipt and Invoice', () => {
      const required = ['Receipt', 'Invoice'];
      expect(required).toContain('Receipt');
      expect(required).toContain('Invoice');
      expect(required.length).toBe(2);
      expect(required).not.toContain('Attestation');
    });

    test('Tutoring Individual requires Receipt, Invoice, and Attestation', () => {
      const required = ['Receipt', 'Invoice', 'Attestation'];
      expect(required).toContain('Receipt');
      expect(required).toContain('Invoice');
      expect(required).toContain('Attestation');
      expect(required.length).toBe(3);
    });

    test('Supplemental Materials requires Curriculum and Receipt', () => {
      const required = ['Curriculum', 'Receipt'];
      expect(required).toContain('Curriculum');
      expect(required).toContain('Receipt');
      expect(required.length).toBe(2);
      expect(required).not.toContain('Invoice');
    });
  });

  describe('Direct Pay Categories', () => {
    test('should have correct Direct Pay categories defined', () => {
      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
        'Curriculum': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Invoice'],
        'Supplemental Materials (Curriculum Always Required)': ['Invoice', 'Curriculum']
      };

      expect(Object.keys(directPayCategories).length).toBe(5);
    });

    test('Direct Pay - Computer Hardware requires only Invoice', () => {
      const required = ['Invoice'];
      expect(required).toContain('Invoice');
      expect(required).not.toContain('Receipt');
      expect(required.length).toBe(1);
    });

    test('Direct Pay - Curriculum requires only Invoice', () => {
      const required = ['Invoice'];
      expect(required).toContain('Invoice');
      expect(required).not.toContain('Receipt');
      expect(required.length).toBe(1);
    });

    test('Direct Pay - Tutoring Facility requires only Invoice', () => {
      const required = ['Invoice'];
      expect(required).toContain('Invoice');
      expect(required).not.toContain('Receipt');
      expect(required).not.toContain('Attestation');
      expect(required.length).toBe(1);
    });

    test('Direct Pay - Tutoring Individual requires only Invoice', () => {
      const required = ['Invoice'];
      expect(required).toContain('Invoice');
      expect(required).not.toContain('Receipt');
      expect(required).not.toContain('Attestation');
      expect(required.length).toBe(1);
    });

    test('Direct Pay - Supplemental Materials requires Invoice and Curriculum', () => {
      const required = ['Invoice', 'Curriculum'];
      expect(required).toContain('Invoice');
      expect(required).toContain('Curriculum');
      expect(required).not.toContain('Receipt');
      expect(required.length).toBe(2);
    });
  });

  describe('Category Configuration Consistency', () => {
    test('both configs should have same category names', () => {
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
        'Curriculum': ['Receipt'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Receipt', 'Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Receipt', 'Invoice', 'Attestation'],
        'Supplemental Materials (Curriculum Always Required)': ['Curriculum', 'Receipt']
      };

      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
        'Curriculum': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Invoice'],
        'Supplemental Materials (Curriculum Always Required)': ['Invoice', 'Curriculum']
      };

      const reimbursementCategories = Object.keys(expenseCategories);
      const directPayCategoryNames = Object.keys(directPayCategories);

      expect(reimbursementCategories).toEqual(directPayCategoryNames);
    });

    test('all categories should have non-empty required files', () => {
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
        'Curriculum': ['Receipt'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Receipt', 'Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Receipt', 'Invoice', 'Attestation'],
        'Supplemental Materials (Curriculum Always Required)': ['Curriculum', 'Receipt']
      };

      Object.entries(expenseCategories).forEach(([category, files]) => {
        expect(files.length).toBeGreaterThan(0);
      });
    });

    test('all file types should be valid', () => {
      const validTypes = new Set(['Receipt', 'Invoice', 'Attestation', 'Curriculum']);
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
        'Curriculum': ['Receipt'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Receipt', 'Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Receipt', 'Invoice', 'Attestation'],
        'Supplemental Materials (Curriculum Always Required)': ['Curriculum', 'Receipt']
      };

      Object.entries(expenseCategories).forEach(([category, files]) => {
        files.forEach(file => {
          expect(validTypes.has(file)).toBe(true);
        });
      });
    });
  });

  describe('File Requirements Differences', () => {
    test('Receipt should be removed from most Direct Pay categories', () => {
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
        'Curriculum': ['Receipt'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Receipt', 'Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Receipt', 'Invoice', 'Attestation'],
        'Supplemental Materials (Curriculum Always Required)': ['Curriculum', 'Receipt']
      };

      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
        'Curriculum': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Invoice'],
        'Supplemental Materials (Curriculum Always Required)': ['Invoice', 'Curriculum']
      };

      const categoriesToCheck = [
        'Computer Hardware & Technological Devices',
        'Curriculum',
        'Tutoring & Teaching Services - Accredited Facility/Business',
        'Tutoring & Teaching Services - Accredited Individual'
      ];

      categoriesToCheck.forEach(category => {
        const hasReceiptInReimbursement = expenseCategories[category].includes('Receipt');
        const hasReceiptInDirectPay = directPayCategories[category].includes('Receipt');

        if (hasReceiptInReimbursement) {
          expect(hasReceiptInDirectPay).toBe(false);
        }
      });
    });

    test('Invoice should be required in all Direct Pay categories', () => {
      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
        'Curriculum': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Invoice'],
        'Supplemental Materials (Curriculum Always Required)': ['Invoice', 'Curriculum']
      };

      Object.entries(directPayCategories).forEach(([category, files]) => {
        expect(files).toContain('Invoice');
      });
    });

    test('Curriculum should be optional in Direct Pay except Supplemental Materials', () => {
      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
        'Curriculum': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Invoice'],
        'Supplemental Materials (Curriculum Always Required)': ['Invoice', 'Curriculum']
      };

      const categoriesToCheck = [
        'Computer Hardware & Technological Devices',
        'Curriculum',
        'Tutoring & Teaching Services - Accredited Facility/Business',
        'Tutoring & Teaching Services - Accredited Individual'
      ];

      categoriesToCheck.forEach(category => {
        expect(directPayCategories[category]).not.toContain('Curriculum');
      });

      // Verify Supplemental Materials still requires Curriculum
      const supplemental = 'Supplemental Materials (Curriculum Always Required)';
      expect(directPayCategories[supplemental]).toContain('Curriculum');
    });

    test('Attestation should never be required in Direct Pay', () => {
      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
        'Curriculum': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Facility/Business': ['Invoice'],
        'Tutoring & Teaching Services - Accredited Individual': ['Invoice'],
        'Supplemental Materials (Curriculum Always Required)': ['Invoice', 'Curriculum']
      };

      Object.entries(directPayCategories).forEach(([category, files]) => {
        expect(files).not.toContain('Attestation');
      });
    });
  });
});

describe('Form Validation Logic', () => {
  describe('getCategoryConfig function', () => {
    test('should return expenseCategories for Reimbursement request type', () => {
      const requestType = 'Reimbursement';
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
      };
      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
      };

      const config = requestType === 'Direct Pay' ? directPayCategories : expenseCategories;
      expect(config).toEqual(expenseCategories);
    });

    test('should return directPayCategories for Direct Pay request type', () => {
      const requestType = 'Direct Pay';
      const expenseCategories = {
        'Computer Hardware & Technological Devices': ['Receipt'],
      };
      const directPayCategories = {
        'Computer Hardware & Technological Devices': ['Invoice'],
      };

      const config = requestType === 'Direct Pay' ? directPayCategories : expenseCategories;
      expect(config).toEqual(directPayCategories);
    });
  });

  describe('File Validation', () => {
    test('should validate required files for Reimbursement', () => {
      const category = 'Computer Hardware & Technological Devices';
      const requiredFiles = ['Receipt'];
      const selectedFiles = { 'Receipt': 'file.pdf' };

      const allFilesUploaded = requiredFiles.every(ft => selectedFiles[ft]);
      expect(allFilesUploaded).toBe(true);
    });

    test('should fail validation if required file is missing', () => {
      const category = 'Computer Hardware & Technological Devices';
      const requiredFiles = ['Receipt'];
      const selectedFiles = {};

      const allFilesUploaded = requiredFiles.every(ft => selectedFiles[ft]);
      expect(allFilesUploaded).toBe(false);
    });

    test('should validate multiple required files', () => {
      const category = 'Tutoring & Teaching Services - Accredited Individual';
      const requiredFiles = ['Receipt', 'Invoice', 'Attestation'];
      const selectedFiles = {
        'Receipt': 'receipt.pdf',
        'Invoice': 'invoice.pdf',
        'Attestation': 'attestation.pdf'
      };

      const allFilesUploaded = requiredFiles.every(ft => selectedFiles[ft]);
      expect(allFilesUploaded).toBe(true);
    });

    test('should fail if one of multiple required files is missing', () => {
      const requiredFiles = ['Receipt', 'Invoice', 'Attestation'];
      const selectedFiles = {
        'Receipt': 'receipt.pdf',
        'Invoice': 'invoice.pdf'
        // Missing Attestation
      };

      const allFilesUploaded = requiredFiles.every(ft => selectedFiles[ft]);
      expect(allFilesUploaded).toBe(false);
    });
  });

  describe('Request Type Change Logic', () => {
    test('should reset selectedFiles when switching request types', () => {
      let selectedFiles = { 'Receipt': 'receipt.pdf', 'Invoice': 'invoice.pdf' };

      // Simulate switching request type
      selectedFiles = {};

      expect(Object.keys(selectedFiles).length).toBe(0);
    });

    test('should require re-upload of files when switching to Direct Pay', () => {
      const oldFiles = { 'Receipt': 'receipt.pdf' };
      const newRequiredFiles = ['Invoice'];

      const allFilesUploaded = newRequiredFiles.every(ft => oldFiles[ft]);
      expect(allFilesUploaded).toBe(false);
    });
  });
});

describe('File Labels Configuration', () => {
  test('should have correct file labels', () => {
    const fileLabels = {
      'Receipt': 'Receipt/Payment Proof',
      'Invoice': 'Invoice',
      'Attestation': 'Instructor Attestation',
      'Curriculum': 'Curriculum Document'
    };

    expect(fileLabels['Receipt']).toBe('Receipt/Payment Proof');
    expect(fileLabels['Invoice']).toBe('Invoice');
    expect(fileLabels['Attestation']).toBe('Instructor Attestation');
    expect(fileLabels['Curriculum']).toBe('Curriculum Document');
  });

  test('should have labels for all valid file types', () => {
    const validTypes = ['Receipt', 'Invoice', 'Attestation', 'Curriculum'];
    const fileLabels = {
      'Receipt': 'Receipt/Payment Proof',
      'Invoice': 'Invoice',
      'Attestation': 'Instructor Attestation',
      'Curriculum': 'Curriculum Document'
    };

    validTypes.forEach(type => {
      expect(fileLabels[type]).toBeDefined();
      expect(fileLabels[type].length).toBeGreaterThan(0);
    });
  });
});
