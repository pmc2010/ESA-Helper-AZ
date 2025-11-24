"""Tests for file requirement configurations and validation"""

import pytest


class TestReimbursementFileRequirements:
    """Test file requirements for Reimbursement submissions"""

    def test_computer_hardware_requires_receipt(self, expense_categories):
        """Computer Hardware should require Receipt"""
        category = 'Computer Hardware & Technological Devices'
        required = expense_categories[category]['required_fields']
        assert 'Receipt' in required
        assert 'Invoice' not in required
        assert len(required) == 1

    def test_curriculum_requires_receipt(self, expense_categories):
        """Curriculum should require Receipt"""
        category = 'Curriculum'
        required = expense_categories[category]['required_fields']
        assert 'Receipt' in required
        assert len(required) == 1

    def test_tutoring_facility_requires_receipt_and_invoice(self, expense_categories):
        """Tutoring Facility should require Receipt and Invoice"""
        category = 'Tutoring & Teaching Services - Accredited Facility/Business'
        required = expense_categories[category]['required_fields']
        assert 'Receipt' in required
        assert 'Invoice' in required
        assert 'Attestation' not in required
        assert len(required) == 2

    def test_tutoring_individual_requires_receipt_invoice_attestation(self, expense_categories):
        """Tutoring Individual should require Receipt, Invoice, and Attestation"""
        category = 'Tutoring & Teaching Services - Accredited Individual'
        required = expense_categories[category]['required_fields']
        assert 'Receipt' in required
        assert 'Invoice' in required
        assert 'Attestation' in required
        assert len(required) == 3

    def test_supplemental_materials_requires_curriculum_and_receipt(self, expense_categories):
        """Supplemental Materials should require Curriculum and Receipt"""
        category = 'Supplemental Materials (Curriculum Always Required)'
        required = expense_categories[category]['required_fields']
        assert 'Curriculum' in required
        assert 'Receipt' in required
        assert 'Invoice' not in required
        assert len(required) == 2


class TestDirectPayFileRequirements:
    """Test file requirements for Direct Pay submissions"""

    def test_direct_pay_computer_hardware_requires_invoice_only(self, direct_pay_categories):
        """Direct Pay: Computer Hardware should require Invoice only"""
        category = 'Computer Hardware & Technological Devices'
        required = direct_pay_categories[category]['required_fields']
        assert 'Invoice' in required
        assert 'Receipt' not in required
        assert len(required) == 1

    def test_direct_pay_curriculum_requires_invoice_only(self, direct_pay_categories):
        """Direct Pay: Curriculum should require Invoice only"""
        category = 'Curriculum'
        required = direct_pay_categories[category]['required_fields']
        assert 'Invoice' in required
        assert 'Receipt' not in required
        assert len(required) == 1

    def test_direct_pay_tutoring_facility_requires_invoice_only(self, direct_pay_categories):
        """Direct Pay: Tutoring Facility should require Invoice only"""
        category = 'Tutoring & Teaching Services - Accredited Facility/Business'
        required = direct_pay_categories[category]['required_fields']
        assert 'Invoice' in required
        assert 'Receipt' not in required
        assert 'Attestation' not in required
        assert len(required) == 1

    def test_direct_pay_tutoring_individual_requires_invoice_only(self, direct_pay_categories):
        """Direct Pay: Tutoring Individual should require Invoice only"""
        category = 'Tutoring & Teaching Services - Accredited Individual'
        required = direct_pay_categories[category]['required_fields']
        assert 'Invoice' in required
        assert 'Receipt' not in required
        assert 'Attestation' not in required
        assert len(required) == 1

    def test_direct_pay_supplemental_materials_requires_invoice_and_curriculum(self, direct_pay_categories):
        """Direct Pay: Supplemental Materials should require Invoice and Curriculum"""
        category = 'Supplemental Materials (Curriculum Always Required)'
        required = direct_pay_categories[category]['required_fields']
        assert 'Invoice' in required
        assert 'Curriculum' in required
        assert 'Receipt' not in required
        assert len(required) == 2


