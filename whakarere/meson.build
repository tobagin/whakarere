pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'whakarere'
gnome = import('gnome')
python_module = import('python').find_installation('python3')
whakarere_dir = python_module.get_install_dir() / 'whakarere'

gnome.compile_resources('whakarere',
  'whakarere.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

tar_file_path = meson.current_source_dir() / 'whakarere-api.tar.xz'

# Directory creation
run_command('mkdir', '-p', '/app/lib/python3.11/site-packages/whakarere')

# Custom target to extract the tar.xz file
custom_target('extract_whakarere_api',
    output : 'dummy.out',
    command : ['tar', '-xvf', tar_file_path, '-C', whakarere_dir],
    build_by_default : true)

configure_file(
  input: 'whakarere.in',
  output: 'whakarere',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

whakarere_main = [
  '__init__.py',
  'main.py',
  '.env',
]
install_data(whakarere_main, install_dir: whakarere_dir, install_mode: 'rwxr-xr-x')

whakarere_images = [
  'images/__init__.py',
  'images/unknown_contact.py',
  'images/whatsapp_logo.py',
  'images/whatsapp_logo_alt.py',
]
install_data(whakarere_images, install_dir: whakarere_dir / 'images', install_mode: 'rwxr-xr-x')

whakarere_managers = [
  'managers/app.py',
  'managers/qrcode.py',
  'managers/session.py',
  'managers/whatsapp.py',
]
install_data(whakarere_managers, install_dir: whakarere_dir / 'managers', install_mode: 'rwxr-xr-x')

whakarere_pages = [
  'pages/qrcode.py',
  'pages/session.py',
  'pages/whatsapp.py',
]
install_data(whakarere_pages, install_dir: whakarere_dir / 'pages', install_mode: 'rwxr-xr-x')

whakarere_types = [
  'types/account.py',
  'types/chat.py',
]
install_data(whakarere_types, install_dir: whakarere_dir / 'types', install_mode: 'rwxr-xr-x')

whakarere_widgets = [
  'widgets/main_menu.py',
  'widgets/titlebar.py',
]
install_data(whakarere_widgets, install_dir: whakarere_dir / 'widgets', install_mode: 'rwxr-xr-x')

whakarere_windows = [
  'windows/whakarere.py',
]
install_data(whakarere_windows, install_dir: whakarere_dir / 'windows', install_mode: 'rwxr-xr-x')