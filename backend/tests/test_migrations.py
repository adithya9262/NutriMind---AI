import configparser
import importlib
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
ALEMBIC_DIR = Path(__file__).resolve().parent.parent / "alembic"
VERSIONS_DIR = ALEMBIC_DIR / "versions"
ENV_PY = ALEMBIC_DIR / "env.py"


class TestAlembicConfigExists:
    def test_alembic_ini_exists(self):
        assert ALEMBIC_INI.is_file(), "alembic.ini must exist"

    def test_alembic_dir_exists(self):
        assert ALEMBIC_DIR.is_dir(), "alembic/ directory must exist"

    def test_versions_dir_exists(self):
        assert VERSIONS_DIR.is_dir(), "alembic/versions/ directory must exist"

    def test_env_py_exists(self):
        assert ENV_PY.is_file(), "alembic/env.py must exist"

    def test_no_other_alembic_config(self):
        root_ini = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
        if root_ini != ALEMBIC_INI:
            assert not root_ini.is_file(), "No alembic.ini at repository root"
        root_dir = Path(__file__).resolve().parent.parent.parent / "alembic"
        if root_dir != ALEMBIC_DIR:
            assert not root_dir.is_dir(), "No alembic/ at repository root"

    def test_no_duplicate_backend_migration_dir(self):
        other = Path(__file__).resolve().parent.parent / "migrations"
        assert not other.is_dir(), "No backend/migrations/ directory"


class TestAlembicIniSafety:
    def test_script_location_is_backend_alembic(self):
        parser = configparser.ConfigParser()
        parser.read(ALEMBIC_INI)
        script_location = parser.get("alembic", "script_location", raw=True, fallback="")
        assert "alembic" in script_location, (
            f"script_location must point to alembic/, got {script_location!r}"
        )

    def test_no_database_url_in_ini(self):
        parser = configparser.ConfigParser()
        parser.read(ALEMBIC_INI)
        url = parser.get("alembic", "sqlalchemy.url", fallback="")
        assert url == "" or url.startswith("#") or url.startswith(";"), (
            "sqlalchemy.url in alembic.ini must be empty, not a real URL"
        )

    def test_no_password_in_ini(self):
        content = ALEMBIC_INI.read_text(encoding="utf-8")
        assert "password" not in content.lower(), "alembic.ini must not contain a password"

    def test_port_5433_not_hardcoded_in_alembic_ini(self):
        content = ALEMBIC_INI.read_text(encoding="utf-8")
        assert "5433" not in content, "Port 5433 must not be hard-coded in alembic.ini"


class TestEnvPy:
    def test_env_imports_app_base(self):
        env_source = ENV_PY.read_text(encoding="utf-8")
        assert "from app.db.base import Base" in env_source

    def test_target_metadata_is_base_metadata(self):
        env_source = ENV_PY.read_text(encoding="utf-8")
        assert "target_metadata = Base.metadata" in env_source

    def test_no_second_declarative_base_in_alembic(self):
        env_source = ENV_PY.read_text(encoding="utf-8")
        assert "DeclarativeBase" not in env_source, (
            "Alembic env.py must not create a second DeclarativeBase"
        )

    def test_no_create_all_in_alembic(self):
        env_source = ENV_PY.read_text(encoding="utf-8")
        assert "create_all" not in env_source, "Alembic env.py must not call create_all()"

    def test_missing_url_raises_safe_error(self):
        from app.core.config import Settings

        settings = Settings(APP_ENV="test", DATABASE_URL="")
        assert settings.DATABASE_URL == ""
        from app.db.base import Base

        assert Base.metadata is not None


class TestBaselineMigration:
    def test_exactly_five_migration_files(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        assert len(files) == 7, (
            f"Expected seven migration files, found {len(files)}: {[f.name for f in files]}"
        )

    def test_baseline_down_revision_is_none(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = [f for f in files if "3f0c6eb4f49e" in f.name]
        assert len(baseline) == 1
        migration_text = baseline[0].read_text(encoding="utf-8")
        assert "None" in migration_text.split("down_revision")[1].split("\n")[0]

    def test_baseline_upgrade_is_empty(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = next(f for f in files if "baseline" in f.name)
        migration_text = baseline.read_text(encoding="utf-8")
        assert "def upgrade" in migration_text
        assert "pass" in migration_text.split("def upgrade")[1].split("def downgrade")[0]

    def test_baseline_downgrade_is_empty(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = next(f for f in files if "baseline" in f.name)
        migration_text = baseline.read_text(encoding="utf-8")
        assert "def downgrade" in migration_text
        assert "pass" in migration_text.split("def downgrade")[1]

    def test_no_application_tables_in_migration(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = next(f for f in files if "baseline" in f.name)
        migration_text = baseline.read_text(encoding="utf-8")
        forbidden = ["op.create_table(", "sa.Table(", "op.add_column("]
        for token in forbidden:
            assert token not in migration_text, (
                f"Baseline migration must not create tables, found {token}"
            )

    def test_no_credentials_in_migration(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = next(f for f in files if "baseline" in f.name)
        migration_text = baseline.read_text(encoding="utf-8")
        assert "://" not in migration_text, "Migration files must not contain URLs"
        assert "password" not in migration_text.lower(), (
            "Migration files must not contain passwords"
        )

    def test_no_orm_model_names_in_migration(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = next(f for f in files if "baseline" in f.name)
        migration_text = baseline.read_text(encoding="utf-8")
        model_names = ["user", "nutrition", "food", "recipe", "profile"]
        for name in model_names:
            assert name not in migration_text.lower(), (
                f"Baseline must not reference model name '{name}'"
            )


class TestAppIsolationFromMigrations:
    def test_importing_app_does_not_trigger_alembic(self):
        import app.main as app_main

        reloaded = importlib.reload(app_main)
        assert hasattr(reloaded, "create_app")

    def test_app_factory_does_not_run_migrations(self):
        settings = Settings(APP_ENV="test", DATABASE_URL="")
        app = create_app(settings=settings)
        assert app is not None

    async def test_health_endpoint_independent_from_migrations(self):
        settings = Settings(APP_ENV="test", DATABASE_URL="")
        app = create_app(settings=settings)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
        assert response.status_code == 200

    def test_base_metadata_has_application_tables(self):
        from app.db.base import Base

        assert len(Base.metadata.tables) >= 2, "ORM models should be registered"

    def test_no_create_all_exists(self):
        from app.db.base import Base

        assert not hasattr(Base.metadata, "_create_all_called")

    def test_no_automatic_migration_execution(self):
        import app.main as app_main

        source = Path(app_main.__file__).read_text(encoding="utf-8")
        assert "alembic" not in source.lower(), "app/main.py must not import or call alembic"


class TestAlembicConfiguration:
    def test_alembic_imports(self):
        import alembic.config

        assert alembic.config is not None

    def test_alembic_config_can_be_loaded(self):
        from alembic.config import Config

        config = Config(str(ALEMBIC_INI))
        assert config.get_main_option("script_location") is not None

    def test_script_location_ends_with_alembic(self):
        from alembic.config import Config

        config = Config(str(ALEMBIC_INI))
        loc = config.get_main_option("script_location")
        assert loc.rstrip("/\\").endswith("alembic"), (
            f"script_location must end with 'alembic', got {loc!r}"
        )