class TestFileRequirementsDifferences:
    """Test differences between Reimbursement and Direct Pay requirements"""

    def test_receipt_removed_in_direct_pay(self, expense_categories, direct_pay_categories):
        """Verify Receipt is removed from most Direct Pay categories"""
        categories = [
            'Computer Hardware & Technological Devices',
            'Curriculum',
            'Tutoring & Teaching Services - Accredited Facility/Business',
            'Tutoring & Teaching Services - Accredited Individual'
        ]
        for category in categories:
            reimbursement_files = expense_categories[category]['required_fields']
            direct_pay_files = direct_pay_categories[category]['required_fields']

            # Receipt should be in reimbursement but not direct pay (except Supplemental)
            if 'Receipt' in reimbursement_files:
                assert 'Receipt' not in direct_pay_files, \
                    f"Receipt should be removed from {category} for Direct Pay"

    def test_invoice_added_to_all_direct_pay(self, direct_pay_categories):
        """Verify Invoice is required for all Direct Pay categories"""
        for category, config in direct_pay_categories.items():
            assert 'Invoice' in config['required_fields'], \
                f"Invoice should be required for {category} Direct Pay"

    def test_curriculum_optional_in_direct_pay_except_supplemental(self,
                                                                     expense_categories,
                                                                     direct_pay_categories):
        """Curriculum should be optional in Direct Pay except for Supplemental Materials"""
        # Check that most categories don't require Curriculum in Direct Pay
        categories_without_curriculum = [
            'Computer Hardware & Technological Devices',
            'Curriculum',
            'Tutoring & Teaching Services - Accredited Facility/Business',
            'Tutoring & Teaching Services - Accredited Individual'
        ]

        for category in categories_without_curriculum:
            direct_pay_files = direct_pay_categories[category]['required_fields']
            assert 'Curriculum' not in direct_pay_files, \
                f"Curriculum should be optional for {category} Direct Pay"

        # Verify Supplemental Materials still requires Curriculum
        supplemental = 'Supplemental Materials (Curriculum Always Required)'
        assert 'Curriculum' in direct_pay_categories[supplemental]['required_fields']

    def test_attestation_not_required_in_direct_pay(self, direct_pay_categories):
        """Attestation should never be required in Direct Pay"""
        for category, config in direct_pay_categories.items():
            assert 'Attestation' not in config['required_fields'], \
                f"Attestation should not be in {category} Direct Pay"


class TestCategoryConsistency:
    """Test that all categories are consistent across configurations"""

    def test_both_configs_have_same_categories(self, expense_categories, direct_pay_categories):
        """Both Reimbursement and Direct Pay should have the same categories"""
        reimbursement_cats = set(expense_categories.keys())
        direct_pay_cats = set(direct_pay_categories.keys())
        assert reimbursement_cats == direct_pay_cats

    def test_no_empty_required_fields(self, expense_categories, direct_pay_categories):
        """No category should have empty required_fields"""
        for category, config in expense_categories.items():
            assert len(config['required_fields']) > 0, \
                f"Reimbursement category '{category}' has no required fields"

        for category, config in direct_pay_categories.items():
            assert len(config['required_fields']) > 0, \
                f"Direct Pay category '{category}' has no required fields"

    def test_required_fields_are_valid_file_types(self, expense_categories, direct_pay_categories):
        """All required fields should be valid file types"""
        valid_types = {'Receipt', 'Invoice', 'Attestation', 'Curriculum'}

        for category, config in expense_categories.items():
            for file_type in config['required_fields']:
                assert file_type in valid_types, \
                    f"Invalid file type '{file_type}' in {category}"

        for category, config in direct_pay_categories.items():
            for file_type in config['required_fields']:
                assert file_type in valid_types, \
                    f"Invalid file type '{file_type}' in {category}"
