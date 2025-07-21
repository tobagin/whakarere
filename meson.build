project('karere',
  version: '0.4.4',
  license: 'GPL-3.0-or-later',
  meson_version: '>= 1.4.0',
  default_options: [
    'warning_level=2',
    'werror=false',
  ],
)

# Import modules
gnome = import('gnome')
python = import('python')

# Python installation
py_installation = python.find_installation('python3')
if not py_installation.found()
  error('Python 3 not found')
endif

# Dependencies
dependency('gtk4', version: '>= 4.0')
dependency('libadwaita-1', version: '>= 1.0')
dependency('webkitgtk-6.0', version: '>= 2.40')

# Application information
application_id = 'io.github.tobagin.karere'
pkgdatadir = py_installation.get_install_dir()
moduledir = py_installation.get_install_dir() / 'karere'

# Configuration data
conf = configuration_data()
conf.set('PYTHON', py_installation.full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('INSTALLED_PYTHONPATH', py_installation.get_install_dir())

# Install Python modules
install_subdir('src/karere', install_dir: py_installation.get_install_dir(), exclude_files: ['ui'])

# Process subdirectories
subdir('src/karere/ui')
subdir('data')
subdir('po')

# Generate executable script
configure_file(
  input: 'karere.in',
  output: 'karere',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

# Version validation tests
version_consistency_script = files('scripts/test_version_consistency.py')
test('version-consistency', py_installation,
  args: [version_consistency_script],
  suite: 'validation',
  timeout: 30
)

# Build-time version validation
build_validation_script = files('scripts/validate_build_version.py')
test('build-version-validation', py_installation,
  args: [build_validation_script],
  suite: 'validation',
  timeout: 30
)

# Version format validation
version_format_script = configure_file(
  input: files('scripts/test_version_format.py.in'),
  output: 'test_version_format.py',
  configuration: conf
)

test('version-format', py_installation,
  args: [version_format_script],
  suite: 'validation',
  timeout: 10
)

# Production hardening validation
production_hardening_script = files('scripts/test_production_hardening.py')
test('production-hardening', py_installation,
  args: [production_hardening_script],
  suite: 'validation',
  timeout: 30
)

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)