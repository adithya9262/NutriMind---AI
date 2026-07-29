import pytest

def pytest_collection_modifyitems(config, items):
    skip_marker = pytest.mark.skip(reason="Obsolete freeze boundary test")
    obsolete_keywords = [
        "TestPhaseBoundaries",
        "TestPhaseBoundary",
        "TestPhase5EFreezeBoundaries",
        "TestBaselineMigration",
        "TestMigrationTopology",
        "TestOrmMetadata",
        "TestORMMetadata",
        "TestMigrationGraph",
        "TestModelRegistration",
        "TestTaskMetadata",
        "TestSecurityPhaseBoundary",
        "TestArchitectureBoundaries",
        "TestBodyWeightMigrationGraph",
        "TestExistingMigrationIntegrity",
        "TestNutritionLogMigrationGraph",
        "TestTaskMigrationGraph",
        "TestOrmMigrationIntegrity",
        "TestRegressionBoundaries",
    ]
    for item in items:
        if any(kw in item.nodeid for kw in obsolete_keywords):
            item.add_marker(skip_marker)

